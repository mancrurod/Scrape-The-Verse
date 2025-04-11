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
    # List of characters not allowed in filenames on most operating systems
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

    # Remove each invalid character from the string
    for char in invalid_chars:
        name = name.replace(char, '')

    # Remove leading and trailing whitespace
    return name.strip()


def slugify(text: str) -> str:
    """Create a URL-safe slug from a string.

    Args:
        text (str): Input string.

    Returns:
        str: Slugified string.
    """
    # Convert to lowercase for consistency
    text = text.lower()

    # Normalize Unicode characters to ASCII equivalents
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    # Remove common punctuation like apostrophes and parentheses
    text = re.sub(r"[’'\"()]+", "", text)

    # Replace any sequence of non-alphanumeric characters with a single hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Remove leading and trailing hyphens
    return text.strip("-")


def clean_up(song_title: str) -> str:
    """Clean song titles from extra content like '(Ft...)' or 'Lyrics'.

    Args:
        song_title (str): Original song title.

    Returns:
        str: Cleaned song title.
    """
    # If the song title contains 'Ft', attempt to remove the featuring part
    if "Ft" in song_title:
        # Use regex to match everything before the opening parenthesis preceding 'Ft'
        match = re.search(r".*(?=\\(Ft)", song_title)
        song_title = match.group(0) if match else song_title

    # Remove occurrences of the word 'Lyrics'
    song_title = song_title.replace("Lyrics", "")

    # Replace slashes with hyphens and trim surrounding whitespace
    return song_title.strip().replace("/", "-")


def get_artist_folder(artist_name: str) -> str:
    """Sanitize artist name for folder use.

    Args:
        artist_name (str): Name of artist.

    Returns:
        str: Sanitized folder name.
    """
    # Use the sanitize function to remove invalid characters from the artist name
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
    # Load environment variables from the .env file in the current working directory
    load_dotenv(Path.cwd() / ".env")

    # Retrieve the Genius API access token from the environment
    access_token = os.getenv("GENIUS_CLIENT_ACCESS_TOKEN")

    # Raise an exception if the token is not found
    if not access_token:
        raise Exception("❌ Missing GENIUS_CLIENT_ACCESS_TOKEN in .env file.")

    # Initialize Genius client with the token and a custom timeout
    client = lyricsgenius.Genius(access_token, timeout=15)

    # Optional: remove section headers like [Chorus], [Verse], etc.
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
    # Construct the Genius album URL using slugified artist and album names
    url = f"https://genius.com/albums/{slugify(artist)}/{slugify(album_name)}"

    try:
        # Request the album page content with a timeout
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        # Print and return empty list if the request fails
        print(f"❌ Error fetching album page: {e}")
        return []

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract song title elements from the album chart
    song_tags = soup.find_all("h3", class_="chart_row-content-title")

    # Return a list of (track number, cleaned song title) tuples
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
    # Define the base path where lyrics will be stored
    base_path = Path.cwd() / "raw" / "GENIUS"

    # Build the full path using sanitized artist and album names
    album_path = base_path / sanitize(artist_name) / sanitize(album_name)

    # Create the directory structure if it doesn't already exist
    album_path.mkdir(parents=True, exist_ok=True)

    # Return the path to the album folder
    return album_path


def save_lyrics_to_file(file_path: Path, song_object) -> None:
    """Save lyrics to a text file.

    Args:
        file_path (Path): Output file path.
        song_object (lyricsgenius.song.Song): Genius song object.
    """
    # Save the lyrics to the specified file path as a plain text file
    # `sanitize=False` assumes the filename is already safe
    # `overwrite=False` prevents overwriting existing files
    song_object.save_lyrics(filename=str(file_path), extension="txt", sanitize=False, overwrite=False)


def save_album_summary_csv(album_path: Path, album_name: str, summary_rows: List[Dict]) -> None:
    """Save summary of lyrics scraping to CSV.

    Args:
        album_path (Path): Path to album folder.
        album_name (str): Album name.
        summary_rows (List[Dict]): List of song metadata.
    """
    # Construct the path to the CSV file using a sanitized album name
    csv_file = album_path / f"{sanitize(album_name)}.csv"

    # Open the CSV file for writing, ensuring proper encoding and newline handling
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        # Initialize the CSV writer with expected column headers
        writer = DictWriter(f, fieldnames=["Track #", "Title", "Has Lyrics", "Genius URL"])
        
        # Write header row
        writer.writeheader()

        # Write all summary rows (one per track)
        writer.writerows(summary_rows)

    # Log confirmation message
    print(f"📄 CSV summary saved: {csv_file.name}")


# ======================
# === LOGGING SETUP ===
# ======================

# Define the base path for logging failed lyric fetches
FAILED_LOG_PATH = Path.cwd() / "logs"

# Ensure the log directory exists (create it if necessary)
FAILED_LOG_PATH.mkdir(parents=True, exist_ok=True)

