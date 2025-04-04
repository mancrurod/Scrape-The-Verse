import os
import sys
import time
import spotipy
import pandas as pd
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
from datetime import datetime

# =============== UTILS ===============

def sanitize(name: str) -> str:
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '-')
    return name.strip()

def get_artist_folder(artist_name: str) -> str:
    return sanitize(artist_name)

def with_retry(request_fn, *args, max_retries=5, **kwargs):
    retry_count = 0
    while retry_count < max_retries:
        try:
            return request_fn(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", 5))
                print(f"⏳ Rate limit hit. Waiting {retry_after}s (Retry {retry_count+1}/{max_retries})...")
                time.sleep(retry_after)
                retry_count += 1
            else:
                raise
        except Exception as e:
            wait = 2 ** retry_count
            print(f"⚠️ Unexpected error: {e}. Retrying in {wait}s (Retry {retry_count+1}/{max_retries})...")
            time.sleep(wait)
            retry_count += 1
    print("❌ Max retries exceeded.")
    return None

# =============== AUTH ===============

def load_credentials():

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        raise Exception(f".env file not found at {env_path}")

    load_dotenv(dotenv_path=env_path)

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        raise Exception("Missing Spotify credentials in .env")

    return client_id, client_secret, redirect_uri



def connect_to_spotify():
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
    user_info = sp.current_user()
    print(f"✅ Connected as: {user_info['display_name']}")
    return sp

# =============== FETCH ===============

def get_artist_id(sp, artist_name):
    results = with_retry(sp.search, q=f"artist:{artist_name}", type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])
    return items[0]["id"] if items else None

def get_artist_metadata(sp, artist_id):
    return with_retry(sp.artist, artist_id)

def get_album_tracks(sp, album_id):
    results = with_retry(sp.album_tracks, album_id)
    tracks = results['items']
    while results['next']:
        results = with_retry(sp.next, results)
        tracks.extend(results['items'])
    return tracks

def extract_track_metadata(sp, track_id):
    try:
        track_info = with_retry(sp.track, track_id)
        return {
            "Name": track_info.get("name"),
            "Artists": ", ".join([artist["name"] for artist in track_info.get("artists", [])]),
            "Album": track_info.get("album", {}).get("name"),
            "Release Date": track_info.get("album", {}).get("release_date"),
            "Popularity": track_info.get("popularity"),
            "Explicit": track_info.get("explicit"),
            "Duration (ms)": track_info.get("duration_ms")
        }
    except Exception as e:
        print(f"⚠️ Error fetching track metadata for {track_id}: {e}")
        return {}

# =============== STORAGE ===============

def save_album_data(artist_name, album_name, track_data):
    base_path = Path("raw")
    artist_folder = get_artist_folder(artist_name)
    album_folder = sanitize(album_name)
    full_path = base_path / "SPOTIFY" / artist_folder / album_folder
    full_path.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(track_data)
    df.to_csv(full_path / f"{album_folder}.csv", index=False)
    print(f"✅ Saved: {full_path / f'{album_folder}.csv'}")

def save_artist_metadata(artist_name, artist_metadata):
    base_path = Path("raw")
    artist_folder = get_artist_folder(artist_name)
    full_path = base_path / "SPOTIFY" / artist_folder
    full_path.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([artist_metadata])
    df.to_csv(full_path / f"{artist_folder}_metadata.csv", index=False)
    print(f"✅ Saved artist metadata: {full_path / f'{artist_folder}_metadata.csv'}")

def save_album_metadata(artist_name, album_name, album_metadata):
    base_path = Path("raw")
    artist_folder = get_artist_folder(artist_name)
    album_folder = sanitize(album_name)
    full_path = base_path / "SPOTIFY" / artist_folder / album_folder
    full_path.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([album_metadata])
    df.to_csv(full_path / f"{album_folder}_album_metadata.csv", index=False)
    print(f"✅ Saved album metadata: {full_path / f'{album_folder}_album_metadata.csv'}")

def album_fully_scraped(artist_name, album_name):
    base_path = Path("raw")
    artist_folder = get_artist_folder(artist_name)
    album_folder = sanitize(album_name)
    album_dir = base_path / "SPOTIFY" / artist_folder / album_folder
    artist_metadata_path = base_path / "SPOTIFY" / artist_folder / f"{artist_folder}_metadata.csv"
    album_metadata_path = album_dir / f"{album_folder}_album_metadata.csv"
    album_tracks_path = album_dir / f"{album_folder}.csv"
    return artist_metadata_path.exists() and album_metadata_path.exists() and album_tracks_path.exists()

# =============== LOGGING ===============

failed_album_log = []

def log_failed_album(artist_name, album_name):
    failed_album_log.append((artist_name, album_name))

def write_failed_log_to_file():
    if not failed_album_log:
        return
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_path = log_dir / f"failed_albums_{timestamp}.log"
    with open(log_path, "a", encoding="utf-8") as f:
        for artist, album in failed_album_log:
            f.write(f"{artist}|||{album}\n")
    print(f"\n📝 Appended failed albums to: {log_path}")

