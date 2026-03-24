# Standard Library Imports
from pathlib import Path
import requests as re
import unicodedata
import json

# Third Party Imports
from dotenv import dotenv_values

# Local Module Imports
from news_utils import (load_config, require_section,
                        require_list, require_dict, 
                        resolve_repo_path, require_str)

project_root = Path(__file__).resolve().parents[1]

# Load config variables
_cfg = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
_news_vars = require_section(_cfg, "news_vars")
_environment_path = require_section(_cfg, "environment")

HEADLINES_CONTENTS = require_list(_news_vars, "headlines_contents")
SOURCES_CONTENTS = require_list(_news_vars, "sources_contents")
UNICODE_REPLACEMENTS = require_dict(_news_vars, "unicode_replacements")
ENVIRONMENT_PATH = resolve_repo_path(
        project_root, require_str(_environment_path, "environment_path"), ensure_parent=True)

# All environmental variables
env_config = dotenv_values(ENVIRONMENT_PATH)
top_headlines_uri = env_config["NEWSAPIORG_TOP_HEADLINES_URL"]
sources_uri = env_config["NEWSAPIORG_SOURCES_URL"]
__api_key = env_config["NEWSAPIORG_API_KEY"]


def __normalize_text(text):
    if not isinstance(text, str):
        return text
    for unicode_char, ascii_char in UNICODE_REPLACEMENTS.items():
        text = text.replace(unicode_char, ascii_char)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "replace").decode("ascii")
    return text


def __make_api_call(base_uri, **kwargs):
    query_string = ""
    for key, value in kwargs.items():
        query_string += f"&{key}={value}"
    query = f"{base_uri}apiKey={__api_key}{query_string}"
    try:
        response = re.get(query)
    except re.RequestException:
        print("Error: API call failed")
        return None
    return response.json()


def get_top_headlines(**kwargs):
    result_json = __make_api_call(top_headlines_uri, **kwargs)
    if result_json is None:
        print("Error: API call failed")
        return None
    if result_json.get("status") != "ok":
        print(f"Error: {result_json.get('message', 'Unknown error')}")
        return None
    try:
        articles = result_json["articles"]
    except KeyError:
        print("Error: Key 'articles' not found in JSON response")
        return None
    final_result = {}
    for i, article in enumerate(articles):
        add = {}
        for content in HEADLINES_CONTENTS:
            try:
                if content == "source":
                    add["source_name"] = __normalize_text(
                        article["source"]["name"]
                    )
                else:
                    add[content] = __normalize_text(article[content])
            except KeyError:
                print(f"Error: Key '{content}' not found in JSON response")
                add[content] = None
        final_result[i] = add
    return final_result


def get_sources(**kwargs):
    result_json = __make_api_call(sources_uri, **kwargs)
    if result_json is None:
        print("Error: API call failed")
        return None
    if result_json.get("status") != "ok":
        print(f"Error: {result_json.get('message', 'Unknown error')}")
        return None
    try:
        sources = result_json["sources"]
    except KeyError:
        print("Error: Key 'sources' not found in JSON response")
        return None
    final_result = {}
    for source in sources:
        add = {}
        for content in SOURCES_CONTENTS:
            try:
                if content != "id":
                    add[content] = __normalize_text(source[content])
            except KeyError:
                print(f"Error: Key '{content}' not found in JSON response")
                add[content] = None
        final_result[source["id"]] = add
    return final_result


if __name__ == "__main__":

    headlines_params = {
        "country": "us",
        "category": "technology",
        "pageSize": "5"
    }
    print("=== Top Headlines ===")
    test_headlines = get_top_headlines(**headlines_params)
    print(test_headlines)
    with open("../data/test_headlines.json", "w") as f:
        json.dump(test_headlines, f, indent=4)

    print("\n=== Sources ===")
    sources_params = {
        "category": "technology",
        "language": "en",
        "country": "us"
    }
    test_sources = get_sources(**sources_params)
    print(test_sources)
    with open("../data/test_sources.json", "w") as f:
        json.dump(test_sources, f, indent=4)
