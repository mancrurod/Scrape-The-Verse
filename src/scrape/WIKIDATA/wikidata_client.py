import requests


def search_entity_id(artist_name: str) -> str:
    endpoint = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": artist_name
    }
    response = requests.get(endpoint, params=params).json()
    if not response.get("search"):
        return None
    return response["search"][0]["id"]


def fetch_entity_claims(entity_id: str) -> dict:
    endpoint = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": entity_id,
        "props": "claims",
        "languages": "en"
    }
    response = requests.get(endpoint, params=params).json()
    return response["entities"][entity_id]["claims"]


def get_label(qid: str) -> str:
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    data = requests.get(url).json()
    return data["entities"][qid]["labels"].get("en", {}).get("value", qid)
