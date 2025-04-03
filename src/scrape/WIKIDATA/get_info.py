import pandas as pd
from pathlib import Path
from src.scrape.WIKIDATA.wikidata_client import search_entity_id, fetch_entity_claims
from src.scrape.WIKIDATA.wikidata_parser import extract_single_string, extract_labels, extract_date


def fetch_artist_data_from_wikidata(artist_name: str) -> dict:
    entity_id = search_entity_id(artist_name)
    if not entity_id:
        print(f"❌ No results for '{artist_name}'")
        return {}

    claims = fetch_entity_claims(entity_id)

    return {
        "BirthName": extract_single_string(claims.get("P1477", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "DateOfBirth": extract_date(claims, "P569"),
        "PlaceOfBirth": extract_single_string(claims.get("P19", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "CountryOfCitizenship": extract_single_string(claims.get("P27", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "WorkPeriodStart": extract_date(claims, "P2031", length=4),
        "Genres": ", ".join(extract_labels(claims, "P136")),
        "Instruments": ", ".join(extract_labels(claims, "P1303")),
        "VoiceType": extract_single_string(claims.get("P412", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}))
    }