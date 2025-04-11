import pandas as pd
from pathlib import Path
from typing import List

# =======================
# === MERGING FUNCTION ===
# =======================

def merge_artist_metadata(spotify_csv_path: str, wikidata_csv_path: str, output_path: str) -> None:
    """
    Merge and standardize artist metadata from Spotify and Wikidata CSVs.

    Args:
        spotify_csv_path (str): Path to the Spotify metadata CSV.
        wikidata_csv_path (str): Path to the Wikidata metadata CSV.
        output_path (str): Output file path for the merged CSV.
    """
    spotify_df = pd.read_csv(spotify_csv_path)
    wikidata_df = pd.read_csv(wikidata_csv_path)

    # Drop URI if it exists
    spotify_df.drop(columns=["URI"], errors="ignore", inplace=True)

    # Rename genre columns to avoid collision
    spotify_df.rename(columns={"Genres": "GenresSpotify"}, inplace=True)
    wikidata_df.rename(columns={"Genres": "GenresWikidata"}, inplace=True)

    # Concatenate both sources horizontally
    merged_df = pd.concat([spotify_df, wikidata_df], axis=1)

    # Format birth date
    if "DateOfBirth" in merged_df:
        merged_df["DateOfBirth"] = pd.to_datetime(
            merged_df["DateOfBirth"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Convert numeric values safely
    for col in ["Followers", "Popularity"]:
        if col in merged_df:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0).astype(int)

    # Filter for relevant fields only
    desired_columns: List[str] = [
        "Name", "BirthName", "DateOfBirth", "PlaceOfBirth", "CountryOfCitizenship",
        "WorkPeriodStart", "GenresWikidata", "GenresSpotify", "Instruments",
        "VoiceType", "Popularity", "Followers", "ImageURL"
    ]

    columns_available = [col for col in desired_columns if col in merged_df.columns]
    merged_df = merged_df[columns_available]

    # Save result
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_file, index=False)
    print(f"✅ Merged metadata saved to: {output_file}")

# ==========================
# === CLI ENTRY POINT  ====
# ==========================

def main() -> None:
    """
    CLI for merging artist metadata from Spotify and Wikidata.
    Prompts user to enter artist name, then merges and saves metadata to transformations folder.
    """
    print("\n🧬 Wikidata + Spotify Metadata Merger\n")

    while True:
        # Prompt the user to enter an artist name or exit
        artist_name = input("🎤 Enter the artist name (or type 'exit' to quit): ").strip()

        if artist_name.lower() == "exit":
            print("\n👋 Exiting metadata merger. See you next time!\n")
            break

        if not artist_name:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        # Define paths to input and output CSVs
        spotify_csv = f"raw/SPOTIFY/{artist_name}/{artist_name}_metadata.csv"
        wikidata_csv = f"raw/WIKIDATA/{artist_name}/wikidata_summary.csv"
        output_csv = f"transformations/SPOTIFY/{artist_name}/{artist_name}_merged_metadata.csv"

        try:
            # Attempt to merge the artist metadata
            merge_artist_metadata(spotify_csv, wikidata_csv, output_csv)
        except Exception as e:
            # Log any errors during the merge process
            print(f"❌ Error merging metadata for {artist_name}: {e}\n")


if __name__ == "__main__":
    main()
