import shutil
import pandas as pd
from pathlib import Path
from difflib import get_close_matches
from datetime import datetime
from typing import List, Tuple

# =======================
# === CONFIGURATION  ===
# =======================

TRANSFORMED_GENIUS = Path("transformations/GENIUS")
TRANSFORMED_SPOTIFY = Path("transformations/SPOTIFY")
PROCESSED = Path("processed")
LOGS = Path("logs")
LOGS.mkdir(parents=True, exist_ok=True)

# ==========================
# === JOINING FUNCTION  ===
# ==========================

def join_album(artist_name: str, album_name: str) -> None:
    """
    Merge Genius lyrics with Spotify track data for a given album.

    Args:
        artist_name (str): Name of the artist.
        album_name (str): Name of the album.
    """
    # Locate cleaned lyrics files for the album
    lyrics_dir = TRANSFORMED_GENIUS / artist_name / album_name
    track_files = list(lyrics_dir.glob("*.txt"))

    # Exit early if no lyrics were found
    if not track_files:
        print(f"⚠️ No lyrics found for {artist_name} - {album_name}")
        return

    # Locate transformed Spotify track data
    spotify_csv = TRANSFORMED_SPOTIFY / artist_name / album_name / f"{album_name}_transformed.csv"
    if not spotify_csv.exists():
        print(f"❌ Missing transformed Spotify data for {artist_name} - {album_name}")
        return

    # Load Spotify track data
    df = pd.read_csv(spotify_csv)

    # Create a simplified version of song titles for matching
    df["CleanTitle"] = df["SongName"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)

    # Prepare containers for final results and logs
    lyrics_column: List[str] = []
    matched: List[Tuple[str, str]] = []
    missing: List[str] = []

    # Iterate through each track in the dataset
    for _, row in df.iterrows():
        clean_title = row["CleanTitle"]

        # Attempt direct match with simplified filenames
        match = next(
            (f for f in track_files if clean_title in f.stem.lower().replace(" ", "").replace("-", "").replace("_", "")),
            None
        )

        # If no direct match found, try fuzzy matching
        if not match:
            possible_matches = get_close_matches(
                clean_title,
                [f.stem.lower().replace(" ", "").replace("-", "").replace("_", "") for f in track_files],
                n=1, cutoff=0.7
            )
            if possible_matches:
                index = [
                    f.stem.lower().replace(" ", "").replace("-", "").replace("_", "") for f in track_files
                ].index(possible_matches[0])
                match = track_files[index]

        # If a match was found, read lyrics; otherwise, log as missing
        if match:
            lyrics = match.read_text(encoding="utf-8")
            lyrics_column.append(lyrics)
            matched.append((row["SongName"], match.name))
        else:
            lyrics_column.append("")
            missing.append(row["SongName"])

    # Assign collected lyrics to new column and remove helper column
    df["Lyrics"] = lyrics_column
    df.drop(columns=["CleanTitle"], inplace=True)

    # Define output path and ensure directory exists
    output_dir = PROCESSED / artist_name / album_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save final dataset with lyrics
    final_csv = output_dir / f"{album_name}_final.csv"
    df.to_csv(final_csv, index=False)
    print(f"✅ Final dataset saved to {final_csv}")

    # Log timestamped results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Log any missing lyrics
    if missing:
        with open(LOGS / f"missing_lyrics_{artist_name}_{album_name}_{timestamp}.log", "w", encoding="utf-8") as f:
            f.write("\n".join(missing))
        print("❌ Missing lyrics logged.")

    # Log successful matches
    if matched:
        with open(LOGS / f"matched_lyrics_{artist_name}_{album_name}_{timestamp}.log", "w", encoding="utf-8") as f:
            for song, filename in matched:
                f.write(f"{song} --> {filename}\n")

    # Copy merged artist-level metadata from Spotify to processed folder
    metadata_src = TRANSFORMED_SPOTIFY / artist_name / f"{artist_name}_merged_metadata.csv"
    metadata_dst = PROCESSED / artist_name / f"{artist_name}_merged_metadata.csv"
    if metadata_src.exists():
        shutil.copy(metadata_src, metadata_dst)
        print(f"📄 Copied artist metadata to {metadata_dst}")


# =======================
# === CLI ENTRYPOINT  ===
# =======================

def main() -> None:
    """
    CLI tool to merge Genius lyrics and Spotify track metadata
    for all albums of a given artist.
    """
    print("\n🔗 Genius + Spotify Lyrics Processor \n")

    while True:
        # Prompt the user to enter an artist name
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()

        # Exit the program if user types 'exit'
        if artist.lower() == "exit":
            print("\n👋 Exiting lyrics processor. See you next time!\n")
            break

        # Handle empty input
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        # Check if the transformed Genius lyrics directory exists for the artist
        albums_root = TRANSFORMED_GENIUS / artist
        if not albums_root.exists():
            print(f"❌ No transformed Genius lyrics found for '{artist}'.")
            continue

        # Process each album directory found under the artist's lyrics folder
        for album_dir in albums_root.iterdir():
            if album_dir.is_dir():
                print(f"\n📀 Processing album: {album_dir.name}")
                join_album(artist, album_dir.name)


if __name__ == "__main__":
    main()