# =============== MAIN INTERACTIVE ENTRYPOINT ===============

def scrape_album(sp, artist_name, album_name, album_id):
    if album_fully_scraped(artist_name, album_name):
        print(f"⏭️  Skipping '{album_name}' by {artist_name} (already scraped)")
        return

    try:
        album_metadata = with_retry(sp.album, album_id)
        simplified_album_metadata = {
            "Name": album_metadata.get("name"),
            "Release Date": album_metadata.get("release_date"),
            "Total Tracks": album_metadata.get("total_tracks"),
            "Label": album_metadata.get("label"),
            "Popularity": album_metadata.get("popularity"),
            "Genres": ", ".join(album_metadata.get("genres", [])),
            "Album Type": album_metadata.get("album_type"),
            "URI": album_metadata.get("uri")
        }
        save_album_metadata(artist_name, album_name, simplified_album_metadata)

        tracks = get_album_tracks(sp, album_id)
        time.sleep(2)

        track_data = []
        for track in tracks:
            track_metadata = extract_track_metadata(sp, track["id"])
            if track_metadata:
                track_data.append(track_metadata)
            time.sleep(0.4)

        save_album_data(artist_name, album_name, track_data)
    except Exception as e:
        print(f"❌ Error processing album '{album_name}': {e}")
        log_failed_album(artist_name, album_name)

def scrape_full_artist_interactive(sp, artist_name):
    artist_id = get_artist_id(sp, artist_name)
    if not artist_id:
        print(f"❌ Artist not found: {artist_name}")
        return

    artist_metadata = get_artist_metadata(sp, artist_id)
    simplified_metadata = {
        "Name": artist_metadata.get("name"),
        "Genres": ", ".join(artist_metadata.get("genres", [])),
        "Followers": artist_metadata.get("followers", {}).get("total"),
        "Popularity": artist_metadata.get("popularity"),
        "URI": artist_metadata.get("uri")
    }
    save_artist_metadata(artist_name, simplified_metadata)

    results = sp.artist_albums(artist_id, album_type="album")
    album_items = results["items"]
    seen = set()
    while results["next"]:
        results = with_retry(sp.next, results)
        album_items.extend(results["items"])

    unique_albums = []
    for album in album_items:
        name = album["name"].lower()
        if name not in seen:
            seen.add(name)
            unique_albums.append(album)

    album_refs = [{"name": album["name"], "id": album["id"]} for album in unique_albums]
    for album in album_refs:
        scrape_album(sp, artist_name, album["name"], album["id"])

def scrape_single_album_interactive(sp, artist_name, album_name):
    search = with_retry(sp.search, q=f"album:{album_name} artist:{artist_name}", type="album", limit=10)
    items = search["albums"]["items"]
    album_id = None

    for item in items:
        result_album_name = item["name"].strip().lower()
        result_artist_names = [a["name"].lower() for a in item["artists"]]
        if album_name.lower().strip() == result_album_name and artist_name.lower() in result_artist_names:
            album_id = item["id"]
            break

    if not album_id:
        print(f"❌ Album '{album_name}' not found for '{artist_name}'")
        log_failed_album(artist_name, album_name)
        return

    scrape_album(sp, artist_name, album_name, album_id)

def main():
    print("\n🎧✨ Spotify Artist Scraper: Let's Get Those Tracks ✨🎧\n")
    sp = connect_to_spotify()

    while True:
        try:
            artist_name = input("🎤 Enter the artist's name (or type 'exit' to quit): ").strip()
            if artist_name.lower() == 'exit':
                print("\n👋 See you next time. Stay groovy! 🎵\n")
                break

            if not artist_name:
                print("⚠️  Please enter a valid artist name.\n")
                continue

            print(f"\n🔍 Searching Spotify for: '{artist_name}'...")
            print("   ⏳ Scraping metadata...\n")

            mode = input("🎯 Choose mode: (A) Full artist or (B) Single album [A/B]: ").strip().upper()
            if mode == 'A':
                scrape_full_artist_interactive(sp, artist_name)
                print(f"   ✅ Done scraping: '{artist_name}'\n" + "-" * 60 + "\n")
            elif mode == 'B':
                album_name = input("💿 Enter the album name: ").strip()
                if album_name:
                    scrape_single_album_interactive(sp, artist_name, album_name)
                    print(f"   ✅ Done scraping album: '{album_name}' by '{artist_name}'\n" + "-" * 60 + "\n")
                else:
                    print("⚠️  Please enter a valid album name.\n")
            else:
                print("⚠️  Invalid option. Please enter A or B.\n")

        except Exception as e:
            print(f"\n❌ An error occurred while processing '{artist_name}': {e}\n")
            sys.exit(1)

if __name__ == "__main__":
    main()
