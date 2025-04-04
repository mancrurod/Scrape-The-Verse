# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.processing.run_cleaning
#
# DO NOT run it directly (e.g., `python run_cleaning.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.processing.join_lyrics_and_metadata import join_album
from pathlib import Path
from datetime import datetime

def main():
    artist_root = Path("transformations/GENIUS")
    logs = []
    successes = []

    for artist_dir in artist_root.iterdir():
        if artist_dir.is_dir():
            artist = artist_dir.name
            for album_dir in artist_dir.iterdir():
                if album_dir.is_dir():
                    album = album_dir.name
                    print(f"\n🎧 Processing {artist} - {album}")
                    join_album(artist, album, logs, successes)

    print("\n📊 SUMMARY")
    print(f"✅ Successful albums: {len(successes)}")
    print(f"❌ Failed albums: {len(logs)}")

    if logs:
        log_path = Path("logs") / f"failed_merging_lyrics_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))
        print(f"🧾 Logged errors to {log_path}")

if __name__ == "__main__":
    main()
