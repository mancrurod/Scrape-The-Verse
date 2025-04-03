import json
import difflib
from pathlib import Path

FALLBACK_FILE = Path(__file__).resolve().parents[2] / "logs" / "missing_albums.json"

def load_fallbacks():
    if not FALLBACK_FILE.exists():
        return {}
    with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_fallbacks(fallbacks):
    FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(fallbacks, f, indent=4)


def auto_resolve_album_id(sp, artist_name, album_name):
    query = f"album:{album_name} artist:{artist_name}"
    results = sp.search(q=query, type="album", limit=10)
    items = results["albums"]["items"]

    if not items:
        return None

    best_score = 0
    best_match = None
    for item in items:
        result_album_name = item["name"].lower()
        result_artists = [a["name"].lower() for a in item["artists"]]
        score = difflib.SequenceMatcher(None, album_name.lower(), result_album_name).ratio()

        # Bonus if the correct artist is in the artist list
        if artist_name.lower() in result_artists:
            score += 0.2

        if score > best_score:
            best_score = score
            best_match = item

    return best_match["id"] if best_score >= 0.6 else None

def resolve_album_id_from_user(sp, artist_name, album_name):
    print(f"🔗 Please provide the Spotify URL or album ID for: '{album_name}' by '{artist_name}'")
    print("👉 Example: https://open.spotify.com/album/6YabPKtZAjxwyWbuO9p4ZD")
    
    raw_input = input("Paste album URL or ID (or leave blank to skip): ").strip()

    if not raw_input:
        print("⏭️ Skipping manual ID entry.")
        return None

    # Extract ID from URL if needed
    if "open.spotify.com/album/" in raw_input:
        album_id = raw_input.split("album/")[-1].split("?")[0]
    else:
        album_id = raw_input

    try:
        sp.album(album_id)  # Check if ID is valid
        return album_id
    except Exception as e:
        print(f"❌ Invalid album ID: {e}")
        return None

