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
from typing import List, Tuple, Dict, Optional

# =======================
# === UTILITY METHODS ===
# =======================

def sanitize(name: str) -> str:
    """Remove characters invalid for filenames.

    Args:
        name (str): Original string.

    Returns:
        str: Sanitized string.
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name.strip()

def slugify(text: str) -> str:
    """Create a URL-safe slug from a string.

    Args:
        text (str): Input string.

    Returns:
        str: Slugified string.
    """
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[’'\"()]+", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def clean_up(song_title: str) -> str:
    """Clean song titles from extra content like '(Ft...)' or 'Lyrics'.

    Args:
        song_title (str): Original song title.

    Returns:
        str: Cleaned song title.
    """
    if "Ft" in song_title:
        match = re.search(r".*(?=\\(Ft)", song_title)
        song_title = match.group(0) if match else song_title
    song_title = song_title.replace("Lyrics", "")
    return song_title.strip().replace("/", "-")

def get_artist_folder(artist_name: str) -> str:
    """Sanitize artist name for folder use.

    Args:
        artist_name (str): Name of artist.

    Returns:
        str: Sanitized folder name.
    """
    return sanitize(artist_name)

# ==========================
# === GENIUS API CLIENT ===
# ==========================

def get_genius_client() -> lyricsgenius.Genius:
    """Authenticate and return Genius API client.

    Returns:
        lyricsgenius.Genius: Authenticated Genius client.

    Raises:
        Exception: If token is missing.
    """
    load_dotenv(Path.cwd() / ".env")
    access_token = os.getenv("GENIUS_CLIENT_ACCESS_TOKEN")
    if not access_token:
        raise Exception("❌ Missing GENIUS_CLIENT_ACCESS_TOKEN in .env file.")
    client = lyricsgenius.Genius(access_token, timeout=15)
    client.remove_section_headers = True
    return client

# =============================
# === ALBUM PAGE SCRAPING ===
# =============================

def get_all_songs_from_album(artist: str, album_name: str) -> List[Tuple[int, str]]:
    """Scrape Genius album page and return tracklist.

    Args:
        artist (str): Artist name.
        album_name (str): Album title.

    Returns:
        List[Tuple[int, str]]: List of track number and clean title pairs.
    """
    url = f"https://genius.com/albums/{slugify(artist)}/{slugify(album_name)}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching album page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    song_tags = soup.find_all("h3", class_="chart_row-content-title")
    return [(i + 1, clean_up(tag.text)) for i, tag in enumerate(song_tags)]

# =============================
# === FILE HANDLING UTILS ===
# =============================

def get_album_path(artist_name: str, album_name: str) -> Path:
    """Create album folder structure.

    Args:
        artist_name (str): Artist name.
        album_name (str): Album name.

    Returns:
        Path: Path to album directory.
    """
    base_path = Path.cwd() / "raw" / "GENIUS"
    album_path = base_path / sanitize(artist_name) / sanitize(album_name)
    album_path.mkdir(parents=True, exist_ok=True)
    return album_path

def save_lyrics_to_file(file_path: Path, song_object: lyricsgenius.song.Song) -> None:
    """Save lyrics to a text file.

    Args:
        file_path (Path): Output file path.
        song_object (lyricsgenius.song.Song): Genius song object.
    """
    song_object.save_lyrics(filename=str(file_path), extension="txt", sanitize=False, overwrite=False)

def save_album_summary_csv(album_path: Path, album_name: str, summary_rows: List[Dict]) -> None:
    """Save summary of lyrics scraping to CSV.

    Args:
        album_path (Path): Path to album folder.
        album_name (str): Album name.
        summary_rows (List[Dict]): List of song metadata.
    """
    csv_file = album_path / f"{sanitize(album_name)}.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = DictWriter(f, fieldnames=["Track #", "Title", "Has Lyrics", "Genius URL"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"📄 CSV summary saved: {csv_file.name}")

# ======================
# === LOGGING SETUP ===
# ======================

FAILED_LOG_PATH = Path.cwd() / "logs"
FAILED_LOG_PATH.mkdir(parents=True, exist_ok=True)

def log_failed_lyrics(artist: str, album: str, song_title: str, reason: str) -> None:
    """Log songs that failed to fetch lyrics.

    Args:
        artist (str): Artist name.
        album (str): Album name.
        song_title (str): Song title.
        reason (str): Reason for failure.
    """
    log_file = FAILED_LOG_PATH / f"failed_lyrics_{datetime.now().date()}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Artist: {artist} | Album: {album} | Song: {song_title} | Reason: {reason}\n")

# ========================
# === SCRAPING ENGINE ===
# ========================

def download_album_lyrics(artist: str, album_name: str) -> None:
    """Download all lyrics from a given album via Genius.

    Args:
        artist (str): Artist name.
        album_name (str): Album name.
    """
    album_path = get_album_path(artist, album_name)
    csv_file = album_path / f"{sanitize(album_name)}.csv"

    if csv_file.exists():
        print(f"⏭️  Skipping '{album_name}' by {artist} (already scraped)")
        return

    print(f"🎤 Scraping '{album_name}' by {artist}...")
    genius = get_genius_client()
    tracks = get_all_songs_from_album(artist, album_name)

    if not tracks:
        print(f"❌ No songs found for album: {album_name}")
        return

    summary = []
    for track_number, title in tracks:
        file_path = album_path / f"{sanitize(title)}.txt"

        if file_path.exists():
            print(f"⏭️  Skipping '{title}' (already downloaded)")
            summary.append({"Track #": track_number, "Title": title, "Has Lyrics": "✅", "Genius URL": "Already saved"})
            continue

        print(f"🎶 {title}")
        try:
            song = genius.search_song(title, artist)
        except Exception as e:
            print(f"⏱️ Error while fetching '{title}': {e}")
            log_failed_lyrics(artist, album_name, title, str(e))
            continue

        if song:
            save_lyrics_to_file(file_path, song)
            print(f"✅ Saved: {file_path.name}")
            summary.append({"Track #": track_number, "Title": title, "Has Lyrics": "✅", "Genius URL": song.url})
        else:
            print(f"❌ No lyrics found for: {title}")
            summary.append({"Track #": track_number, "Title": title, "Has Lyrics": "❌", "Genius URL": "N/A"})
            log_failed_lyrics(artist, album_name, title, "No lyrics found")

        time.sleep(1)

    save_album_summary_csv(album_path, album_name, summary)

# =================================
# === ARTIST/ALBUM STRUCTURE ===
# =================================

def build_artist_albums_from_spotify_raw() -> Dict[str, List[str]]:
    """Scan raw/SPOTIFY to build artist → albums map.

    Returns:
        Dict[str, List[str]]: Dictionary of artists and albums.
    """
    base_path = Path("raw/SPOTIFY")
    if not base_path.exists():
        print("❌ 'raw/SPOTIFY' directory not found. Run Spotify extraction first.")
        return {}

    artist_albums = {}
    for artist_folder in base_path.iterdir():
        if not artist_folder.is_dir():
            continue
        albums = [folder.name for folder in artist_folder.iterdir() if folder.is_dir()]
        if albums:
            artist_albums[artist_folder.name] = albums
    return artist_albums

# ======================
# === MAIN ROUTINE  ===
# ======================

def main() -> None:
    """Main function to run batch lyrics scraping."""
    print("\n🎤✨ Genius Lyrics Scraper: Batch Mode Activated ✨🎤\n")
    artist_albums = build_artist_albums_from_spotify_raw()

    if not artist_albums:
        print("⚠️ No artist/album data found. Exiting.")
        return

    for artist, albums in artist_albums.items():
        print(f"🎼 Artist: {artist}")
        for album in albums:
            print(f"   📀 Album: {album}\n   ⏳ Downloading lyrics...\n")
            try:
                download_album_lyrics(artist, album)
                print(f"   ✅ Finished: '{album}' by {artist}\n" + "-" * 60 + "\n")
            except Exception as e:
                print(f"   ❌ Error for '{album}' by {artist}: {e}\n" + "-" * 60 + "\n")
                log_failed_lyrics(artist, album, "N/A", str(e))

    print("✅ Batch scrape complete! Check logs for any failed lyrics.\n")

if __name__ == "__main__":
    main()
