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
    # List of characters that are not allowed in filenames
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

    # Replace each invalid character with a hyphen
    for char in invalid_chars:
        name = name.replace(char, '-')

    # Remove leading and trailing whitespace
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
    retry_count = 0  # Tracks the number of retry attempts

    while retry_count < max_retries:
        try:
            # Attempt to execute the request function with provided arguments
            return request_fn(*args, **kwargs)

        except spotipy.exceptions.SpotifyException as e:
            # Specific handling for rate-limiting (HTTP 429)
            if e.http_status == 429:
                # Use the "Retry-After" header from the response, or default to 5 seconds
                wait = int(e.headers.get("Retry-After", 5))
                print(f"⏳ Rate limited. Waiting {wait}s (Retry {retry_count + 1}/{max_retries})")
                time.sleep(wait)
                retry_count += 1
            else:
                # Re-raise other Spotify exceptions that aren't handled explicitly
                raise

        except Exception as e:
            # Handle unexpected errors with exponential backoff (2^retry_count seconds)
            wait = 2 ** retry_count
            print(f"⚠️ Unexpected error: {e}. Retrying in {wait}s (Retry {retry_count + 1}/{max_retries})")
            time.sleep(wait)
            retry_count += 1

    # If all retries fail, return None and log failure
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
    # Build the path to the .env file, assuming it's two levels above this script
    env_path = Path(__file__).resolve().parents[2] / ".env"

    # Raise an error if the .env file does not exist
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}")

    # Load environment variables from the .env file
    load_dotenv(dotenv_path=env_path)

    # Retrieve Spotify credentials from environment variables
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    # Raise an error if any of the required credentials are missing
    if not all([client_id, client_secret, redirect_uri]):
        raise EnvironmentError("Missing one or more Spotify credentials in .env")

    # Return the credentials as a tuple
    return client_id, client_secret, redirect_uri


def connect_to_spotify() -> spotipy.Spotify:
    """Authenticate using Spotipy and return the client.

    Returns:
        spotipy.Spotify: Authenticated Spotify client.
    """
    # Load Spotify API credentials from the .env file
    client_id, client_secret, redirect_uri = load_credentials()

    # Define the required scopes for access to user and playlist data
    scope = "user-library-read user-read-private playlist-read-private"

    # Set up the Spotipy authentication manager
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,       # Force login dialog for clarity and session control
        cache_path=".spotify_cache"  # Cache token locally to avoid repeated login prompts
    )

    # Initialize the Spotipy client with the authenticated session
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Confirm connection by fetching and printing the user's display name
    user = sp.current_user()
    print(f"✅ Connected as: {user['display_name']}")

    return sp


# =====================
# === SPOTIFY FETCH ===
# =====================

def get_artist_id(sp: spotipy.Spotify, artist_name: str) -> Optional[str]:
    """Retrieve the Spotify artist ID for a given artist name.

    Args:
        sp (spotipy.Spotify): Authenticated Spotipy client.
        artist_name (str): Name of the artist to search for.

    Returns:
        Optional[str]: Spotify artist ID if found, else None.
    """
    # Perform a search query for the artist, using retry logic for robustness
    results = with_retry(sp.search, q=f"artist:{artist_name}", type="artist", limit=1)

    # Safely access the list of artist items in the response
    items = results.get("artists", {}).get("items", [])

    # Return the ID of the first artist found, or None if no match
    return items[0]["id"] if items else None


def get_artist_metadata(sp: spotipy.Spotify, artist_id: str) -> dict:
    """Retrieve full metadata for a given artist by Spotify ID.

    Args:
        sp (spotipy.Spotify): Authenticated Spotipy client.
        artist_id (str): Spotify ID of the artist.

    Returns:
        dict: Metadata dictionary returned by the Spotify API.
    """
    # Fetch artist metadata using the Spotify API, with retry logic for reliability
    return with_retry(sp.artist, artist_id)


def get_album_tracks(sp: spotipy.Spotify, album_id: str) -> List[dict]:
    """Retrieve all tracks from a given Spotify album.

    Args:
        sp (spotipy.Spotify): Authenticated Spotipy client.
        album_id (str): Spotify album ID.

    Returns:
        List[dict]: List of track objects from the album.
    """
    # Request the first page of tracks for the album
    results = with_retry(sp.album_tracks, album_id)

    # Initialize track list with items from the first response
    tracks = results['items']

    # If there are more pages of results, paginate through them
    while results.get('next'):
        # Fetch the next page using Spotify's pagination helper
        results = with_retry(sp.next, results)
        tracks.extend(results['items'])

    # Return the complete list of track dictionaries
    return tracks


def extract_track_metadata(sp: spotipy.Spotify, track_id: str) -> dict:
    """Extract selected metadata for a given Spotify track.

    Args:
        sp (spotipy.Spotify): Authenticated Spotipy client.
        track_id (str): Spotify track ID.

    Returns:
        dict: Dictionary containing relevant track metadata, or empty if failed.
    """
    try:
        # Request track metadata using retry logic for robustness
        track = with_retry(sp.track, track_id)

        # Safely extract and structure key metadata fields
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
        # Log any unexpected error and return an empty result
        print(f"⚠️ Error fetching metadata for track {track_id}: {e}")
        return {}


