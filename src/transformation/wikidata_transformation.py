import pandas as pd
from pathlib import Path

def merge_artist_metadata(spotify_csv_path: str, wikidata_csv_path: str, output_path: str):
    """
    Merge Spotify and Wikidata artist metadata, clean and rename columns, rearrange, and save to CSV inside SPOTIFY's artist folder.

    Args:
        spotify_csv_path (str): Path to Spotify metadata CSV.
        wikidata_csv_path (str): Path to Wikidata metadata CSV.
        output_path (str): Path to save the merged output CSV.
    """
    # Load input data
    spotify_df = pd.read_csv(spotify_csv_path)
    wikidata_df = pd.read_csv(wikidata_csv_path)

    # Keep 'Name', drop 'URI'
    spotify_df = spotify_df.drop(columns=["URI"], errors="ignore")

    # Rename genres column
    spotify_df = spotify_df.rename(columns={"Genres": "GenresSpotify"})
    wikidata_df = wikidata_df.rename(columns={"Genres": "GenresWikidata"})

    # Merge
    merged_df = pd.concat([spotify_df, wikidata_df], axis=1)

    # Format DateOfBirth as yyyy-mm-dd
    if "DateOfBirth" in merged_df.columns:
        merged_df["DateOfBirth"] = pd.to_datetime(
            merged_df["DateOfBirth"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Convert Followers and Popularity to numeric
    for col in ["Followers", "Popularity"]:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0).astype(int)

    # Desired column order
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

    # Reorder, keeping only available columns
    columns_available = [col for col in desired_columns if col in merged_df.columns]
    merged_df = merged_df[columns_available]

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    merged_df.to_csv(output_path, index=False)
    print(f"✅ Merged metadata saved to: {output_path}")


def main():
    print("\n🧬 Wikidata + Spotify Metadata Merger\n")

    while True:
        artist_name = input("🎤 Enter the artist name (or type 'exit' to quit): ").strip()
        if artist_name.lower() == "exit":
            print("\n👋 Exiting metadata merger. See you next time!\n")
            break
        if not artist_name:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        output_csv = f"transformations/SPOTIFY/{artist_name}/{artist_name}_merged_metadata.csv"
        spotify_csv = f"raw/SPOTIFY/{artist_name}/{artist_name}_metadata.csv"
        wikidata_csv = f"raw/WIKIDATA/{artist_name}/wikidata_summary.csv"

        try:
            merge_artist_metadata(spotify_csv, wikidata_csv, output_csv)
        except Exception as e:
            print(f"❌ Error merging metadata for {artist_name}: {e}\n")


if __name__ == "__main__":
    main()
