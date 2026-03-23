# Standard Library Imports
from pathlib import Path
import requests as re
import unicodedata

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
NEWSIO_ENDPOINT = require_int(_news_io_content, "newsio_endpoint")

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
    try:
        results = result_json["results"]
    except KeyError:
        print("Error: Key 'results' not found in JSON response")
        return None
    final_result = {}
    for result in results:
        add = {}
        for content in NEWSIO_CONTENTS:
            try:
                if content != "article_id":
                    add[content] = __normalize_text(result[content])
            except KeyError:
                print(f"Error: Key '{content}' not found in JSON response")
                add[content] = None
        final_result[result["article_id"]] = add
    return final_result


# if __name__ == "__main__":

#     set_params = {
#         "country": "in",
#         "language": "en",
#         "category": "politics",
#         "removedduplicate": "1",
#         "size": "10"
#     }
#     print(get_latest_news(**set_params))
