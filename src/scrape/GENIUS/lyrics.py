import time
from src.scraping.GENIUS.auth import get_genius_client  # Import function to authenticate and get Genius API client
from src.scraping.GENIUS.fetch import get_all_songs_from_album  # Import function to fetch all songs from an album
from src.scraping.GENIUS.storage import (  # Import functions for file storage and album summary handling
    get_album_path,
    save_lyrics_to_file,
    save_album_summary_csv
)
from src.scraping.GENIUS.logging import log_failed_lyrics  # Import function to log failed lyric fetch attempts

def download_album_lyrics(artist: str, album_name: str):
    """
    Downloads lyrics for all songs in a specified album by a given artist.

    Args:
        artist (str): Name of the artist.
        album_name (str): Name of the album.

    This function:
    - Authenticates with the Genius API.
    - Fetches all songs from the specified album.
    - Downloads lyrics for each song and saves them to text files.
    - Logs any errors or missing lyrics.
    - Generates a summary CSV file for the album.
    """
    genius = get_genius_client()  # Authenticate and get Genius API client
    clean_songs = get_all_songs_from_album(artist, album_name)  # Fetch all songs from the album

    if not clean_songs:  # Check if no songs were found
        print(f"❌ No songs found for album: {album_name}")
        return

    summary_rows = []  # Initialize list to store summary data
    album_path = get_album_path(artist, album_name)  # Get the file path for the album

    for track_number, song in clean_songs:  # Iterate through each song in the album
        file_path = album_path / f"{song}.txt"  # Define the file path for the song's lyrics

        if file_path.exists():  # Skip if lyrics file already exists
            print(f"⏭️  Skipping '{song}' (already downloaded)")
            summary_rows.append({
                "Track #": track_number,
                "Title": song,
                "Has Lyrics": "✅",
                "Genius URL": "Already saved"
            })
            continue

        print(f"🎶 {song}")  # Indicate the song being processed
        try:
            song_object = genius.search_song(song, artist)  # Search for the song on Genius
        except Exception as e:  # Handle any exceptions during the search
            print(f"⏱️ Error while fetching '{song}': {e}")
            song_object = None
            log_failed_lyrics(artist, album_name, song, str(e))  # Log the error
            continue

        has_lyrics = "✅" if song_object else "❌"  # Check if lyrics were found
        genius_url = song_object.url if song_object else "N/A"  # Get the Genius URL if available

        if song_object:  # If lyrics were found
            save_lyrics_to_file(file_path, song_object)  # Save lyrics to a text file
            print(f"✅ Saved: {file_path.name}")
        else:  # If no lyrics were found
            print(f"❌ No lyrics found for: {song}")
            log_failed_lyrics(artist, album_name, song, "No lyrics found")  # Log the failure

        # Append song details to the summary
        summary_rows.append({
            "Track #": track_number,
            "Title": song,
            "Has Lyrics": has_lyrics,
            "Genius URL": genius_url
        })

        time.sleep(1)  # Pause to avoid hitting API rate limits

    # Save the album summary as a CSV file
    save_album_summary_csv(album_path, album_name, summary_rows)
