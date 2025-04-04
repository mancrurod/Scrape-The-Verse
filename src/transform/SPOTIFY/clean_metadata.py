import pandas as pd
from pathlib import Path

RAW_PATH = Path("raw/SPOTIFY")
OUTPUT_BASE = Path("transformations/SPOTIFY")

# Function to load CSV files
def load_csv(track_csv, album_metadata_csv):
    tracks = pd.read_csv(track_csv)
    album_metadata = pd.read_csv(album_metadata_csv)
    return tracks, album_metadata

# Function to merge CSV data
def merge_csv(tracks, album_metadata):
    merged_df = pd.merge(
        tracks,
        album_metadata,
        how="left",
        left_on="Album",
        right_on="Name",
        suffixes=("", "_album")
    )
    return merged_df

# Function to clean and reorder the DataFrame
def clean_df(df):
    cols_to_drop = [
        "Name_album", "Total Tracks", "Label", "Genres", 
        "Album Type", "URI", "Artists", "Release Date"
    ]
    df.drop(columns=cols_to_drop, inplace=True, errors="ignore")
    
    # Rename columns explicitly
    df.rename(columns={
        "Name": "SongName",
        "Popularity": "SongPopularity",
        "Popularity_album": "AlbumPopularity",
        "Album": "AlbumName",
        "Duration (ms)": "DurationMs",
        "Release Date_album": "ReleaseDateAlbum"
    }, inplace=True)

    # Format columns
    if "ReleaseDateAlbum" in df.columns:
        df["ReleaseDateAlbum"] = pd.to_datetime(df["ReleaseDateAlbum"], errors="coerce")
    if "SongPopularity" in df.columns:
        df["SongPopularity"] = pd.to_numeric(df["SongPopularity"], errors="coerce").fillna(0).astype(int)
    if "Explicit" in df.columns:
        df["Explicit"] = df["Explicit"].astype(bool)
    if "DurationMs" in df.columns:
        df["DurationMs"] = pd.to_numeric(df["DurationMs"], errors="coerce").fillna(0).astype(int)
    if "AlbumPopularity" in df.columns:
        df["AlbumPopularity"] = pd.to_numeric(df["AlbumPopularity"], errors="coerce").fillna(0).astype(int)

    # Ensure column order
    ordered_columns = [
        "SongName", "SongPopularity", "Explicit", "DurationMs",
        "AlbumName", "ReleaseDateAlbum", "AlbumPopularity"
    ]
    df = df[[col for col in ordered_columns if col in df.columns]]

    return df


# Function to execute the transformation for all albums
def run_transformation():
    for artist_dir in RAW_PATH.iterdir():
        if artist_dir.is_dir():
            for album_dir in artist_dir.iterdir():
                if album_dir.is_dir():
                    track_csv = album_dir / f"{album_dir.name}.csv"
                    album_metadata_csv = album_dir / f"{album_dir.name}_album_metadata.csv"

                    if track_csv.exists() and album_metadata_csv.exists():
                        tracks, album_metadata = load_csv(track_csv, album_metadata_csv)
                        merged_df = merge_csv(tracks, album_metadata)
                        cleaned_df = clean_df(merged_df)

                        output_dir = OUTPUT_BASE / artist_dir.name / album_dir.name
                        output_dir.mkdir(parents=True, exist_ok=True)
                        cleaned_df.to_csv(output_dir / f"{album_dir.name}_transformed.csv", index=False)

                        print(f"✅ Transformed file saved at: {output_dir}")