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
    """Handles inserting news data into MongoDB Atlas collections."""

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
