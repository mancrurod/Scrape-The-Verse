from pathlib import Path
from datetime import datetime

# List to store failed album logs
failed_album_log = []

def log_failed_album(artist_name, album_name):
    """
    Logs a failed album by appending the artist name and album name to the failed_album_log list.

    Args:
        artist_name (str): The name of the artist.
        album_name (str): The name of the album.
    """
    # Append the artist and album to the log
    failed_album_log.append((artist_name, album_name))

def write_failed_log_to_file():
    """
    Writes the failed album logs to a file in the 'logs' directory.
    Each log entry is saved in the format 'artist_name|||album_name'.
    If the log directory does not exist, it is created.

    Returns:
        None
    """
    # If there are no failed albums, exit the function
    if not failed_album_log:
        return

    # Define the log directory path (3 levels up from the current file)
    log_dir = Path(__file__).resolve().parents[3] / "logs"
    # Create the directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate a timestamp for the log file name
    timestamp = datetime.now().strftime("%Y-%m-%d")
    # Define the log file path
    log_path = log_dir / f"failed_albums_{timestamp}.log"

    # Write the failed albums to the log file
    with open(log_path, "a", encoding="utf-8") as f:
        for artist, album in failed_album_log:
            f.write(f"{artist}|||{album}\n")

    # Print a message indicating where the log was saved
    print(f"\n📝 Appended failed albums to: {log_path}")