# =====================
# === DATA STORAGE ====
# =====================

def save_album_data(artist_name: str, album_name: str, track_data: List[dict]) -> None:
    """Save extracted track data for an album to a CSV file.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
        track_data (List[dict]): List of track metadata dictionaries.
    """
    # Build the output folder path using sanitized artist and album names
    folder = Path("raw/SPOTIFY") / get_artist_folder(artist_name) / sanitize(album_name)

    # Ensure the directory exists (create parent folders as needed)
    folder.mkdir(parents=True, exist_ok=True)

    # Convert the list of track metadata to a DataFrame
    df = pd.DataFrame(track_data)

    # Save the DataFrame to a CSV file in the album folder
    df.to_csv(folder / f"{sanitize(album_name)}.csv", index=False)

    # Confirm successful save to console
    print(f"✅ Saved: {folder / f'{sanitize(album_name)}.csv'}")


def save_artist_metadata(artist_name: str, metadata: dict) -> None:
    """Save artist metadata to a CSV file.

    Args:
        artist_name (str): Name of the artist.
        metadata (dict): Metadata dictionary for the artist.
    """
    # Build the output path using a sanitized artist folder name
    folder = Path("raw/SPOTIFY") / get_artist_folder(artist_name)

    # Ensure the directory exists
    folder.mkdir(parents=True, exist_ok=True)

    # Wrap the metadata dictionary in a list to create a single-row DataFrame
    df = pd.DataFrame([metadata])

    # Save the metadata to a CSV file named after the artist
    df.to_csv(folder / f"{get_artist_folder(artist_name)}_metadata.csv", index=False)

    # Confirm the metadata was saved successfully
    print(f"✅ Saved artist metadata: {folder / f'{get_artist_folder(artist_name)}_metadata.csv'}")


def save_album_metadata(artist_name: str, album_name: str, metadata: dict) -> None:
    """Save album metadata to a CSV file.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
        metadata (dict): Metadata dictionary for the album.
    """
    # Build the path to the album folder using sanitized artist and album names
    folder = Path("raw/SPOTIFY") / get_artist_folder(artist_name) / sanitize(album_name)

    # Ensure the album directory exists
    folder.mkdir(parents=True, exist_ok=True)

    # Create a single-row DataFrame from the metadata dictionary
    df = pd.DataFrame([metadata])

    # Save the DataFrame to a CSV file named after the album
    df.to_csv(folder / f"{sanitize(album_name)}_album_metadata.csv", index=False)

    # Confirm successful save to console
    print(f"✅ Saved album metadata: {folder / f'{sanitize(album_name)}_album_metadata.csv'}")


def album_fully_scraped(artist_name: str, album_name: str) -> bool:
    """Check whether all expected files for an album have been successfully scraped.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.

    Returns:
        bool: True if all related files exist, False otherwise.
    """
    # Define base path to the album folder
    base = Path("raw/SPOTIFY") / get_artist_folder(artist_name) / sanitize(album_name)

    # Check existence of:
    # 1. Track data CSV
    # 2. Album metadata CSV
    # 3. Artist metadata CSV (stored in the parent artist folder)
    return (
        (base / f"{sanitize(album_name)}.csv").exists() and
        (base / f"{sanitize(album_name)}_album_metadata.csv").exists() and
        (base.parent / f"{get_artist_folder(artist_name)}_metadata.csv").exists()
    )

# =====================
# === LOGGING FAILURES ===
# =====================

# In-memory log to store artist/album pairs that failed during processing
failed_album_log: List[tuple[str, str]] = []

def log_failed_album(artist_name: str, album_name: str) -> None:
    """Append a failed artist-album pair to the in-memory log.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
    """
    # Add the (artist, album) tuple to the global log list
    failed_album_log.append((artist_name, album_name))


def write_failed_log_to_file() -> None:
    """Persist the failed album log to a dated .log file in the 'logs/' directory."""
    # Skip if no failures have been recorded
    if not failed_album_log:
        return

    # Ensure the logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Build a log filename with the current date
    log_path = log_dir / f"failed_albums_{datetime.now().strftime('%Y-%m-%d')}.log"

    # Write each (artist, album) pair to the log file using a clear delimiter
    with open(log_path, "a", encoding="utf-8") as f:
        for artist, album in failed_album_log:
            f.write(f"{artist}|||{album}\n")

    # Confirm successful write
    print(f"📝 Failed albums logged to: {log_path}")


# =====================
# === MAIN SCRAPER ====
# =====================

