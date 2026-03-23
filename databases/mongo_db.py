# Standard Library Imports
from typing import Dict
from pathlib import Path

# Third Party Imports
from dotenv import dotenv_values
from pymongo import MongoClient

# Local Module Imports
from db_utils import (load_config, require_section,
                      require_str, resolve_repo_path)

project_root = Path(__file__).resolve().parents[1]

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

    def _connect_db(self):
        """
        Connect to MongoDB Atlas and store the database handle
        in self.database for reuse across insert calls.
        """
        client = MongoClient(MONGODB_CONN_STRING)
        self.database = client[DATABASE]

    def add_news_to_newsio(self, insert_dict: Dict):
        """
        Insert newsio articles into the newsio MongoDB collection.

        Takes the dict returned by get_newsio() and inserts all
        values as documents via insert_many.
        """
        if not hasattr(self, "database"):
            self._connect_db()
        collection = self.database[NEWSIO_COLLECTION]
        collection.insert_many(list(insert_dict.values()))

    def add_news_to_newsapiorg(self, insert_dict: Dict):
        """
        Insert newsapiorg articles into the newsapiorg MongoDB collection.

        Takes the dict returned by get_newsapiorg() and inserts all
        values as documents via insert_many.
        """
        if not hasattr(self, "database"):
            self._connect_db()
        collection = self.database[NEWSAPIORG_COLLECTION]
        collection.insert_many(list(insert_dict.values()))

    def add_to_sources(self, insert_dict: Dict):
        """
        Insert news sources into the sources MongoDB collection.

        Takes the dict returned by get_newsapiorg_sources() and inserts
        all values as documents via insert_many.
        """
        if not hasattr(self, "database"):
            self._connect_db()
        collection = self.database[SOURCES_COLLECTION]
        collection.insert_many(list(insert_dict.values()))
