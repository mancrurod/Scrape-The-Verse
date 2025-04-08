import requests
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

# ==========================
# === WIKIDATA CLIENT ==== 
# ==========================

def search_entity_id(artist_name: str) -> Optional[str]:
    """Search for the Wikidata entity ID of a given artist.

    Args:
        artist_name (str): Name of the artist.

    Returns:
        Optional[str]: First entity ID found or None.
    """
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

def fetch_entity_claims(entity_id: str) -> Dict:
    """Fetch all claims (properties) for a Wikidata entity.

    Args:
        entity_id (str): Wikidata Q-ID.

    Returns:
        Dict: Claims dictionary.
    """
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
    """Get English label from a Wikidata Q-ID.

    Args:
        qid (str): Wikidata Q-ID.

    Returns:
        str: English label or Q-ID if not found.
    """
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    data = requests.get(url).json()
    return data["entities"][qid]["labels"].get("en", {}).get("value", qid)

# ==========================
# === DATA PARSING HELPERS ===
# ==========================

def extract_single_string(value: Any) -> str:
    if isinstance(value, dict):
        if "text" in value:
            return value["text"]
        if "id" in value:
            return get_label(value["id"])
    return str(value)

def extract_labels(claims: Dict, prop: str) -> List[str]:
    if prop not in claims:
        return []
    qids = [c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
            for c in claims[prop] if c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")]
    return [get_label(qid) for qid in qids if qid]

def extract_date(claims: Dict, prop: str, length: int = 10) -> str:
    val = claims.get(prop, [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
    return val.get("time", "").lstrip("+")[:length] if isinstance(val, dict) else ""

def get_image_url_from_claims(claims: Dict) -> str:
    if "P18" not in claims:
        return ""
    image_name = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
    image_encoded = image_name.replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_encoded}"

# ==========================
# === MAIN EXTRACTION ===
# ==========================

def fetch_artist_data_from_wikidata(artist_name: str) -> Dict[str, str]:
    entity_id = search_entity_id(artist_name)
    if not entity_id:
        print(f"❌ No results for '{artist_name}'")
        return {}

    claims = fetch_entity_claims(entity_id)
    return {
        "Artist": artist_name,
        "BirthName": extract_single_string(claims.get("P1477", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "DateOfBirth": extract_date(claims, "P569"),
        "PlaceOfBirth": extract_single_string(claims.get("P19", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "CountryOfCitizenship": extract_single_string(claims.get("P27", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "WorkPeriodStart": extract_date(claims, "P2031", length=4),
        "Genres": ", ".join(extract_labels(claims, "P136")),
        "Instruments": ", ".join(extract_labels(claims, "P1303")),
        "VoiceType": extract_single_string(claims.get("P412", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})),
        "ImageURL": get_image_url_from_claims(claims)
    }

# ==========================
# === BATCH & CLI LOGIC ===
# ==========================

def extract_wikidata(artist_names: List[str]) -> None:
    print("🚀 Starting Wikidata extraction...")
    data = [fetch_artist_data_from_wikidata(name) for name in artist_names if fetch_artist_data_from_wikidata(name)]

    if not data:
        print("⚠️ No data extracted.")
        return

    output_dir = Path("extracted/WIKIDATA")
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    path = output_dir / "wikidata_metadata.csv"
    df.to_csv(path, index=False)
    print(f"✅ Extraction complete. Data saved to: {path}")

def main() -> None:
    print("\n🧠✨ Wikidata Artist Scraper: Ready to fetch metadata ✨🧠\n")

    while True:
        artist = input("🎤 Enter the artist's name (or type 'exit' to quit): ").strip()
        if artist.lower() == 'exit':
            print("\n👋 Exiting Wikidata scraper. See you next time!")
            break
        if not artist:
            print("⚠️  Please enter a valid artist name.\n")
            continue

        output_path = Path(f"raw/WIKIDATA/{artist}/wikidata_summary.csv")
        if output_path.exists():
            print(f"⏭️  Skipping '{artist}' (already scraped)\n")
            continue

        print("🔎 Please wait while we fetch data from Wikidata...\n")
        info = fetch_artist_data_from_wikidata(artist)

        if info:
            df = pd.DataFrame([info])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"✅ Data saved to {output_path}")
            print(df)
        else:
            print("❌ No data extracted.\n")

if __name__ == "__main__":
    main()