def scrape_album(sp: spotipy.Spotify, artist_name: str, album_name: str, album_id: str) -> None:
    """Scrape metadata and tracks for a given album using the Spotify API.

    Args:
        sp (spotipy.Spotify): Authenticated Spotify client.
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
        album_id (str): Spotify album ID.
    """
    # Skip processing if all expected files already exist for this album
    if album_fully_scraped(artist_name, album_name):
        print(f"⏭️  Skipping '{album_name}' by {artist_name} (already scraped)")
        return

    try:
        # Fetch full album metadata from the Spotify API
        metadata = with_retry(sp.album, album_id)

        # Extract relevant fields and simplify the metadata structure
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

        # Save album-level metadata to CSV
        save_album_metadata(artist_name, album_name, simplified)

        # Fetch all tracks belonging to the album (including pagination)
        tracks = get_album_tracks(sp, album_id)

        # Short delay to avoid rapid-fire requests to track endpoints
        time.sleep(2)

        # Extract metadata for each track, skipping empty/null tracks
        track_data = [extract_track_metadata(sp, t["id"]) for t in tracks if t]

        # Delay scaled by number of requests to avoid hitting rate limits
        time.sleep(0.4 * len(track_data))

        # Save track-level data to CSV
        save_album_data(artist_name, album_name, track_data)

    except Exception as e:
        # Log and record the album if any part of the scraping process fails
        print(f"❌ Error processing '{album_name}': {e}")
        log_failed_album(artist_name, album_name)


def scrape_full_artist_interactive(sp: spotipy.Spotify, artist_name: str) -> None:
    """Scrape full artist data (metadata + all unique albums) from Spotify.

    Args:
        sp (spotipy.Spotify): Authenticated Spotify client.
        artist_name (str): Name of the artist to scrape.
    """
    # Retrieve the Spotify artist ID
    artist_id = get_artist_id(sp, artist_name)
    if not artist_id:
        print(f"❌ Artist not found: {artist_name}")
        return

    # Fetch full artist metadata and simplify it to key fields
    metadata = get_artist_metadata(sp, artist_id)
    simplified = {
        "Name": metadata.get("name"),
        "Genres": ", ".join(metadata.get("genres", [])),
        "Followers": metadata.get("followers", {}).get("total"),
        "Popularity": metadata.get("popularity"),
        "URI": metadata.get("uri")
    }

    # Save simplified artist metadata to CSV
    save_artist_metadata(artist_name, simplified)

    # Retrieve all albums (only those classified as "album", not singles or compilations)
    results = sp.artist_albums(artist_id, album_type="album")
    albums = results["items"]

    # Paginate through all album results if necessary
    while results.get("next"):
        results = with_retry(sp.next, results)
        albums.extend(results["items"])

    # Deduplicate albums by their lowercase name
    seen = set()
    unique = []
    for album in albums:
        name = album["name"].lower()
        if name not in seen:
            seen.add(name)
            unique.append(album)

    # Scrape each unique album
    for album in unique:
        scrape_album(sp, artist_name, album["name"], album["id"])


def scrape_single_album_interactive(sp: spotipy.Spotify, artist_name: str, album_name: str) -> None:
    """Search for a specific album by an artist and scrape its metadata and track info.

    Args:
        sp (spotipy.Spotify): Authenticated Spotify client.
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
    """
    # Search Spotify for the album using both album and artist name
    search = with_retry(
        sp.search,
        q=f"album:{album_name} artist:{artist_name}",
        type="album",
        limit=10
    )

    # Extract search results safely
    items = search.get("albums", {}).get("items", [])
    album_id = None

    # Attempt to match the album exactly by name and artist
    for item in items:
        album_matches = album_name.lower() == item["name"].strip().lower()
        artist_matches = artist_name.lower() in [a["name"].lower() for a in item["artists"]]
        if album_matches and artist_matches:
            album_id = item["id"]
            break

    # If no match was found, notify the user and log the failure
    if not album_id:
        print(f"❌ Album '{album_name}' not found for '{artist_name}'")
        log_failed_album(artist_name, album_name)
        return

    # Proceed to scrape album if a valid match was found
    scrape_album(sp, artist_name, album_name, album_id)


# =====================
# === CLI ENTRYPOINT ===
# =====================

def main() -> None:
    """Main interactive loop for scraping Spotify artist or album data."""
    print("\n🎧✨ Spotify Artist Scraper: Let's Get Those Tracks ✨🎧\n")

    # Authenticate and connect to Spotify
    sp = connect_to_spotify()

    while True:
        try:
            # Prompt user for artist name
            artist = input("🎤 Enter artist name (or 'exit'): ").strip()
            if artist.lower() == 'exit':
                break  # Exit the loop if user types 'exit'

            if not artist:
                print("⚠️ Enter a valid artist name.\n")
                continue

            # Prompt for scraping mode: full artist or single album
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
            # Handle unexpected errors, save log, and exit gracefully
            print(f"❌ Error: {e}")
            write_failed_log_to_file()
            sys.exit(1)

    # Write any failed albums to log at the end of the session
    write_failed_log_to_file()
    print("\n👋 Goodbye! 🎵")


if __name__ == "__main__":
    main()
