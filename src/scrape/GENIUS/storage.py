from csv import DictWriter
from pathlib import Path
from src.scrape.GENIUS.utils import sanitize, get_artist_folder

def get_album_path(artist_name: str, album_name: str) -> Path:
    """
    Creates and returns the path to the album folder for a given artist and album name.

    Args:
        artist_name (str): The name of the artist.
        album_name (str): The name of the album.

    Returns:
        Path: The path to the album folder.
    """
    from pathlib import Path
    base_path = Path.cwd() / "raw" / "GENIUS"  # Base directory for storing album data
    artist_folder = get_artist_folder(artist_name)  # Get sanitized artist folder name
    album_folder = sanitize(album_name)  # Sanitize album name for folder creation
    album_path = base_path / artist_folder / album_folder
    album_path.mkdir(parents=True, exist_ok=True)  # Create the folder if it doesn't exist
    return album_path

def save_lyrics_to_file(file_path: Path, song_object):
    """
    Saves the lyrics of a song to a text file.

    Args:
        file_path (Path): The path to the file where lyrics will be saved.
        song_object: An object representing the song, which has a `save_lyrics` method.
    """
    # Save the song lyrics to the specified file
    song_object.save_lyrics(filename=str(file_path), extension="txt", sanitize=False, overwrite=False)

def save_album_summary_csv(album_path: Path, album_name: str, summary_rows: list):
    """
    Saves a CSV summary of an album's tracks.

    Args:
        album_path (Path): The path to the album folder.
        album_name (str): The name of the album.
        summary_rows (list): A list of dictionaries containing track summary data.

    Each dictionary in `summary_rows` should have the following keys:
        - "Track #": The track number.
        - "Title": The title of the track.
        - "Has Lyrics": Whether the track has lyrics (True/False).
        - "Genius URL": The Genius URL for the track.
    """
    csv_name = f"{sanitize(album_name)}.csv"  # Sanitize album name for CSV file
    csv_path = album_path / csv_name

    # Write the summary rows to the CSV file
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = DictWriter(f, fieldnames=["Track #", "Title", "Has Lyrics", "Genius URL"])
        writer.writeheader()  # Write the header row
        writer.writerows(summary_rows)  # Write the track summary rows

    print(f"📄 CSV summary saved: {csv_path.name}")  # Notify user of saved CSV
