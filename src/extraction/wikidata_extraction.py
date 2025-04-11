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
        Optional[str]: First entity ID found or None if no match.
    """
    # Define the Wikidata API endpoint and search parameters
    endpoint = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": artist_name
    }

    # Make a GET request to the Wikidata API
    response = requests.get(endpoint, params=params).json()

    # Return None if no results were found
    if not response.get("search"):
        return None

    # Return the ID of the first matched entity
    return response["search"][0]["id"]


def fetch_entity_claims(entity_id: str) -> Dict:
    """Fetch all claims (properties) for a Wikidata entity.

    Args:
        entity_id (str): Wikidata Q-ID.

    Returns:
        Dict: Claims dictionary for the specified entity.
    """
    # Define the Wikidata API endpoint and query parameters
    endpoint = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",  # Action to get entity data
        "format": "json",           # Response format
        "ids": entity_id,           # Entity ID (e.g., Q1299 for Bob Dylan)
        "props": "claims",          # We only want the claims section
        "languages": "en"           # Preferred language for labels
    }

    # Perform the GET request to fetch claims
    response = requests.get(endpoint, params=params).json()

    # Return the dictionary of claims for the given entity
    return response["entities"][entity_id]["claims"]

def get_label(qid: str) -> str:
    """Get English label from a Wikidata Q-ID.

    Args:
        qid (str): Wikidata Q-ID (e.g., 'Q1299').

    Returns:
        str: English label for the entity, or the Q-ID if not found.
    """
    # Construct the URL to access the entity data in JSON format
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

    # Fetch the entity data from Wikidata
    data = requests.get(url).json()

    # Attempt to retrieve the English label; fall back to Q-ID if not available
    return data["entities"][qid]["labels"].get("en", {}).get("value", qid)


# ==========================
# === DATA PARSING HELPERS ===
# ==========================

def extract_single_string(value: Any) -> str:
    """Extract a human-readable string from a value returned in a Wikidata claim.

    Args:
        value (Any): Raw value from a Wikidata claim.

    Returns:
        str: Extracted string (either plain text, label from Q-ID, or fallback string).
    """
    # If the value is a dictionary, check its structure
    if isinstance(value, dict):
        # Return direct text if present (common in language-specific labels)
        if "text" in value:
            return value["text"]

        # If it's a reference to another Wikidata entity, fetch its label
        if "id" in value:
            return get_label(value["id"])

    # Fallback: cast the value to string (covers numbers, strings, and edge cases)
    return str(value)


def extract_labels(claims: Dict, prop: str) -> List[str]:
    """Extract English labels from a specific Wikidata property.

    Args:
        claims (Dict): Dictionary of claims from a Wikidata entity.
        prop (str): Property ID to extract (e.g., 'P136' for genre).

    Returns:
        List[str]: List of human-readable labels.
    """
    # Return an empty list if the property is not present in the claims
    if prop not in claims:
        return []

    # Extract Q-IDs from the specified property claims
    qids = [
        c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
        for c in claims[prop]
        if c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
    ]

    # Convert Q-IDs to English labels using get_label
    return [get_label(qid) for qid in qids if qid]


def extract_date(claims: Dict, prop: str, length: int = 10) -> str:
    """Extract and format a date string from a Wikidata claim.

    Args:
        claims (Dict): Dictionary of claims from a Wikidata entity.
        prop (str): Property ID to extract (e.g., 'P569' for date of birth).
        length (int): Number of characters to keep from the date (default: 10 for YYYY-MM-DD).

    Returns:
        str: Extracted date string in truncated ISO format, or empty string if unavailable.
    """
    # Attempt to get the value of the first claim for the given property
    val = claims.get(prop, [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})

    # If the value is a dict (expected structure), extract and format the 'time' field
    return val.get("time", "").lstrip("+")[:length] if isinstance(val, dict) else ""


def get_image_url_from_claims(claims: Dict) -> str:
    """Extract the Wikimedia Commons image URL from Wikidata claims.

    Args:
        claims (Dict): Claims dictionary from a Wikidata entity.

    Returns:
        str: Direct URL to the image file, or an empty string if not found.
    """
    # Check if the image property (P18) exists in the claims
    if "P18" not in claims:
        return ""

    # Extract the image filename from the claim
    image_name = claims["P18"][0]["mainsnak"]["datavalue"]["value"]

    # Encode the filename for URL use (replace spaces with underscores)
    image_encoded = image_name.replace(" ", "_")

    # Construct the direct URL to the image using Special:FilePath
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_encoded}"

# ==========================
# === MAIN EXTRACTION ===
# ==========================

def fetch_artist_data_from_wikidata(artist_name: str) -> Dict[str, str]:
    """Fetch a structured artist profile from Wikidata using their name.

    Args:
        artist_name (str): Name of the artist to search.

    Returns:
        Dict[str, str]: Dictionary with extracted artist metadata, or empty if not found.
    """
    # Search for the Wikidata entity ID using the artist's name
    entity_id = search_entity_id(artist_name)
    if not entity_id:
        print(f"❌ No results for '{artist_name}'")
        return {}

    # Fetch all property claims for the found entity
    claims = fetch_entity_claims(entity_id)

    # Build a structured dictionary with selected properties
    return {
        "Artist": artist_name,

        # Birth name (P1477)
        "BirthName": extract_single_string(
            claims.get("P1477", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        ),

        # Date of birth (P569) — full date
        "DateOfBirth": extract_date(claims, "P569"),

        # Place of birth (P19)
        "PlaceOfBirth": extract_single_string(
            claims.get("P19", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        ),

        # Country of citizenship (P27)
        "CountryOfCitizenship": extract_single_string(
            claims.get("P27", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        ),

        # Work period start (P2031) — only year
        "WorkPeriodStart": extract_date(claims, "P2031", length=4),

        # Genres (P136) — list of Q-IDs converted to labels
        "Genres": ", ".join(extract_labels(claims, "P136")),

        # Instruments (P1303)
        "Instruments": ", ".join(extract_labels(claims, "P1303")),

        # Voice type (P412)
        "VoiceType": extract_single_string(
            claims.get("P412", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
        ),

        # Wikimedia Commons image URL (P18)
        "ImageURL": get_image_url_from_claims(claims)
    }


# ==========================
# === BATCH & CLI LOGIC ===
# ==========================

def extract_wikidata(artist_names: List[str]) -> None:
    """Extract Wikidata metadata for a list of artists and save it to a CSV file.

    Args:
        artist_names (List[str]): List of artist names to search and extract data for.
    """
    print("🚀 Starting Wikidata extraction...")

    # Fetch data for each artist (only keep non-empty results)
    data = [
        fetch_artist_data_from_wikidata(name)
        for name in artist_names
        if fetch_artist_data_from_wikidata(name)
    ]

    # If no data was successfully extracted, warn and exit
    if not data:
        print("⚠️ No data extracted.")
        return

    # Create output directory if it doesn't exist
    output_dir = Path("extracted/WIKIDATA")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data)

    # Define output CSV path and save the data
    path = output_dir / "wikidata_metadata.csv"
    df.to_csv(path, index=False)

    print(f"✅ Extraction complete. Data saved to: {path}")


def main() -> None:
    """Run an interactive Wikidata scraper session for individual artists."""
    print("\n🧠✨ Wikidata Artist Scraper: Ready to fetch metadata ✨🧠\n")

    while True:
        # Ask the user for an artist name
        artist = input("🎤 Enter the artist's name (or type 'exit' to quit): ").strip()

        # Exit loop if user types 'exit'
        if artist.lower() == 'exit':
            print("\n👋 Exiting Wikidata scraper. See you next time!")
            break

        # Warn if input is empty
        if not artist:
            print("⚠️  Please enter a valid artist name.\n")
            continue

        # Define the output path where the artist's data will be stored
        output_path = Path(f"raw/WIKIDATA/{artist}/wikidata_summary.csv")

        # Skip if the data has already been scraped and saved
        if output_path.exists():
            print(f"⏭️  Skipping '{artist}' (already scraped)\n")
            continue

        print("🔎 Please wait while we fetch data from Wikidata...\n")

        # Fetch the artist's data
        info = fetch_artist_data_from_wikidata(artist)

        if info:
            # Create parent folder if necessary and save to CSV
            df = pd.DataFrame([info])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)

            # Confirm success and preview the data
            print(f"✅ Data saved to {output_path}")
            print(df)
        else:
            print("❌ No data extracted.\n")


if __name__ == "__main__":
    main()