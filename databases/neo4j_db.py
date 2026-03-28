# Standard Library Imports
import sys
from typing import Dict, List
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Third Party Imports
from dotenv import dotenv_values
from neo4j import GraphDatabase

# Local Module Imports
from db_utils import (load_config, require_section,
                      require_str, resolve_repo_path)

# Load config variables
_cfg = load_config(project_root / "config.yaml")
_environment = require_section(_cfg, "environment")
_neo4j = require_section(_cfg, "neo4j")

ENVIRONMENT_PATH = resolve_repo_path(
    project_root, require_str(_environment, "environment_path"),
    ensure_parent=True)

# All environmental variables
env_config = dotenv_values(ENVIRONMENT_PATH)
NEO4J_URI = env_config["NEO_J_URI"]
NEO4J_USERNAME = env_config["NEO_J_USERNAME"]
NEO4J_PASSWORD = env_config["NEO_J_PASSWORD"]

# Neo4j config
NEO4J_DATABASE = require_str(_neo4j, "database")


class GraphDB:
    """Handles building and updating the Neo4j news graph."""

    def __init__(self):
        pass

    def _connection(self):
        """
        Create a Neo4j driver instance. Caller is responsible for
        closing via driver.close() or using it as a context manager.
        """
        driver = GraphDatabase.driver(NEO4J_URI,
                                      auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        return driver

    def _ensure_countries(self, driver, countries: Dict[str, str]):
        """
        MERGE Country nodes from the country_longforms config dict.

        Args:
            countries: {code: long_name} e.g. {"us": "United States of America"}
        """
        for code, name in countries.items():
            driver.execute_query(
                "MERGE (c:Country {code: $code}) "
                "SET c.name = $name",
                code=code, name=name,
                database_=NEO4J_DATABASE,
            )

    def _ensure_sources(self, driver, sources: List[Dict]):
        """
        MERGE Source nodes from the MongoDB sources collection.

        Each source doc has: name, description, url, category, language, country.
        """
        for source in sources:
            driver.execute_query(
                "MERGE (s:Source {name: $name}) "
                "SET s.url = $url, s.description = $description",
                name=source.get("name", ""),
                url=source.get("url", ""),
                description=source.get("description", ""),
                database_=NEO4J_DATABASE,
            )

    def _build_source_lookup(self, sources: List[Dict]) -> Dict[str, Dict]:
        """
        Build a lookup dict from sources: {name: {country, category}}.

        Used to resolve country/category for newsapiorg articles.
        """
        lookup = {}
        for source in sources:
            name = source.get("name", "")
            if name:
                lookup[name] = {
                    "country": source.get("country", ""),
                    "category": source.get("category", ""),
                }
        return lookup

    def _upsert_edges(self, driver, articles: List[Dict],
                      source_lookup: Dict[str, Dict]):
        """
        MERGE PUBLISHES_IN edges between Source and Country nodes.

        For newsio articles: country and category are fields on the doc (as lists).
        For newsapiorg articles: country and category are resolved via source_lookup.

        If edge exists, increments article_count. If new, sets article_count = 1.
        """
        for article in articles:
            source_name = article.get("source_name", "")
            if not source_name:
                continue

            # Determine countries and categories
            countries = article.get("country")
            categories = article.get("category")

            # newsio: country/category are lists
            if isinstance(countries, list) and isinstance(categories, list):
                for country in countries:
                    for category in categories:
                        self._merge_edge(driver, source_name,
                                         country, category)
            # newsapiorg: resolve from source_lookup
            elif source_name in source_lookup:
                info = source_lookup[source_name]
                country = info.get("country", "")
                category = info.get("category", "")
                if country and category:
                    self._merge_edge(driver, source_name, country, category)

    def _merge_edge(self, driver, source_name: str,
                    country_code: str, category: str):
        """
        MERGE a single PUBLISHES_IN edge between a Source and Country.

        Increments article_count on match, sets to 1 on create.
        """
        driver.execute_query(
            "MERGE (s:Source {name: $source_name}) "
            "MERGE (c:Country {code: $country_code}) "
            "MERGE (s)-[r:PUBLISHES_IN {category: $category}]->(c) "
            "ON CREATE SET r.article_count = 1 "
            "ON MATCH SET r.article_count = r.article_count + 1",
            source_name=source_name,
            country_code=country_code,
            category=category,
            database_=NEO4J_DATABASE,
        )

    def build_graph(self, articles: List[Dict], sources: List[Dict],
                    countries: Dict[str, str]):
        """
        Build or incrementally update the Neo4j graph.

        1. MERGE all Country nodes from config.
        2. MERGE all Source nodes from MongoDB sources collection.
        3. MERGE PUBLISHES_IN edges for each article, incrementing
           article_count on existing edges.

        Args:
            articles: Combined list of newsio + newsapiorg article dicts.
            sources: List of source dicts from MongoDB sources collection.
            countries: {code: long_name} from config country_longforms.
        """
        source_lookup = self._build_source_lookup(sources)
        driver = self._connection()
        try:
            self._ensure_countries(driver, countries)
            self._ensure_sources(driver, sources)
            self._upsert_edges(driver, articles, source_lookup)
        finally:
            driver.close()
