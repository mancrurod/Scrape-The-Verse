# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
# 
#     python -m src.scraping.GENIUS.main_genius_scrap
# 
# DO NOT run it directly (e.g., `python main_genius_scrap.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.scraping.GENIUS.lyrics import download_album_lyrics  # Import function to download lyrics for an album
from src.scraping.GENIUS.logging import log_failed_lyrics  # Import function to log failed lyric downloads

def main():
    """
    Main function to scrape lyrics for a batch of albums by various artists.
    Iterates through a predefined dictionary of artists and their albums,
    downloads lyrics for each album, and logs any failures.
    """
    print("\n🎤✨ Genius Lyrics Scraper: Batch Mode Activated ✨🎤\n")

    # Dictionary containing artists and their respective albums
    artist_albums = {
        "Taylor Swift": [
            "Taylor Swift", "Fearless", "Speak Now", "Red", "1989", "reputation", "Lover",
            "folklore", "evermore", "Fearless (Taylor’s Version)", "Red (Taylor’s Version)",
            "Midnights", "Speak Now (Taylor’s Version)", "1989 (Taylor’s Version)",
            "THE TORTURED POETS DEPARTMENT: THE ANTHOLOGY"
        ],
        "Bob Dylan": [
            "Bob Dylan", "The Freewheelin' Bob Dylan", "The Times They Are A-Changin'",
            "Another Side of Bob Dylan", "Bringing It All Back Home", "Highway 61 Revisited",
            "Blonde on Blonde", "John Wesley Harding", "Nashville Skyline", "Self Portrait",
            "New Morning", "Pat Garrett & Billy the Kid", "Dylan (1973)", "Planet Waves",
            "Before the Flood", "Blood on the Tracks", "Desire", "Street-Legal",
            "Slow Train Coming", "Saved", "Shot of Love", "Infidels", "Empire Burlesque",
            "Knocked Out Loaded", "Down in the Groove", "Oh Mercy", "Under the Red Sky",
            "Good as I Been to You", "World Gone Wrong", "Time Out of Mind", "Love and Theft",
            "Modern Times", "Together Through Life", "Christmas in the Heart", "Tempest",
            "Shadows in the Night", "Fallen Angels", "Triplicate", "Rough and Rowdy Ways",
            "Shadow Kingdom"
        ]
    }

    # Iterate through each artist and their albums
    for artist, albums in artist_albums.items():
        print(f"🎼 Artist: {artist}")
        for album in albums:
            print(f"   📀 Album: {album}")
            print("   ⏳ Downloading lyrics...\n")
            try:
                # Attempt to download lyrics for the current album
                download_album_lyrics(artist, album)
                print(f"   ✅ Finished downloading: '{album}' by {artist}\n" + "-" * 60 + "\n")
            except Exception as e:
                # Log any errors encountered during the download
                print(f"   ❌ Error for '{album}' by {artist}: {e}\n" + "-" * 60 + "\n")
                log_failed_lyrics(artist, album, "N/A", str(e))

    # Print completion message
    print("✅ Finished batch scrape! Check logs for any failed lyrics.\n")


if __name__ == "__main__":
    # Entry point of the script
    main()
