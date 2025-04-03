# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.transform.GENIUS.run_cleaning
#
# DO NOT run it directly (e.g., `python run_cleaning.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from pathlib import Path
from src.transform.GENIUS.clean_lyrics import clean_lyrics_folder_recursive


def main():
    input_base = Path("raw/GENIUS")
    output_base = Path("transformations/GENIUS")

    for artist_folder in input_base.iterdir():
        if artist_folder.is_dir():
            artist_output_folder = output_base / artist_folder.name
            clean_lyrics_folder_recursive(
                input_base=str(artist_folder),
                output_base=str(artist_output_folder)
            )


if __name__ == "__main__":
    main()
