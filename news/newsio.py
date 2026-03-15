from dotenv import dotenv_values
import requests as re

# All environmental variables
config = dotenv_values("../.env")
uri = config["NEWSDATAIO_API_URL"]
__api_key = config["NEWSDATAIO_API_KEY"]

# content variables
contents = ["article_id", "title", "description", "keywords", "country",
            "category", "source_name"]


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


def make_api_call(endpoint, **kwargs):
    path_string, query_string = __build_query(endpoint, **kwargs)
    query = f"{path_string}apikey={__api_key}{query_string}"
    try:
        response = re.get(query)
    except re.RequestException:
        print("Error: API call failed")
        return None
    return response.json()


def get_latest_news(**kwargs):
    result_json = make_api_call("latest", **kwargs)
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
        for content in contents:
            try:
                if content != "article_id":
                    add[content] = result[content]
            except KeyError:
                print(f"Error: Key '{content}' not found in JSON response")
                add[content] = None
        final_result[result["article_id"]] = add
    return final_result


if __name__ == "__main__":

    set_params = {
        "country": "in",
        "language": "en",
        "category": "politics",
        "removedduplicate": "1",
        "size": "10"
    }
    print(get_latest_news(**set_params))
