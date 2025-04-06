import os
import re
import time
import requests
import unicodedata
import lyricsgenius
import pandas as pd
from csv import DictWriter
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# === UTILS ===

def sanitize(name: str) -> str:
    """
    Remove invalid characters from filenames (e.g., for Windows).
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name.strip()

def slugify(text: str) -> str:
    """
    Generate a slug-safe string for URLs (used in Genius album URLs).
    """
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[’'\"()]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def clean_up(song_title: str) -> str:
    """
    Clean song titles by removing suffixes like '(Ft...)' or 'Lyrics'.
    """
    if "Ft" in song_title:
        before_ft_pattern = re.compile(r".*(?=\(Ft)")
        song_title_before_ft = before_ft_pattern.search(song_title).group(0)
        clean_song_title = song_title_before_ft.strip().replace("/", "-")
    else:
        song_title_no_lyrics = song_title.replace("Lyrics", "")
        clean_song_title = song_title_no_lyrics.strip().replace("/", "-")
    return clean_song_title

def get_artist_folder(artist_name: str) -> str:
    """
    Sanitize the artist name to use as a folder.
    """
    return sanitize(artist_name)

# === AUTHENTICATION ===

def get_genius_client():
    """
    Load Genius API client using token from .env file.
    """
    project_root = Path.cwd()
    load_dotenv(dotenv_path=project_root / ".env")
    access_token = os.getenv("GENIUS_CLIENT_ACCESS_TOKEN")
    if not access_token:
        raise Exception("❌ Missing GENIUS_CLIENT_ACCESS_TOKEN in .env file.")
    genius = lyricsgenius.Genius(access_token, timeout=15)
    genius.remove_section_headers = True
    return genius

# === ALBUM FETCHING ===

def get_all_songs_from_album(artist: str, album_name: str):
    """
    Scrape the Genius album page and return a list of track numbers and cleaned song titles.
    """
    artist_slug = slugify(artist)
    album_slug = slugify(album_name)
    try:
        response = requests.get(f"https://genius.com/albums/{artist_slug}/{album_slug}", timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching album page: {e}")
        return []
    html_string = response.text
    document = BeautifulSoup(html_string, "html.parser")
    song_title_tags = document.find_all("h3", attrs={"class": "chart_row-content-title"})
    song_titles = [song_title.text for song_title in song_title_tags]
    return [(i + 1, clean_up(title)) for i, title in enumerate(song_titles)]

# === FILE MANAGEMENT ===

def get_album_path(artist_name: str, album_name: str) -> Path:
    """
    Generate and create the output folder for storing lyrics of a given album.
    """
    base_path = Path.cwd() / "raw" / "GENIUS"
    artist_folder = get_artist_folder(artist_name)
    album_folder = sanitize(album_name)
    album_path = base_path / artist_folder / album_folder
    album_path.mkdir(parents=True, exist_ok=True)
    return album_path

def save_lyrics_to_file(file_path: Path, song_object):
    """
    Save lyrics to a .txt file using lyricsgenius.
    """
    song_object.save_lyrics(filename=str(file_path), extension="txt", sanitize=False, overwrite=False)

def save_album_summary_csv(album_path: Path, album_name: str, summary_rows: list):
    """
    Save a CSV summary with song titles, lyrics availability, and Genius URLs.
    """
    csv_name = f"{sanitize(album_name)}.csv"
    csv_path = album_path / csv_name
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = DictWriter(f, fieldnames=["Track #", "Title", "Has Lyrics", "Genius URL"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"📄 CSV summary saved: {csv_path.name}")

# === LOGGING ===

FAILED_LOG_PATH = Path.cwd() / "logs"
FAILED_LOG_PATH.mkdir(parents=True, exist_ok=True)

def log_failed_lyrics(artist: str, album: str, song_title: str, reason: str):
    """
    Log lyrics that could not be fetched, including the reason and timestamp.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = FAILED_LOG_PATH / f"failed_lyrics_{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Artist: {artist} | Album: {album} | Song: {song_title} | Reason: {reason}\n")

# === SCRAPING FUNCTION ===

