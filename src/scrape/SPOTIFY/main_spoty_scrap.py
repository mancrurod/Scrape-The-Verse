# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
# 
#     python -m src.scrape.SPOTIFY.main_spoty_scrap
# 
# DO NOT run it directly (e.g., `python main_spoty_scrap.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

import sys
from src.scrape.SPOTIFY.auth import connect_to_spotify  # Import function to authenticate with Spotify API
from src.scrape.SPOTIFY.artist import scrape_full_artist  # Import function to scrape all data for an artist
from src.scrape.SPOTIFY.albums import scrape_single_album  # Import function to scrape data for a single album

def main():
    """
    Main function to run the Spotify scraping script.
    It allows the user to interactively choose between scraping an artist's full metadata
    or scraping metadata for a specific album.
    """
    print("\n🎧✨ Spotify Artist Scraper: Let's Get Those Tracks ✨🎧\n")

    # Authenticate with Spotify API
    sp = connect_to_spotify()

    while True:
        try:
            # Prompt user for the artist's name
            artist_name = input("🎤 Enter the artist's name (or type 'exit' to quit): ").strip()
            if artist_name.lower() == 'exit':  # Exit condition
                print("\n👋 See you next time. Stay groovy! 🎵\n")
                break

            if not artist_name:  # Handle empty input
                print("⚠️  Please enter a valid artist name.\n")
                continue

            print(f"\n🔍 Searching Spotify for: '{artist_name}'...")
            print("   ⏳ Scraping metadata...\n")

            # Prompt user to choose scraping mode
            mode = input("🎯 Choose mode: (A) Full artist or (B) Single album [A/B]: ").strip().upper()
            if mode == 'A':  # Full artist scraping mode
                scrape_full_artist(sp, artist_name)  # Call function to scrape full artist data
                print(f"   ✅ Done scraping: '{artist_name}'\n" + "-" * 60 + "\n")
            elif mode == 'B':  # Single album scraping mode
                # Prompt user for album name
                album_name = input("💿 Enter the album name: ").strip()
                if album_name:
                    scrape_single_album(sp, artist_name, album_name)  # Call function to scrape album data
                    print(f"   ✅ Done scraping album: '{album_name}' by '{artist_name}'\n" + "-" * 60 + "\n")
                else:  # Handle empty album name input
                    print("⚠️  Please enter a valid album name.\n")
            else:  # Handle invalid mode input
                print("⚠️  Invalid option. Please enter A or B.\n")

        except Exception as e:
            # Handle unexpected errors and exit the script
            print(f"\n❌ An error occurred while processing '{artist_name}': {e}\n")
            sys.exit(1)

# Entry point of the script
if __name__ == "__main__":
    main()
