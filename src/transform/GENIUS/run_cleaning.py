# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.transform.GENIUS.run_cleaning
#
# DO NOT run it directly (e.g., `python run_cleaning.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.transform.GENIUS.clean_lyrics import clean_lyrics_folder_recursive


def main():
    clean_lyrics_folder_recursive(
        input_base="raw/GENIUS/Taylor Swift",
        output_base="transformations/GENIUS/Taylor Swift"
    )


if __name__ == "__main__":
    main()
