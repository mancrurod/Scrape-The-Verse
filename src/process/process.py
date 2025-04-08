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
    lyrics_dir = TRANSFORMED_GENIUS / artist_name / album_name
    track_files = list(lyrics_dir.glob("*.txt"))
    if not track_files:
        print(f"⚠️ No lyrics found for {artist_name} - {album_name}")
        return

    spotify_csv = TRANSFORMED_SPOTIFY / artist_name / album_name / f"{album_name}_transformed.csv"
    if not spotify_csv.exists():
        print(f"❌ Missing transformed Spotify data for {artist_name} - {album_name}")
        return

    df = pd.read_csv(spotify_csv)
    df["CleanTitle"] = df["SongName"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)

    lyrics_column: List[str] = []
    matched: List[Tuple[str, str]] = []
    missing: List[str] = []

    for _, row in df.iterrows():
        clean_title = row["CleanTitle"]
        match = next(
            (f for f in track_files if clean_title in f.stem.lower().replace(" ", "").replace("-", "").replace("_", "")),
            None
        )

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

        if match:
            lyrics = match.read_text(encoding="utf-8")
            lyrics_column.append(lyrics)
            matched.append((row["SongName"], match.name))
        else:
            lyrics_column.append("")
            missing.append(row["SongName"])

    df["Lyrics"] = lyrics_column
    df.drop(columns=["CleanTitle"], inplace=True)

    output_dir = PROCESSED / artist_name / album_name
    output_dir.mkdir(parents=True, exist_ok=True)
    final_csv = output_dir / f"{album_name}_final.csv"
    df.to_csv(final_csv, index=False)
    print(f"✅ Final dataset saved to {final_csv}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if missing:
        with open(LOGS / f"missing_lyrics_{artist_name}_{album_name}_{timestamp}.log", "w", encoding="utf-8") as f:
            f.write("\n".join(missing))
        print("❌ Missing lyrics logged.")

    if matched:
        with open(LOGS / f"matched_lyrics_{artist_name}_{album_name}_{timestamp}.log", "w", encoding="utf-8") as f:
            for song, filename in matched:
                f.write(f"{song} --> {filename}\n")

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
    CLI tool to merge Genius and Spotify data for all albums of a given artist.
    """
    print("\n🔗 Genius + Spotify Lyrics Processor \n")

    while True:
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting lyrics processor. See you next time!\n")
            break
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        albums_root = TRANSFORMED_GENIUS / artist
        if not albums_root.exists():
            print(f"❌ No transformed Genius lyrics found for '{artist}'.")
            continue

        for album_dir in albums_root.iterdir():
            if album_dir.is_dir():
                print(f"\n📀 Processing album: {album_dir.name}")
                join_album(artist, album_dir.name)

if __name__ == "__main__":
    main()
