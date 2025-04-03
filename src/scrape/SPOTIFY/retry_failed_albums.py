# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
# 
#     python -m src.scraping.SPOTIFY.retry_failed_albums
# 
# DO NOT run it directly (e.g., `python retry_failed_albums.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

import sys
from pathlib import Path

from src.scraping.SPOTIFY.auth import connect_to_spotify
from src.scraping.SPOTIFY.albums import scrape_single_album

# Function to load the latest log file containing failed albums
def load_failed_log():
    # Define the directory where log files are stored
    log_dir = Path(__file__).resolve().parents[0] / "logs"
    
    # Check if the 'logs/' directory exists
    if not log_dir.exists():
        print("❌ No 'logs/' directory found.")
        sys.exit(1)

    # Get all log files matching the pattern 'failed_albums_*.log', sorted by date
    log_files = sorted(log_dir.glob("failed_albums_*.log"), reverse=True)
    
    # Exit if no log files are found
    if not log_files:
        print("❌ No failed_albums_*.log files found.")
        sys.exit(1)

    # Use the most recent log file
    latest_log = log_files[0]
    print(f"📂 Using latest log file: {latest_log.name}")

    # Read the log file and extract failed album entries
    with open(latest_log, "r", encoding="utf-8") as f:
        lines = f.readlines()

    failed_items = []
    for line in lines:
        # Parse lines containing artist and album separated by '|||'
        if "|||" in line:
            artist, album = line.strip().split("|||")
            failed_items.append((artist, album))
    return failed_items

# Main function to retry scraping failed albums
def main():
    print("\n🔁 Retry Mode: Spotify Scraper for Failed Albums\n")
    
    # Connect to the Spotify API
    sp = connect_to_spotify()
    
    # Load the list of failed albums from the log file
    failed_albums = load_failed_log()

    # Retry scraping each failed album
    for artist, album in failed_albums:
        print(f"🔄 Retrying: '{album}' by {artist}")
        try:
            # Attempt to scrape the album
            scrape_single_album(sp, artist, album)
            print("-" * 60 + "\n")
        except Exception as e:
            # Handle any errors during scraping
            print(f"❌ Still failed for '{album}' by {artist}: {e}\n" + "-" * 60 + "\n")

# Entry point of the script
if __name__ == "__main__":
    main()
