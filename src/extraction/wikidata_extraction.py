import requests
import pandas as pd
from pathlib import Path

# === CLIENTE WIKIDATA ===

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

# === PARSER DE DATOS ===

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

# === EXTRACCIÓN PRINCIPAL ===

def fetch_artist_data_from_wikidata(artist_name: str) -> dict:
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
        "VoiceType": extract_single_string(claims.get("P412", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}))
    }

def extract_wikidata(artist_names: list[str]):
    print("🚀 Iniciando extracción de Wikidata...")
    data = []
    for name in artist_names:
        artist_data = fetch_artist_data_from_wikidata(name)
        if artist_data:
            data.append(artist_data)

    if not data:
        print("⚠️ No se extrajo ningún dato.")
        return

    df = pd.DataFrame(data)
    output_dir = Path("extracted/WIKIDATA")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "wikidata_metadata.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Extracción completa. Datos guardados en: {output_path}")

def main():
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
