import pandas as pd
from pathlib import Path
from typing import Tuple

# =======================
# === CONFIGURATION  ===
# =======================

RAW_PATH = Path("raw/SPOTIFY")
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
        how="left",
        left_on="Album",
        right_on="Name",
        suffixes=("", "_album")
    )

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize merged track/album metadata.

    Args:
        df (pd.DataFrame): Raw merged dataset.

    Returns:
        pd.DataFrame: Final cleaned dataset with relevant fields.
    """
    df.drop(columns=[
        "Name_album", "Total Tracks", "Label", "Genres",
        "Album Type", "URI", "Artists", "Release Date"
    ], inplace=True, errors="ignore")

    df.rename(columns={
        "Name": "SongName",
        "Popularity": "SongPopularity",
        "Popularity_album": "AlbumPopularity",
        "Album": "AlbumName",
        "Duration (ms)": "DurationMs",
        "Release Date_album": "ReleaseDateAlbum"
    }, inplace=True)

    if "ReleaseDateAlbum" in df:
        df["ReleaseDateAlbum"] = pd.to_datetime(df["ReleaseDateAlbum"], errors="coerce")

    if "SongPopularity" in df:
        df["SongPopularity"] = pd.to_numeric(df["SongPopularity"], errors="coerce").fillna(0).astype(int)

    if "Explicit" in df:
        df["Explicit"] = df["Explicit"].astype(bool)

    if "DurationMs" in df:
        df["DurationMs"] = pd.to_numeric(df["DurationMs"], errors="coerce").fillna(0).astype(int)

    if "AlbumPopularity" in df:
        df["AlbumPopularity"] = pd.to_numeric(df["AlbumPopularity"], errors="coerce").fillna(0).astype(int)

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
    artist_path = RAW_PATH / artist_name
    if not artist_path.exists():
        print(f"❌ No raw data found for artist: {artist_name}")
        return

    for album_dir in artist_path.iterdir():
        if not album_dir.is_dir():
            continue

        track_csv = album_dir / f"{album_dir.name}.csv"
        album_metadata_csv = album_dir / f"{album_dir.name}_album_metadata.csv"
        output_csv = OUTPUT_BASE / artist_name / album_dir.name / f"{album_dir.name}_transformed.csv"

        if output_csv.exists():
            print(f"⏭️  Skipping '{album_dir.name}' by {artist_name} (already transformed)")
            continue

        if track_csv.exists() and album_metadata_csv.exists():
            tracks, album_metadata = load_csv(track_csv, album_metadata_csv)
            merged_df = merge_csv(tracks, album_metadata)
            cleaned_df = clean_df(merged_df)

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
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting transformer. See you next time!\n")
            break
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        run_transformation_for_artist(artist)

if __name__ == "__main__":
    main()
