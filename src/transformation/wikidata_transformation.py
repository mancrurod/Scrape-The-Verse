import pandas as pd
from pathlib import Path

def merge_artist_metadata(spotify_csv_path: str, wikidata_csv_path: str, output_path: str):
    """
    Merge artist metadata from Spotify and Wikidata sources, clean and standardize the result,
    and save it as a CSV file inside the SPOTIFY artist transformation folder.

    Args:
        spotify_csv_path (str): Path to the Spotify metadata CSV file.
        wikidata_csv_path (str): Path to the Wikidata metadata CSV file.
        output_path (str): Destination path to save the merged metadata CSV.
    """
    # Load both metadata CSVs into DataFrames
    spotify_df = pd.read_csv(spotify_csv_path)
    wikidata_df = pd.read_csv(wikidata_csv_path)

    # Remove 'URI' column from Spotify data if it exists
    spotify_df = spotify_df.drop(columns=["URI"], errors="ignore")

    # Rename 'Genres' columns to differentiate their origin
    spotify_df = spotify_df.rename(columns={"Genres": "GenresSpotify"})
    wikidata_df = wikidata_df.rename(columns={"Genres": "GenresWikidata"})

    # Concatenate both DataFrames horizontally (assuming one row per source)
    merged_df = pd.concat([spotify_df, wikidata_df], axis=1)

    # Standardize 'DateOfBirth' format to YYYY-MM-DD
    if "DateOfBirth" in merged_df.columns:
        merged_df["DateOfBirth"] = pd.to_datetime(
            merged_df["DateOfBirth"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Convert numeric columns to integers, filling missing values with 0
    for col in ["Followers", "Popularity"]:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0).astype(int)

    # Define desired column order for output CSV
    desired_columns = [
        "Name",
        "BirthName",
        "DateOfBirth",
        "PlaceOfBirth",
        "CountryOfCitizenship",
        "WorkPeriodStart",
        "GenresWikidata",
        "GenresSpotify",
        "Instruments",
        "VoiceType",
        "Popularity",
        "Followers"
    ]

    # Keep only columns that are present in the merged data
    columns_available = [col for col in desired_columns if col in merged_df.columns]
    merged_df = merged_df[columns_available]

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save cleaned and merged data to CSV
    merged_df.to_csv(output_path, index=False)
    print(f"✅ Merged metadata saved to: {output_path}")


def main():
    """
    Command-line interface for merging metadata.
    Prompts user for an artist name and merges Spotify and Wikidata metadata for that artist.
    """
    print("\n🧬 Wikidata + Spotify Metadata Merger\n")

    while True:
        # Prompt user for artist name
        artist_name = input("🎤 Enter the artist name (or type 'exit' to quit): ").strip()
        if artist_name.lower() == "exit":
            print("\n👋 Exiting metadata merger. See you next time!\n")
            break
        if not artist_name:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        # Define paths for input/output
        output_csv = f"transformations/SPOTIFY/{artist_name}/{artist_name}_merged_metadata.csv"
        spotify_csv = f"raw/SPOTIFY/{artist_name}/{artist_name}_metadata.csv"
        wikidata_csv = f"raw/WIKIDATA/{artist_name}/wikidata_summary.csv"

        # Attempt to merge metadata
        try:
            merge_artist_metadata(spotify_csv, wikidata_csv, output_csv)
        except Exception as e:
            print(f"❌ Error merging metadata for {artist_name}: {e}\n")


if __name__ == "__main__":
    main()
