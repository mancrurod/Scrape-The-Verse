import os
import sys
import time
import spotipy
import pandas as pd
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# =====================
# === UTILITIES =======
# =====================

def sanitize(name: str) -> str:
    """Replace invalid filename characters with hyphens.

    Args:
        name (str): Original name.

    Returns:
        str: Sanitized name.
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '-')
    return name.strip()

def get_artist_folder(artist_name: str) -> str:
    """Sanitize artist name for folder usage.

    Args:
        artist_name (str): Name of the artist.

    Returns:
        str: Folder-safe name.
    """
    return sanitize(artist_name)

def with_retry(request_fn, *args, max_retries: int = 5, **kwargs):
    """Wrapper for retrying API calls with exponential backoff.

    Args:
        request_fn: Function to call.
        max_retries (int): Maximum number of retries.

    Returns:
        Any: Response from request_fn or None.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            return request_fn(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                wait = int(e.headers.get("Retry-After", 5))
                print(f"⏳ Rate limited. Waiting {wait}s (Retry {retry_count + 1}/{max_retries})")
                time.sleep(wait)
                retry_count += 1
            else:
                raise
        except Exception as e:
            wait = 2 ** retry_count
            print(f"⚠️ Unexpected error: {e}. Retrying in {wait}s (Retry {retry_count + 1}/{max_retries})")
            time.sleep(wait)
            retry_count += 1
    print("❌ Max retries exceeded.")
    return None

# =====================
# === AUTHENTICATION ===
# =====================

def load_credentials() -> tuple[str, str, str]:
    """Load Spotify credentials from .env file.

    Returns:
        tuple[str, str, str]: client_id, client_secret, redirect_uri
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}")
    load_dotenv(dotenv_path=env_path)

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        raise EnvironmentError("Missing one or more Spotify credentials in .env")

    return client_id, client_secret, redirect_uri

def connect_to_spotify() -> spotipy.Spotify:
    """Authenticate using Spotipy and return the client.

    Returns:
        spotipy.Spotify: Authenticated Spotify client.
    """
    client_id, client_secret, redirect_uri = load_credentials()
    scope = "user-library-read user-read-private playlist-read-private"
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,
        cache_path=".spotify_cache"
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    user = sp.current_user()
    print(f"✅ Connected as: {user['display_name']}")
    return sp

# =====================
# === SPOTIFY FETCH ===
# =====================

def get_artist_id(sp: spotipy.Spotify, artist_name: str) -> Optional[str]:
    results = with_retry(sp.search, q=f"artist:{artist_name}", type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])
    return items[0]["id"] if items else None

def get_artist_metadata(sp: spotipy.Spotify, artist_id: str) -> dict:
    return with_retry(sp.artist, artist_id)

def get_album_tracks(sp: spotipy.Spotify, album_id: str) -> List[dict]:
    results = with_retry(sp.album_tracks, album_id)
    tracks = results['items']
    while results.get('next'):
        results = with_retry(sp.next, results)
        tracks.extend(results['items'])
    return tracks

def extract_track_metadata(sp: spotipy.Spotify, track_id: str) -> dict:
    try:
        track = with_retry(sp.track, track_id)
        return {
            "Name": track.get("name"),
            "Artists": ", ".join([a["name"] for a in track.get("artists", [])]),
            "Album": track.get("album", {}).get("name"),
            "Release Date": track.get("album", {}).get("release_date"),
            "Popularity": track.get("popularity"),
            "Explicit": track.get("explicit"),
            "Duration (ms)": track.get("duration_ms")
        }
    except Exception as e:
        print(f"⚠️ Error fetching metadata for track {track_id}: {e}")
        return {}

# =====================
# === DATA STORAGE ====
# =====================

def save_album_data(artist_name: str, album_name: str, track_data: List[dict]) -> None:
    folder = Path("raw/SPOTIFY") / get_artist_folder(artist_name) / sanitize(album_name)
    folder.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(track_data)
    df.to_csv(folder / f"{sanitize(album_name)}.csv", index=False)
    print(f"✅ Saved: {folder / f'{sanitize(album_name)}.csv'}")

def save_artist_metadata(artist_name: str, metadata: dict) -> None:
    folder = Path("raw/SPOTIFY") / get_artist_folder(artist_name)
    folder.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([metadata])
    df.to_csv(folder / f"{get_artist_folder(artist_name)}_metadata.csv", index=False)
    print(f"✅ Saved artist metadata: {folder / f'{get_artist_folder(artist_name)}_metadata.csv'}")

def save_album_metadata(artist_name: str, album_name: str, metadata: dict) -> None:
    folder = Path("raw/SPOTIFY") / get_artist_folder(artist_name) / sanitize(album_name)
    folder.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([metadata])
    df.to_csv(folder / f"{sanitize(album_name)}_album_metadata.csv", index=False)
    print(f"✅ Saved album metadata: {folder / f'{sanitize(album_name)}_album_metadata.csv'}")

def album_fully_scraped(artist_name: str, album_name: str) -> bool:
    base = Path("raw/SPOTIFY") / get_artist_folder(artist_name) / sanitize(album_name)
    return (
        (base / f"{sanitize(album_name)}.csv").exists() and
        (base / f"{sanitize(album_name)}_album_metadata.csv").exists() and
        (base.parent / f"{get_artist_folder(artist_name)}_metadata.csv").exists()
    )

# =====================
# === LOGGING FAILURES ===
# =====================

failed_album_log: List[tuple[str, str]] = []

def log_failed_album(artist_name: str, album_name: str) -> None:
    failed_album_log.append((artist_name, album_name))

def write_failed_log_to_file() -> None:
    if not failed_album_log:
        return
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"failed_albums_{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_path, "a", encoding="utf-8") as f:
        for artist, album in failed_album_log:
            f.write(f"{artist}|||{album}\n")
    print(f"📝 Failed albums logged to: {log_path}")

# =====================
# === MAIN SCRAPER ====
# =====================

def scrape_album(sp: spotipy.Spotify, artist_name: str, album_name: str, album_id: str) -> None:
    if album_fully_scraped(artist_name, album_name):
        print(f"⏭️  Skipping '{album_name}' by {artist_name} (already scraped)")
        return

    try:
        metadata = with_retry(sp.album, album_id)
        simplified = {
            "Name": metadata.get("name"),
            "Release Date": metadata.get("release_date"),
            "Total Tracks": metadata.get("total_tracks"),
            "Label": metadata.get("label"),
            "Popularity": metadata.get("popularity"),
            "Genres": ", ".join(metadata.get("genres", [])),
            "Album Type": metadata.get("album_type"),
            "URI": metadata.get("uri"),
            "ImageURL": metadata.get("images", [{}])[0].get("url", "")
        }
        save_album_metadata(artist_name, album_name, simplified)

        tracks = get_album_tracks(sp, album_id)
        time.sleep(2)

        track_data = [extract_track_metadata(sp, t["id"]) for t in tracks if t]
        time.sleep(0.4 * len(track_data))
        save_album_data(artist_name, album_name, track_data)

    except Exception as e:
        print(f"❌ Error processing '{album_name}': {e}")
        log_failed_album(artist_name, album_name)

def scrape_full_artist_interactive(sp: spotipy.Spotify, artist_name: str) -> None:
    artist_id = get_artist_id(sp, artist_name)
    if not artist_id:
        print(f"❌ Artist not found: {artist_name}")
        return

    metadata = get_artist_metadata(sp, artist_id)
    simplified = {
        "Name": metadata.get("name"),
        "Genres": ", ".join(metadata.get("genres", [])),
        "Followers": metadata.get("followers", {}).get("total"),
        "Popularity": metadata.get("popularity"),
        "URI": metadata.get("uri")
    }
    save_artist_metadata(artist_name, simplified)

    results = sp.artist_albums(artist_id, album_type="album")
    albums = results["items"]
    seen = set()

    while results.get("next"):
        results = with_retry(sp.next, results)
        albums.extend(results["items"])

    unique = []
    for album in albums:
        name = album["name"].lower()
        if name not in seen:
            seen.add(name)
            unique.append(album)

    for album in unique:
        scrape_album(sp, artist_name, album["name"], album["id"])

def scrape_single_album_interactive(sp: spotipy.Spotify, artist_name: str, album_name: str) -> None:
    search = with_retry(sp.search, q=f"album:{album_name} artist:{artist_name}", type="album", limit=10)
    items = search.get("albums", {}).get("items", [])
    album_id = None

    for item in items:
        if album_name.lower() == item["name"].strip().lower() and artist_name.lower() in [a["name"].lower() for a in item["artists"]]:
            album_id = item["id"]
            break

    if not album_id:
        print(f"❌ Album '{album_name}' not found for '{artist_name}'")
        log_failed_album(artist_name, album_name)
        return

    scrape_album(sp, artist_name, album_name, album_id)

# =====================
# === CLI ENTRYPOINT ===
# =====================

def main() -> None:
    print("\n🎧✨ Spotify Artist Scraper: Let's Get Those Tracks ✨🎧\n")
    sp = connect_to_spotify()

    while True:
        try:
            artist = input("🎤 Enter artist name (or 'exit'): ").strip()
            if artist.lower() == 'exit':
                break
            if not artist:
                print("⚠️ Enter a valid artist name.\n")
                continue

            mode = input("🎯 Mode: (A) Full artist or (B) Single album [A/B]: ").strip().upper()
            if mode == 'A':
                scrape_full_artist_interactive(sp, artist)
            elif mode == 'B':
                album = input("💿 Enter album name: ").strip()
                if album:
                    scrape_single_album_interactive(sp, artist, album)
                else:
                    print("⚠️ Enter a valid album name.\n")
            else:
                print("⚠️ Invalid option. Choose A or B.\n")
        except Exception as e:
            print(f"❌ Error: {e}")
            write_failed_log_to_file()
            sys.exit(1)

    write_failed_log_to_file()
    print("\n👋 Goodbye! 🎵")

if __name__ == "__main__":
    main()
