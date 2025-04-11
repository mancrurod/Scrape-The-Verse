import pandas as pd
from pathlib import Path
from typing import Tuple

# =======================
# === CONFIGURATION  ===
# =======================

# Path to the root directory where raw Spotify CSVs are stored
RAW_PATH = Path("raw/SPOTIFY")

# Path to the root directory where transformed CSVs will be saved
OUTPUT_BASE = Path("transformations/SPOTIFY")

# ==========================
# === TRANSFORMATION LOGIC ===
# ==========================

def load_csv(track_csv: Path, album_metadata_csv: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load track and album metadata from CSV files.

    Args:
        track_csv (Path): Path to the track-level CSV file.
        album_metadata_csv (Path): Path to the album-level CSV file.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: DataFrames for tracks and album metadata.
    """
    # Load the CSVs into pandas DataFrames
    return pd.read_csv(track_csv), pd.read_csv(album_metadata_csv)

def merge_csv(tracks: pd.DataFrame, album_metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Merge track-level and album-level metadata on album name.

    Args:
        tracks (pd.DataFrame): Track metadata.
        album_metadata (pd.DataFrame): Album metadata.

    Returns:
        pd.DataFrame: Combined dataset with album metadata merged into each track.
    """
    return pd.merge(
        tracks,
        album_metadata,
        how="left",           # Keep all tracks, even if some albums are missing metadata
        left_on="Album",      # Match using the 'Album' column from tracks
        right_on="Name",      # Match using the 'Name' column from album metadata
        suffixes=("", "_album")  # Avoid column name collisions by adding suffixes to album metadata
    )


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize merged track/album metadata.

    Args:
        df (pd.DataFrame): Raw merged dataset.

    Returns:
        pd.DataFrame: Final cleaned dataset with relevant fields.
    """
    # Drop unnecessary or redundant columns from the merged dataset
    df.drop(columns=[
        "Name_album",       # Duplicated from album metadata
        "Total Tracks",     # Not needed for track-level analysis
        "Label",            # Optional, often incomplete
        "Genres",           # Too broad for current scope
        "Album Type",       # Typically 'album', not analytically useful
        "URI",              # Internal Spotify URI
        "Artists",          # Often redundant or too nested
        "Release Date"      # Overridden by album's release date
    ], inplace=True, errors="ignore")

    # Rename key columns for clarity and consistency
    df.rename(columns={
        "Name": "SongName",
        "Popularity": "SongPopularity",
        "Popularity_album": "AlbumPopularity",
        "Album": "AlbumName",
        "Duration (ms)": "DurationMs",
        "Release Date_album": "ReleaseDateAlbum"
    }, inplace=True)

    # Convert album release date to datetime (if column exists)
    if "ReleaseDateAlbum" in df:
        df["ReleaseDateAlbum"] = pd.to_datetime(df["ReleaseDateAlbum"], errors="coerce")

    # Clean and convert song popularity to integer
    if "SongPopularity" in df:
        df["SongPopularity"] = pd.to_numeric(df["SongPopularity"], errors="coerce").fillna(0).astype(int)

    # Ensure explicit flag is boolean
    if "Explicit" in df:
        df["Explicit"] = df["Explicit"].astype(bool)

    # Clean and convert duration to integer (in milliseconds)
    if "DurationMs" in df:
        df["DurationMs"] = pd.to_numeric(df["DurationMs"], errors="coerce").fillna(0).astype(int)

    # Clean and convert album popularity to integer
    if "AlbumPopularity" in df:
        df["AlbumPopularity"] = pd.to_numeric(df["AlbumPopularity"], errors="coerce").fillna(0).astype(int)

    # Define the final column order and filter to include only available columns
    final_cols = [
        "SongName", "SongPopularity", "Explicit", "DurationMs",
        "AlbumName", "ReleaseDateAlbum", "AlbumPopularity", "ImageURL"
    ]

    return df[[col for col in final_cols if col in df.columns]]


# =====================
# === MAIN WRAPPER  ===
# =====================

def run_transformation_for_artist(artist_name: str) -> None:
    """
    Transform and clean Spotify CSVs for each album of a given artist.

    Args:
        artist_name (str): Name of the artist (used as folder name).
    """
    # Define the path to the artist's folder in the raw data directory
    artist_path = RAW_PATH / artist_name

    # Check if raw data exists for the artist
    if not artist_path.exists():
        print(f"❌ No raw data found for artist: {artist_name}")
        return

    # Iterate through each album directory under the artist folder
    for album_dir in artist_path.iterdir():
        if not album_dir.is_dir():
            continue  # Skip non-directory files

        # Define expected input file paths
        track_csv = album_dir / f"{album_dir.name}.csv"
        album_metadata_csv = album_dir / f"{album_dir.name}_album_metadata.csv"

        # Define the output path for the transformed CSV
        output_csv = OUTPUT_BASE / artist_name / album_dir.name / f"{album_dir.name}_transformed.csv"

        # Skip if transformation already exists
        if output_csv.exists():
            print(f"⏭️  Skipping '{album_dir.name}' by {artist_name} (already transformed)")
            continue

        # Proceed only if both required input files are present
        if track_csv.exists() and album_metadata_csv.exists():
            # Load input data
            tracks, album_metadata = load_csv(track_csv, album_metadata_csv)

            # Merge and clean the data
            merged_df = merge_csv(tracks, album_metadata)
            cleaned_df = clean_df(merged_df)

            # Ensure the output directory exists and save the cleaned file
            output_csv.parent.mkdir(parents=True, exist_ok=True)
            cleaned_df.to_csv(output_csv, index=False)

            print(f"✅ Transformed file saved at: {output_csv}")
        else:
            print(f"⚠️ Missing input files for: {album_dir.name}")


# =========================
# === CLI ENTRY POINT  ===
# =========================

def main() -> None:
    """
    CLI for batch transforming Spotify metadata files by artist.
    """
    print("\n🎛️ Spotify Metadata Transformer (multi-artist mode)\n")

    while True:
        # Prompt the user to enter an artist name or exit the tool
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()

        # Exit loop if user types 'exit'
        if artist.lower() == "exit":
            print("\n👋 Exiting transformer. See you next time!\n")
            break

        # Handle empty input
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        # Run transformation for the specified artist
        run_transformation_for_artist(artist)


if __name__ == "__main__":
    main()
