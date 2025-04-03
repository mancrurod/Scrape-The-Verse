# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
# 
#     python -m src.scraping.SPOTIFY.main_spoty_scrap
# 
# DO NOT run it directly (e.g., `python main_spoty_scrap.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

import sys
from src.scraping.SPOTIFY.auth import connect_to_spotify
from src.scraping.SPOTIFY.artist import scrape_full_artist
from src.scraping.SPOTIFY.albums import scrape_single_album

def main():
    print("\n🎧✨ Spotify Artist Scraper: Let's Get Those Tracks ✨🎧\n")

    sp = connect_to_spotify()

    while True:
        try:
            artist_name = input("🎤 Enter the artist's name (or type 'exit' to quit): ").strip()
            if artist_name.lower() == 'exit':
                print("\n👋 See you next time. Stay groovy! 🎵\n")
                break

            if not artist_name:
                print("⚠️  Please enter a valid artist name.\n")
                continue

            print(f"\n🔍 Searching Spotify for: '{artist_name}'...")
            print("   ⏳ Scraping metadata...\n")

            mode = input("🎯 Choose mode: (A) Full artist or (B) Single album [A/B]: ").strip().upper()
            if mode == 'A':
                scrape_full_artist(sp, artist_name)
                print(f"   ✅ Done scraping: '{artist_name}'\n" + "-" * 60 + "\n")
            elif mode == 'B':
                album_name = input("💿 Enter the album name: ").strip()
                if album_name:
                    scrape_single_album(sp, artist_name, album_name)
                    print(f"   ✅ Done scraping album: '{album_name}' by '{artist_name}'\n" + "-" * 60 + "\n")
                else:
                    print("⚠️  Please enter a valid album name.\n")
            else:
                print("⚠️  Invalid option. Please enter A or B.\n")

        except Exception as e:
            print(f"\n❌ An error occurred while processing '{artist_name}': {e}\n")
            sys.exit(1)

if __name__ == "__main__":
    main()
