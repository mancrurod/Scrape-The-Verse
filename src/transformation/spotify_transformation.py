import pandas as pd
from pathlib import Path

RAW_PATH = Path("raw/SPOTIFY")
OUTPUT_BASE = Path("transformations/SPOTIFY")

def load_csv(track_csv, album_metadata_csv):
    tracks = pd.read_csv(track_csv)
    album_metadata = pd.read_csv(album_metadata_csv)
    return tracks, album_metadata

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

def clean_df(df):
    cols_to_drop = [
        "Name_album", "Total Tracks", "Label", "Genres", 
        "Album Type", "URI", "Artists", "Release Date"
    ]
    df.drop(columns=cols_to_drop, inplace=True, errors="ignore")

    df.rename(columns={
        "Name": "SongName",
        "Popularity": "SongPopularity",
        "Popularity_album": "AlbumPopularity",
        "Album": "AlbumName",
        "Duration (ms)": "DurationMs",
        "Release Date_album": "ReleaseDateAlbum"
    }, inplace=True)

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

    ordered_columns = [
        "SongName", "SongPopularity", "Explicit", "DurationMs",
        "AlbumName", "ReleaseDateAlbum", "AlbumPopularity"
    ]
    df = df[[col for col in ordered_columns if col in df.columns]]

    return df

def run_transformation_for_artist(artist_name):
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

            output_dir = output_csv.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            cleaned_df.to_csv(output_csv, index=False)

            print(f"✅ Transformed file saved at: {output_csv}")
        else:
            print(f"⚠️ Missing input files for: {album_dir.name}")

def main():
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
