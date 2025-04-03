import pandas as pd
from pathlib import Path

# Define paths for raw input data and output transformations
RAW_PATH = Path("raw/SPOTIFY")
OUTPUT_BASE = Path("transformations/SPOTIFY")

# Function to load CSV files
def load_csv(track_csv, album_metadata_csv, artist_metadata_csv):
    """
    Load track, album metadata, and artist metadata CSV files into DataFrames.

    Args:
        track_csv (Path): Path to the track CSV file.
        album_metadata_csv (Path): Path to the album metadata CSV file.
        artist_metadata_csv (Path): Path to the artist metadata CSV file.

    Returns:
        tuple: DataFrames for tracks, album metadata, and artist metadata.
    """
    tracks = pd.read_csv(track_csv)  # Load track data
    album_metadata = pd.read_csv(album_metadata_csv)  # Load album metadata
    artist_metadata = pd.read_csv(artist_metadata_csv)  # Load artist metadata
    return tracks, album_metadata, artist_metadata

# Function to merge CSV data
def merge_csv(tracks, album_metadata, artist_metadata):
    """
    Merge track, album metadata, and artist metadata into a single DataFrame.

    Args:
        tracks (DataFrame): DataFrame containing track data.
        album_metadata (DataFrame): DataFrame containing album metadata.
        artist_metadata (DataFrame): DataFrame containing artist metadata.

    Returns:
        DataFrame: Merged DataFrame with additional artist metadata columns.
    """
    # Merge tracks with album metadata on album name
    merged_df = pd.merge(
        tracks,
        album_metadata,
        how="left",
        left_on="Album",
        right_on="Name",
        suffixes=("", "_album")
    )

    # Add artist metadata as additional columns
    artist_info = artist_metadata.iloc[0].drop("Name").to_dict()
    for key, value in artist_info.items():
        merged_df[key] = value

    return merged_df

# Function to clean the DataFrame
def clean_df(df):
    """
    Clean the merged DataFrame by dropping unnecessary columns and renaming them.

    Args:
        df (DataFrame): Merged DataFrame.

    Returns:
        DataFrame: Cleaned DataFrame.
    """
    # Columns to drop from the DataFrame
    cols_to_drop = [
        "Name_album", "Total Tracks", "Label", 
        "Genres", "Album Type", "URI", "Followers"
    ]
    df.drop(columns=cols_to_drop, inplace=True)  # Drop unnecessary columns

    # Rename columns to follow a consistent naming convention
    df.columns = [col.lower().replace(" ", "_").title().replace("_", "") for col in df.columns]

    return df

# Function to execute the transformation for all albums
def run_transformation():
    """
    Perform the transformation process for all albums in the raw data directory.
    This includes loading, merging, cleaning, and saving the transformed data.
    """
    # Iterate through each artist directory in the raw data path
    for artist_dir in RAW_PATH.iterdir():
        if artist_dir.is_dir():  # Check if it's a directory
            artist_metadata_csv = artist_dir / f"{artist_dir.name}_metadata.csv"

            # Iterate through each album directory for the artist
            for album_dir in artist_dir.iterdir():
                if album_dir.is_dir():  # Check if it's a directory
                    track_csv = album_dir / f"{album_dir.name}.csv"
                    album_metadata_csv = album_dir / f"{album_dir.name}_album_metadata.csv"

                    # Check if all required files exist
                    if track_csv.exists() and album_metadata_csv.exists() and artist_metadata_csv.exists():
                        # Load, merge, and clean the data
                        tracks, album_metadata, artist_metadata = load_csv(track_csv, album_metadata_csv, artist_metadata_csv)
                        merged_df = merge_csv(tracks, album_metadata, artist_metadata)
                        cleaned_df = clean_df(merged_df)

                        # Save the cleaned DataFrame to the output directory
                        output_dir = OUTPUT_BASE / artist_dir.name / album_dir.name
                        output_dir.mkdir(parents=True, exist_ok=True)
                        cleaned_df.to_csv(output_dir / f"{album_dir.name}_transformed.csv", index=False)

                        # Print success message
                        print(f"✅ Transformed file saved at: {output_dir}")