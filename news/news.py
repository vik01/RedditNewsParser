# Standard Library Imports
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Local Module Imports
from news_utils import (load_config, require_section,
                        require_list, require_int, require_str)
from newsio import get_latest_news
from newsapiorg import get_top_headlines, get_sources
from databases.mongo_db import DbAdd

# Load config variables
_cfg = load_config(project_root / "config.yaml")
_newsio = require_section(_cfg, "newsio")
_newsapiorg = require_section(_cfg, "newsapiorg")
_newsapiorg_sources = require_section(_cfg, "newsapiorg_sources")

# newsio config
NEWSIO_CATEGORIES = require_list(_newsio, "newsio_categories")
NEWSIO_COUNTRIES = require_list(_newsio, "newsio_countries")
NEWSIO_LANGUAGE = require_str(_newsio, "language")
NEWSIO_SIZE = require_int(_newsio, "size")
NEWSIO_REMOVEDUPLICATES = require_int(_newsio, "removeduplicate")

# newsapiorg config
NEWSAPIORG_CATEGORIES = require_list(_newsapiorg, "newsapiorg_categories")
NEWSAPIORG_COUNTRIES = require_list(_newsapiorg, "newsapiorg_countries")
NEWSAPIORG_PAGE_SIZE = require_int(_newsapiorg, "page_size")

# newsapiorg sources config
SOURCE_CATEGORIES = require_list(_newsapiorg_sources, "source_categories")
SOURCE_COUNTRIES = require_list(_newsapiorg_sources, "source_countries")
SOURCE_LANGUAGE = require_str(_newsapiorg_sources, "language")


def get_newsio():
    """
    Fetch latest news articles from the NewsData.io API for every
    country/category combination defined in config.yaml.

    Each successful API response is pushed directly to MongoDB
    via DbAdd. Skips any country/category combo where the API
    call returns None.
    """
    database = DbAdd()
    for country in NEWSIO_COUNTRIES:
        for category in NEWSIO_CATEGORIES:
            params = {
                "country": country,
                "language": NEWSIO_LANGUAGE,
                "category": category,
                "removeduplicate": NEWSIO_REMOVEDUPLICATES,
                "size": NEWSIO_SIZE
            }
            result = get_latest_news(**params)
            if result is None:
                continue
            database.add_news_to_newsio(result)


def get_newsapiorg():
    """
    Fetch top headlines from the NewsAPI.org API for every
    country/category combination defined in config.yaml.

    Each successful API response is pushed directly to MongoDB
    via DbAdd. Skips any country/category combo where the API
    call returns None.
    """
    database = DbAdd()
    for country in NEWSAPIORG_COUNTRIES:
        for category in NEWSAPIORG_CATEGORIES:
            params = {
                "country": country,
                "category": category,
                "pageSize": NEWSAPIORG_PAGE_SIZE
            }
            result = get_top_headlines(**params)
            if result is None:
                continue
            database.add_news_to_newsapiorg(result)


def get_newsapiorg_sources():
    """
    Fetch news sources from the NewsAPI.org API for every
    country/category combination defined in config.yaml.

    Each successful API response is pushed directly to MongoDB
    via DbAdd. Skips any country/category combo where the API
    call returns None.
    """
    database = DbAdd()
    for country in SOURCE_COUNTRIES:
        for category in SOURCE_CATEGORIES:
            params = {
                "category": category,
                "language": SOURCE_LANGUAGE,
                "country": country
            }
            result = get_sources(**params)
            if result is None:
                continue
            database.add_to_sources(result)

if __name__ == "__main__":
    get_newsapiorg_sources()
    get_newsapiorg()
    get_newsio()