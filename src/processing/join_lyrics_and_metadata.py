import unicodedata
import pandas as pd
import shutil
import re
from pathlib import Path
from datetime import datetime
from difflib import get_close_matches


import unicodedata

def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "\u00a0": " ",  # non-breaking space
    }
    for src, target in replacements.items():
        text = text.replace(src, target)
    return text.strip()

def normalize_for_match(text: str) -> str:
    text = normalize_unicode(text)
    text = text.replace("[", "(").replace("]", ")")        # unify brackets
    text = re.sub(r"\s*\(.*?\)", "", text)                 # remove parentheticals
    text = re.sub(r"(?i)from the vault", "", text)         # remove vault mention
    text = re.sub(r"[^\w\s]", "", text)                    # remove punctuation
    return text.strip().lower()


def load_combined_lyrics_map(artist: str, album: str) -> dict:
    base_album = re.sub(r"\s*\(Taylor's Version\)", "", album).strip()
    genius_root = Path("transformations/GENIUS") / artist
    folders = [genius_root / album, genius_root / base_album]

    lyrics_map = {}
    for folder in folders:
        if folder.exists():
            for txt_file in folder.glob("*.txt"):
                key = normalize_unicode(txt_file.stem)
                if key not in lyrics_map:
                    with open(txt_file, "r", encoding="utf-8") as f:
                        lyrics_map[key] = f.read().strip()
    return lyrics_map


def match_lyrics(song_title: str, lyrics_map: dict, match_log: list) -> str:
    simplified_song = normalize_for_match(song_title)
    simplified_map = {normalize_for_match(k): k for k in lyrics_map}

    # Exact normalized match
    if simplified_song in simplified_map:
        original = simplified_map[simplified_song]
        match_log.append(f"{song_title} --> {original}")
        return lyrics_map[original]

    # Fuzzy prefix match
    for sim_key, original in simplified_map.items():
        if sim_key.startswith(simplified_song[:10]):
            match_log.append(f"{song_title} --> {original} (prefix)")
            return lyrics_map[original]

    # Final fuzzy match
    close = get_close_matches(simplified_song, list(simplified_map.keys()), n=1, cutoff=0.5)
    if close:
        original = simplified_map[close[0]]
        match_log.append(f"{song_title} --> {original} (fuzzy)")
        return lyrics_map[original]

    return ""




def find_album_dir_by_csv(artist: str, album: str) -> Path:
    artist_path = Path(f"transformations/SPOTIFY/{artist}")
    album_dirs = [d for d in artist_path.iterdir() if d.is_dir()]
    album = normalize_unicode(album.lower())

    candidates = []
    for folder in album_dirs:
        transformed_files = list(folder.glob("*_transformed.csv"))
        if not transformed_files:
            continue
        stem = normalize_unicode(transformed_files[0].stem.lower().replace("_transformed", ""))
        candidates.append((stem, folder))

    match_names = [c[0] for c in candidates]
    matches = get_close_matches(album, match_names, n=1, cutoff=0.4)

    if matches:
        for stem, folder in candidates:
            if stem == matches[0]:
                return folder

    for stem, folder in candidates:
        if album in stem:
            return folder

    raise FileNotFoundError(f"No matching album folder found for '{album}' in {artist_path}")


def join_album(artist: str, album: str, logs: list, successes: list):
    try:
        artist = normalize_unicode(artist)
        album = normalize_unicode(album)

        album_dir = find_album_dir_by_csv(artist, album)
        spotify_csv_files = list(album_dir.glob("*_transformed.csv"))
        if not spotify_csv_files:
            raise FileNotFoundError(f"No *_transformed.csv found in {album_dir}")
        spotify_csv = spotify_csv_files[0]

        metadata_src = Path(f"transformations/SPOTIFY/{artist}/{artist}_merged_metadata.csv")
        df = pd.read_csv(spotify_csv)
        df.insert(0, "TrackNumber", range(1, len(df) + 1))

        lyrics_map = load_combined_lyrics_map(artist, album)
        match_log = []
        df["Lyrics"] = df["SongName"].apply(lambda name: match_lyrics(name, lyrics_map, match_log))

        if match_log:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = Path("logs") / f"matched_lyrics_{artist}_{album}_{timestamp}.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(match_log))
            print(f"📒 Logged {len(match_log)} matched lyrics in {log_path}")

        missing = df[df["Lyrics"] == ""]["SongName"].tolist()
        if missing:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"missing_lyrics_{artist}_{album}_{timestamp}.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(missing))
            print(f"🕵️ Logged {len(missing)} missing lyrics in {log_path}")

        print(f"📝 Lyrics found for {len(df) - len(missing)}/{len(df)} songs")

        album_output_dir = Path(f"processed/{artist}/{album}")
        album_output_dir.mkdir(parents=True, exist_ok=True)
        final_output = album_output_dir / f"{album}_final.csv"
        df.to_csv(final_output, index=False)
        print(f"✅ Merged: {artist} - {album}")
        successes.append(f"{artist} - {album}")

        metadata_dst = Path(f"processed/{artist}/{artist}_merged_metadata.csv")
        if not metadata_dst.exists() and metadata_src.exists():
            shutil.copy(metadata_src, metadata_dst)
            print(f"📎 Copied metadata for: {artist}")

    except Exception as e:
        logs.append(f"{artist} - {album}: {str(e)}")


def run_full_processing():
    """
    Run the full processing pipeline for all artists and albums.
    Logs successes and failures for review.
    """
    genius_path = Path("transformations/GENIUS")
    logs = []
    successes = []

    # Iterate through all artist directories
    for artist_dir in genius_path.iterdir():
        if artist_dir.is_dir():
            artist_name = artist_dir.name
            # Iterate through all album directories for the artist
            for album_dir in artist_dir.iterdir():
                if album_dir.is_dir():
                    join_album(artist_name, album_dir.name, logs, successes)

    # Log failures
    if logs:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"failed_merging_lyrics_metadata_{timestamp}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))
        print(f"⚠️ {len(logs)} errors occurred. Logged in: {log_file}")

    # Final summary
    print(f"\n📊 SUMMARY")
    print(f"✅ Successful albums: {len(successes)}")
    print(f"❌ Failed albums: {len(logs)}")


if __name__ == "__main__":
    run_full_processing()
