import pandas as pd
from pathlib import Path
from src.scraping.SPOTIFY.utils import sanitize, get_artist_folder

def save_album_data(artist_name, album_name, track_data):
    """
    Saves track data of an album to a CSV file.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
        track_data (list of dict): List of track data dictionaries.
    """
    # Define the base path for saving raw data
    base_path = Path(__file__).resolve().parents[3] / "raw"
    # Get sanitized artist folder name
    artist_folder = get_artist_folder(artist_name)
    # Sanitize album name for folder creation
    album_folder = sanitize(album_name)
    # Construct the full path for the album folder
    full_path = base_path / "SPOTIFY" / artist_folder / album_folder
    # Create the directory if it doesn't exist
    full_path.mkdir(parents=True, exist_ok=True)

    # Convert track data to a DataFrame and save as CSV
    df = pd.DataFrame(track_data)
    csv_path = full_path / f"{album_folder}.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")

def save_artist_metadata(artist_name, artist_metadata):
    """
    Saves artist metadata to a CSV file.

    Args:
        artist_name (str): Name of the artist.
        artist_metadata (dict): Metadata of the artist.
    """
    # Define the base path for saving raw data
    base_path = Path(__file__).resolve().parents[3] / "raw"
    # Get sanitized artist folder name
    artist_folder = get_artist_folder(artist_name)
    # Construct the full path for the artist folder
    full_path = base_path / "SPOTIFY" / artist_folder
    # Create the directory if it doesn't exist
    full_path.mkdir(parents=True, exist_ok=True)

    # Convert artist metadata to a DataFrame and save as CSV
    df = pd.DataFrame([artist_metadata])
    csv_path = full_path / f"{artist_folder}_metadata.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved artist metadata: {csv_path}")

def save_album_metadata(artist_name, album_name, album_metadata):
    """
    Saves album metadata to a CSV file.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
        album_metadata (dict): Metadata of the album.
    """
    # Define the base path for saving raw data
    base_path = Path(__file__).resolve().parents[3] / "raw"
    # Get sanitized artist folder name
    artist_folder = get_artist_folder(artist_name)
    # Sanitize album name for folder creation
    album_folder = sanitize(album_name)
    # Construct the full path for the album folder
    full_path = base_path / "SPOTIFY" / artist_folder / album_folder
    # Create the directory if it doesn't exist
    full_path.mkdir(parents=True, exist_ok=True)

    # Convert album metadata to a DataFrame and save as CSV
    df = pd.DataFrame([album_metadata])
    csv_path = full_path / f"{album_folder}_album_metadata.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved album metadata: {csv_path}")

def album_already_scraped(artist_name, album_name):
    """
    Checks if the album's track data has already been scraped.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.

    Returns:
        bool: True if the album's track data CSV exists, False otherwise.
    """
    # Define the base path for checking raw data
    base_path = Path(__file__).resolve().parents[3] / "raw"
    # Get sanitized artist folder name
    artist_folder = get_artist_folder(artist_name)
    # Sanitize album name for folder creation
    album_folder = sanitize(album_name)
    # Construct the path to the album's track data CSV
    album_path = base_path / "SPOTIFY" / artist_folder / album_folder
    csv_filename = f"{album_folder}.csv"
    return (album_path / csv_filename).exists()

def album_fully_scraped(artist_name, album_name):
    """
    Checks if the album has been fully scraped (metadata and track data).

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.

    Returns:
        bool: True if all required files (artist metadata, album metadata, and track data) exist, False otherwise.
    """
    # Define the base path for checking raw data
    base_path = Path(__file__).resolve().parents[3] / "raw"
    # Get sanitized artist folder name
    artist_folder = get_artist_folder(artist_name)
    # Sanitize album name for folder creation
    album_folder = sanitize(album_name)

    # Construct paths to the required files
    album_dir = base_path / "SPOTIFY" / artist_folder / album_folder
    artist_metadata_path = base_path / "SPOTIFY" / artist_folder / f"{artist_folder}_metadata.csv"
    album_metadata_path = album_dir / f"{album_folder}_album_metadata.csv"
    album_tracks_path = album_dir / f"{album_folder}.csv"

    # Check if all required files exist
    return (
        artist_metadata_path.exists() and
        album_metadata_path.exists() and
        album_tracks_path.exists()
    )