def download_album_lyrics(artist: str, album_name: str):
    """
    Download all lyrics for a given artist and album from Genius.
    - Scrapes tracklist from the Genius album page.
    - Searches each song via the Genius API.
    - Saves lyrics to text files and generates a CSV summary.
    - Skips already-downloaded songs.
    """
    album_path = get_album_path(artist, album_name)
    summary_csv = album_path / f"{sanitize(album_name)}.csv"

    if summary_csv.exists():
        print(f"⏭️  Skipping '{album_name}' by {artist} (already scraped)")
        return

    print(f"🎤 Scraping '{album_name}' by {artist}...")
    genius = get_genius_client()
    clean_songs = get_all_songs_from_album(artist, album_name)

    if not clean_songs:
        print(f"❌ No songs found for album: {album_name}")
        return

    summary_rows = []

    for track_number, song in clean_songs:
        file_path = album_path / f"{sanitize(song)}.txt"
        if file_path.exists():
            print(f"⏭️  Skipping '{song}' (already downloaded)")
            summary_rows.append({
                "Track #": track_number,
                "Title": song,
                "Has Lyrics": "✅",
                "Genius URL": "Already saved"
            })
            continue

        print(f"🎶 {song}")
        try:
            song_object = genius.search_song(song, artist)
        except Exception as e:
            print(f"⏱️ Error while fetching '{song}': {e}")
            song_object = None
            log_failed_lyrics(artist, album_name, song, str(e))
            continue

        has_lyrics = "✅" if song_object else "❌"
        genius_url = song_object.url if song_object else "N/A"

        if song_object:
            save_lyrics_to_file(file_path, song_object)
            print(f"✅ Saved: {file_path.name}")
        else:
            print(f"❌ No lyrics found for: {song}")
            log_failed_lyrics(artist, album_name, song, "No lyrics found")

        summary_rows.append({
            "Track #": track_number,
            "Title": song,
            "Has Lyrics": has_lyrics,
            "Genius URL": genius_url
        })

        # Respectful delay between requests
        time.sleep(1)

    save_album_summary_csv(album_path, album_name, summary_rows)

# === BUILD ARTIST → ALBUM STRUCTURE ===

def build_artist_albums_from_spotify_raw() -> dict:
    """
    Scan the raw/SPOTIFY directory to determine available artists and albums.
    This structure is used to batch scrape lyrics from Genius.
    """
    base_path = Path("raw/SPOTIFY")
    if not base_path.exists():
        print("❌ 'raw/SPOTIFY' directory not found. Run Spotify extraction first.")
        return {}

    artist_albums = {}
    for artist_folder in base_path.iterdir():
        if not artist_folder.is_dir():
            continue
        artist_name = artist_folder.name
        albums = [
            subfolder.name for subfolder in artist_folder.iterdir()
            if subfolder.is_dir()
        ]
        if albums:
            artist_albums[artist_name] = albums
    return artist_albums

# === MAIN EXECUTION ===

def main():
    """
    Main CLI to run batch scraping of lyrics.
    Iterates over all artist/album pairs derived from the raw Spotify folder
    and downloads lyrics from Genius, skipping those already downloaded.
    """
    print("\n🎤✨ Genius Lyrics Scraper: Batch Mode Activated ✨🎤\n")

    artist_albums = build_artist_albums_from_spotify_raw()
    if not artist_albums:
        print("⚠️ No artist/album data found in 'raw/SPOTIFY'. Exiting.")
        return

    for artist, albums in artist_albums.items():
        print(f"🎼 Artist: {artist}")
        for album in albums:
            print(f"   📀 Album: {album}")
            print("   ⏳ Downloading lyrics...\n")
            try:
                download_album_lyrics(artist, album)
                print(f"   ✅ Finished downloading: '{album}' by {artist}\n" + "-" * 60 + "\n")
            except Exception as e:
                print(f"   ❌ Error for '{album}' by {artist}: {e}\n" + "-" * 60 + "\n")
                log_failed_lyrics(artist, album, "N/A", str(e))

    print("✅ Finished batch scrape! Check logs for any failed lyrics.\n")

if __name__ == "__main__":
    main()
