# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.transform.WIKIDATA.run_merging
#
# DO NOT run it directly (e.g., `python run_merging.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.transform.WIKIDATA.merge_artist_metadata import merge_artist_metadata


def main():
    artist_name = input("Enter the artist name (e.g., Bob Dylan): ").strip()

    spotify_csv = f"raw/SPOTIFY/{artist_name}/{artist_name}_metadata.csv"
    wikidata_csv = f"raw/WIKIDATA/{artist_name}/wikidata_summary.csv"
    output_csv = f"transformations/SPOTIFY/{artist_name}/{artist_name}_merged_metadata.csv"

    merge_artist_metadata(spotify_csv, wikidata_csv, output_csv)


if __name__ == "__main__":
    main()
