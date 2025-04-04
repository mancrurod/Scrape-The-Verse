import shutil
import pandas as pd
from pathlib import Path
from difflib import get_close_matches
from datetime import datetime

TRANSFORMED_GENIUS = Path("transformations/GENIUS")
TRANSFORMED_SPOTIFY = Path("transformations/SPOTIFY")
PROCESSED = Path("processed")
LOGS = Path("logs")
LOGS.mkdir(parents=True, exist_ok=True)

def join_album(artist_name: str, album_name: str):
    artist_folder = TRANSFORMED_GENIUS / artist_name / album_name
    track_files = list(artist_folder.glob("*.txt"))
    
    if not track_files:
        print(f"⚠️ No lyrics found for {artist_name} - {album_name}")
        return

    transformed_csv = TRANSFORMED_SPOTIFY / artist_name / album_name / f"{album_name}_transformed.csv"
    if not transformed_csv.exists():
        print(f"❌ Missing transformed Spotify data for {artist_name} - {album_name}")
        return

    df = pd.read_csv(transformed_csv)
    df["CleanTitle"] = df["SongName"].str.lower().str.replace(r"[^a-z0-9]", "", regex=True)

    lyrics_column = []
    matched = []
    missing = []

    for _, row in df.iterrows():
        clean_title = row["CleanTitle"]
        match = None

        for file in track_files:
            filename = file.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
            if clean_title in filename or filename in clean_title:
                match = file
                break

        if not match:
            matches = get_close_matches(clean_title, [f.stem.lower().replace(" ", "").replace("-", "").replace("_", "") for f in track_files], n=1, cutoff=0.7)
            if matches:
                idx = [f.stem.lower().replace(" ", "").replace("-", "").replace("_", "") for f in track_files].index(matches[0])
                match = track_files[idx]

        if match:
            with open(match, encoding="utf-8") as f:
                lyrics = f.read()
            lyrics_column.append(lyrics)
            matched.append((row["SongName"], match.name))
        else:
            lyrics_column.append("")
            missing.append(row["SongName"])

    df["Lyrics"] = lyrics_column
    df.drop(columns=["CleanTitle"], inplace=True)

    output_path = PROCESSED / artist_name / album_name
    output_path.mkdir(parents=True, exist_ok=True)
    output_csv = output_path / f"{album_name}_final.csv"
    df.to_csv(output_csv, index=False)
    print(f"✅ Final dataset saved to {output_csv}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if missing:
        with open(LOGS / f"missing_lyrics_{artist_name}_{album_name}_{timestamp}.log", "w", encoding="utf-8") as f:
            f.write("\n".join(missing))
        print(f"❌ Missing lyrics logged.")
    if matched:
        with open(LOGS / f"matched_lyrics_{artist_name}_{album_name}_{timestamp}.log", "w", encoding="utf-8") as f:
            for song, file in matched:
                f.write(f"{song} --> {file}\n")

    # Copy merged metadata
    metadata_src = TRANSFORMED_SPOTIFY / artist_name / f"{artist_name}_merged_metadata.csv"
    metadata_dst = PROCESSED / artist_name / f"{artist_name}_merged_metadata.csv"
    if metadata_src.exists():
        shutil.copy(metadata_src, metadata_dst)
        print(f"📄 Copied artist metadata to {metadata_dst}")

def main():
    print("\n🧬 Genius + Spotify Lyrics Processor (multi-artist mode)\n")

    while True:
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting lyrics processor. See you next time!\n")
            break
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        albums_path = TRANSFORMED_GENIUS / artist
        if not albums_path.exists():
            print(f"❌ No transformed Genius lyrics found for '{artist}'.")
            continue

        for album_dir in albums_path.iterdir():
            if album_dir.is_dir():
                print(f"\n📀 Processing album: {album_dir.name}")
                join_album(artist, album_dir.name)


if __name__ == "__main__":
    main()
