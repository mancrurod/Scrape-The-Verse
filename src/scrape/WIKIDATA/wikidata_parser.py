from src.scrape.WIKIDATA.wikidata_client import get_label


def extract_single_string(value):
    if isinstance(value, dict):
        if "text" in value:
            return value["text"]
        if "id" in value:
            return get_label(value["id"])
    return value


def extract_labels(claims, prop):
    if prop not in claims:
        return []
    qids = []
    for claim in claims[prop]:
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "id" in val:
            qids.append(val["id"])
    return [get_label(qid) for qid in qids]


def extract_date(claims, prop, length=10):
    val = claims.get(prop, [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
    return val.get("time", "").lstrip("+")[:length] if isinstance(val, dict) else ""
