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

def load_failed_log():
    log_dir = Path(__file__).resolve().parents[0] / "logs"
    if not log_dir.exists():
        print("❌ No 'logs/' directory found.")
        sys.exit(1)

    log_files = sorted(log_dir.glob("failed_albums_*.log"), reverse=True)
    if not log_files:
        print("❌ No failed_albums_*.log files found.")
        sys.exit(1)

    latest_log = log_files[0]
    print(f"📂 Using latest log file: {latest_log.name}")

    with open(latest_log, "r", encoding="utf-8") as f:
        lines = f.readlines()

    failed_items = []
    for line in lines:
        if "|||" in line:
            artist, album = line.strip().split("|||")
            failed_items.append((artist, album))
    return failed_items


def main():
    print("\n🔁 Retry Mode: Spotify Scraper for Failed Albums\n")
    sp = connect_to_spotify()
    failed_albums = load_failed_log()

    for artist, album in failed_albums:
        print(f"🔄 Retrying: '{album}' by {artist}")
        try:
            scrape_single_album(sp, artist, album)
            print("-" * 60 + "\n")
        except Exception as e:
            print(f"❌ Still failed for '{album}' by {artist}: {e}\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    main()
