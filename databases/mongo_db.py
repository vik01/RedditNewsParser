# Standard Library Imports
import sys
from typing import Dict, List
from pathlib import Path
from contextlib import contextmanager

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Third Party Imports
from dotenv import dotenv_values
from pymongo import MongoClient

# Local Module Imports
from db_utils import (load_config, require_section,
                      require_str, resolve_repo_path)

# Load config variables
_cfg = load_config(project_root / "config.yaml")
_environment = require_section(_cfg, "environment")
_atlas_mongo = require_section(_cfg, "atlas_mongo")

ENVIRONMENT_PATH = resolve_repo_path(
    project_root, require_str(_environment, "environment_path"),
    ensure_parent=True)

# All environmental variables
env_config = dotenv_values(ENVIRONMENT_PATH)
MONGODB_CONN_STRING = env_config["MONGODB_CONN_STRING"]

# MongoDB config
CLUSTER = require_str(_atlas_mongo, "cluster")
DATABASE = require_str(_atlas_mongo, "database")
NEWSIO_COLLECTION = require_str(_atlas_mongo, "newsio_collection")
NEWSAPIORG_COLLECTION = require_str(_atlas_mongo, "newsapiorg_collection")
SOURCES_COLLECTION = require_str(_atlas_mongo, "newsio_sources_collection")


class DbAdd:
    """Handles inserting and retrieving news data from MongoDB Atlas collections."""

    def __init__(self):
        pass

    @contextmanager
    def _connection(self):
        """
        Context manager that opens a MongoClient, yields the
        database handle, and guarantees the client is closed
        even if the caller raises an exception.
        """
        client = MongoClient(MONGODB_CONN_STRING)
        try:
            yield client[DATABASE]
        finally:
            client.close()

    def _check_duplicates(self, db, collection_name: str,
                          key_type: str, documents: List[Dict]) -> List[Dict]:
        """
        Filter out documents that already exist in the given collection.

        Queries all existing values for key_type, compares against the
        incoming list, and returns only documents that are new.
        """
        collection = db[collection_name]
        existing_keys = set(
            doc[key_type]
            for doc in collection.find({}, {key_type: 1, "_id": 0})
        )
        return [doc for doc in documents if doc.get(key_type) not in existing_keys]

    def add_news_to_newsio(self, insert_dict: Dict):
        """
        Insert newsio articles into the newsio MongoDB collection.

        Checks for duplicate article_ids before inserting. Only
        new documents are added via insert_many.
        """
        with self._connection() as db:
            documents = list(insert_dict.values())
            new_documents = self._check_duplicates(
                db, NEWSIO_COLLECTION, "article_id", documents)
            if new_documents:
                db[NEWSIO_COLLECTION].insert_many(new_documents)

    def add_news_to_newsapiorg(self, insert_dict: Dict):
        """
        Insert newsapiorg articles into the newsapiorg MongoDB collection.

        Checks for duplicate titles before inserting. Only
        new documents are added via insert_many.
        """
        with self._connection() as db:
            documents = list(insert_dict.values())
            new_documents = self._check_duplicates(
                db, NEWSAPIORG_COLLECTION, "title", documents)
            if new_documents:
                db[NEWSAPIORG_COLLECTION].insert_many(new_documents)

    def add_to_sources(self, insert_dict: Dict):
        """
        Insert news sources into the sources MongoDB collection.

        Checks for duplicate names before inserting. Only
        new documents are added via insert_many.
        """
        with self._connection() as db:
            documents = list(insert_dict.values())
            new_documents = self._check_duplicates(
                db, SOURCES_COLLECTION, "name", documents)
            if new_documents:
                db[SOURCES_COLLECTION].insert_many(new_documents)

    def get_all_newsio(self) -> List[Dict]:
        """Retrieve all documents from the newsio collection."""
        with self._connection() as db:
            return list(db[NEWSIO_COLLECTION].find({}, {"_id": 0}))

    def get_all_newsapiorg(self) -> List[Dict]:
        """Retrieve all documents from the newsapiorg collection."""
        with self._connection() as db:
            return list(db[NEWSAPIORG_COLLECTION].find({}, {"_id": 0}))

    def get_all_sources(self) -> List[Dict]:
        """Retrieve all documents from the sources collection."""
        with self._connection() as db:
            return list(db[SOURCES_COLLECTION].find({}, {"_id": 0}))

    def get_newsio_by_country_category(self, country: str,
                                       category: str) -> List[Dict]:
        """
        Retrieve newsio articles matching a specific country and category.

        MongoDB auto-matches when the field is an array and the query
        value is a scalar (e.g. {"country": "in"} matches ["india"] only
        if stored as "in" — here newsio stores full names like "india",
        so the caller must pass the value as stored in the DB).
        """
        with self._connection() as db:
            return list(db[NEWSIO_COLLECTION].find(
                {"country": country, "category": category},
                {"_id": 0}
            ))

    def get_newsapiorg_by_country_category(self, country: str,
                                           category: str) -> List[Dict]:
        """
        Retrieve newsapiorg articles for a specific country and category
        by joining through the sources collection.

        1. Query sources for matching country + category -> list of names.
        2. Query newsapiorg for source_name in that list.
        """
        with self._connection() as db:
            source_names = [
                doc["name"]
                for doc in db[SOURCES_COLLECTION].find(
                    {"country": country, "category": category},
                    {"name": 1, "_id": 0}
                )
            ]
            if not source_names:
                return []
            return list(db[NEWSAPIORG_COLLECTION].find(
                {"source_name": {"$in": source_names}},
                {"_id": 0}
            ))