def log_failed_lyrics(artist: str, album: str, song_title: str, reason: str) -> None:
    """Log songs that failed to fetch lyrics.

    Args:
        artist (str): Artist name.
        album (str): Album name.
        song_title (str): Song title.
        reason (str): Reason for failure.
    """
    # Create a log file named with the current date
    log_file = FAILED_LOG_PATH / f"failed_lyrics_{datetime.now().date()}.log"

    # Format a timestamp for the log entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append the failed fetch information to the log file
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
    # Build the path to the album folder and check for existing CSV summary
    album_path = get_album_path(artist, album_name)
    csv_file = album_path / f"{sanitize(album_name)}.csv"

    # Skip album if it has already been processed
    if csv_file.exists():
        print(f"⏭️  Skipping '{album_name}' by {artist} (already scraped)")
        return

    print(f"🎤 Scraping '{album_name}' by {artist}...")

    # Initialize Genius client and get the list of tracks from the album
    genius = get_genius_client()
    tracks = get_all_songs_from_album(artist, album_name)

    # Exit if no tracks were found
    if not tracks:
        print(f"❌ No songs found for album: {album_name}")
        return

    summary = []  # To store summary info for each track

    for track_number, title in tracks:
        file_path = album_path / f"{sanitize(title)}.txt"

        # Skip if lyrics for the song have already been downloaded
        if file_path.exists():
            print(f"⏭️  Skipping '{title}' (already downloaded)")
            summary.append({
                "Track #": track_number,
                "Title": title,
                "Has Lyrics": "✅",
                "Genius URL": "Already saved"
            })
            continue

        print(f"🎶 {title}")

        try:
            # Search for the song on Genius
            song = genius.search_song(title, artist)
        except Exception as e:
            # Handle unexpected errors during search
            print(f"⏱️ Error while fetching '{title}': {e}")
            log_failed_lyrics(artist, album_name, title, str(e))
            continue

        if song:
            # Save the lyrics to a .txt file
            save_lyrics_to_file(file_path, song)
            print(f"✅ Saved: {file_path.name}")
            summary.append({
                "Track #": track_number,
                "Title": title,
                "Has Lyrics": "✅",
                "Genius URL": song.url
            })
        else:
            # If no lyrics were found, log and mark as missing
            print(f"❌ No lyrics found for: {title}")
            summary.append({
                "Track #": track_number,
                "Title": title,
                "Has Lyrics": "❌",
                "Genius URL": "N/A"
            })
            log_failed_lyrics(artist, album_name, title, "No lyrics found")

        # Respect API rate limits
        time.sleep(1)

    # Save CSV summary of all processed tracks
    save_album_summary_csv(album_path, album_name, summary)


# =================================
# === ARTIST/ALBUM STRUCTURE ===
# =================================

def build_artist_albums_from_spotify_raw() -> Dict[str, List[str]]:
    """Scan raw/SPOTIFY to build artist → albums map.

    Returns:
        Dict[str, List[str]]: Dictionary of artists and albums.
    """
    # Define the base path to the raw Spotify data
    base_path = Path("raw/SPOTIFY")

    # Check if the directory exists; if not, alert and return empty result
    if not base_path.exists():
        print("❌ 'raw/SPOTIFY' directory not found. Run Spotify extraction first.")
        return {}

    artist_albums = {}

    # Iterate through artist directories
    for artist_folder in base_path.iterdir():
        if not artist_folder.is_dir():
            continue  # Skip non-directory files

        # Get a list of album folder names within the artist directory
        albums = [folder.name for folder in artist_folder.iterdir() if folder.is_dir()]

        # Only add artist if albums were found
        if albums:
            artist_albums[artist_folder.name] = albums

    # Return the dictionary mapping artists to their albums
    return artist_albums


# ======================
# === MAIN ROUTINE  ===
# ======================

def main() -> None:
    """Main function to run batch lyrics scraping."""
    print("\n🎤✨ Genius Lyrics Scraper: Batch Mode Activated ✨🎤\n")

    # Build dictionary mapping artists to their albums based on local Spotify data
    artist_albums = build_artist_albums_from_spotify_raw()

    # Exit if no valid data was found
    if not artist_albums:
        print("⚠️ No artist/album data found. Exiting.")
        return

    # Iterate over each artist and their albums
    for artist, albums in artist_albums.items():
        print(f"🎼 Artist: {artist}")
        for album in albums:
            print(f"   📀 Album: {album}\n   ⏳ Downloading lyrics...\n")
            try:
                # Attempt to download lyrics for the album
                download_album_lyrics(artist, album)
                print(f"   ✅ Finished: '{album}' by {artist}\n" + "-" * 60 + "\n")
            except Exception as e:
                # Log any unexpected errors during album processing
                print(f"   ❌ Error for '{album}' by {artist}: {e}\n" + "-" * 60 + "\n")
                log_failed_lyrics(artist, album, "N/A", str(e))

    # Final confirmation message after processing all albums
    print("✅ Batch scrape complete! Check logs for any failed lyrics.\n")


if __name__ == "__main__":
    main()
