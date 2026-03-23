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
                        resolve_repo_path, require_str, require_int)

project_root = Path(__file__).resolve().parents[1]

# Load config variables
_cfg = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
_news_vars = require_section(_cfg, "news_vars")
_environment_path = require_section(_cfg, "environment")
_news_io_content = require_section(_cfg, "newsio")

NEWSIO_CONTENTS = require_list(_news_vars, "newsio_contents")
UNICODE_REPLACEMENTS = require_dict(_news_vars, "unicode_replacements")
ENVIRONMENT_PATH = resolve_repo_path(
        project_root, require_str(_environment_path, "environment_path"), ensure_parent=True)
NEWSIO_ENDPOINT = require_str(_news_io_content, "newsio_endpoint")

# All environmental variables
env_config = dotenv_values(ENVIRONMENT_PATH)
uri = env_config["NEWSDATAIO_API_URL"]
__api_key = env_config["NEWSDATAIO_API_KEY"]


def __normalize_text(text):
    if not isinstance(text, str):
        return text
    for unicode_char, ascii_char in UNICODE_REPLACEMENTS.items():
        text = text.replace(unicode_char, ascii_char)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "replace").decode("ascii")
    return text


def __build_query(endpoint, **kwargs):
    try:
        try:
            path_string = uri.replace("<ENDPOINT>", endpoint)
        except IndexError:
            print("Error: Index out of bounds")
        query_string = ""
        for key, value in kwargs.items():
            query_string += f"&{key}={value}"
        return path_string, query_string
    except IndexError:
        print("Error: Index out of bounds")


def __make_api_call(endpoint, **kwargs):
    path_string, query_string = __build_query(endpoint, **kwargs)
    query = f"{path_string}apikey={__api_key}{query_string}"
    try:
        response = re.get(query)
    except re.RequestException:
        print("Error: API call failed")
        return None
    return response.json()


def get_latest_news(**kwargs):
    result_json = __make_api_call(NEWSIO_ENDPOINT, **kwargs)
    if result_json is None:
        print("Error: API call failed")
        return None
    if result_json.get("status") != "success":
        print(f"Error: {result_json.get('results', {}).get('message', 'Unknown error')}")
        return None
    try:
        results = result_json["results"]
    except KeyError:
        print("Error: Key 'results' not found in JSON response")
        return None
    if not isinstance(results, list):
        print(f"Error: 'results' is not a list. Got: {type(results)}")
        return None
    final_result = {}
    index_int = 0 
    for result in results:
        if not isinstance(result, dict):
            continue
        add = {}
        for content in NEWSIO_CONTENTS:
            try:
                add[content] = __normalize_text(result[content])
            except KeyError:
                print(f"Error: Key '{content}' not found in JSON response")
                add[content] = None
        final_result[index_int] = add
        index_int += 1
    return final_result


if __name__ == "__main__":

    set_params = {
        "country": "in",
        "language": "en",
        "category": "politics",
        "removeduplicate": "1",
        "size": "10"
    }
    test_res = get_latest_news(**set_params)
    print(test_res)

    with open(f"{set_params['country']}_{set_params['category']}.json", "w") as f:
        json.dump(test_res, f, indent=4)
