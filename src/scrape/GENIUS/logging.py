from pathlib import Path
from datetime import datetime

# Define the path for the logs directory
FAILED_LOG_PATH = Path.cwd() / "logs"
# Create the logs directory if it doesn't exist
FAILED_LOG_PATH.mkdir(parents=True, exist_ok=True)

def log_failed_lyrics(artist: str, album: str, song_title: str, reason: str):
    """
    Logs information about failed attempts to retrieve song lyrics.

    Args:
        artist (str): The name of the artist.
        album (str): The name of the album.
        song_title (str): The title of the song.
        reason (str): The reason why the lyrics retrieval failed.

    This function creates a log entry with the provided details, including a timestamp,
    and appends it to a log file named based on the current date. The log file is stored
    in the 'logs' directory.
    """
    # Get the current timestamp in a readable format
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Define the log file name based on the current date
    log_file = FAILED_LOG_PATH / f"failed_lyrics_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Append the log entry to the log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Artist: {artist} | Album: {album} | Song: {song_title} | Reason: {reason}\n")
