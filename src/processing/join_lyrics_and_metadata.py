import unicodedata
import pandas as pd
import shutil
import re
from pathlib import Path
from datetime import datetime
from difflib import get_close_matches

def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "\u00a0": " "
    }
    for src, target in replacements.items():
        text = text.replace(src, target)
    return text.strip()

def normalize_for_match(text: str) -> str:
    # Normalize text (remove accents, special characters, etc.)
    text = normalize_unicode(text)
    
    # Replace brackets (if any) with parentheses
    text = text.replace('[', '(').replace(']', ')')
    
    # Keep version identifiers intact by capturing anything within parentheses (which would be version-related)
    text = re.sub(r'\s*\((.*?version.*?)\)', r' \1', text, flags=re.IGNORECASE)
    
    # Eliminate other unwanted content like "feat", "remix", etc., without affecting version info
    text = re.sub(r'(feat\..*|explicit|remix|pop mix|radio edit|slow version|vault)', '', text, flags=re.IGNORECASE)
    
    # Clean up special characters, but leave version-related content intact
    text = re.sub(r'[^\w\s\(\)]', '', text)  # Allow parentheses to remain for versioning

    return text.strip().lower()



def find_album_folder_path(artist: str, album: str) -> Path:
    """Busca la carpeta real del álbum, normalizando el nombre y aplicando coincidencia fuzzy si es necesario."""
    artist_path = Path("transformations/GENIUS") / artist
    album_folders = [f for f in artist_path.iterdir() if f.is_dir()]

    normalized_album = normalize_unicode(album).lower()
    folder_map = {normalize_unicode(f.name).lower(): f for f in album_folders}

    if normalized_album in folder_map:
        return folder_map[normalized_album]

    from difflib import get_close_matches
    match = get_close_matches(normalized_album, folder_map.keys(), n=1, cutoff=0.85)
    if match:
        return folder_map[match[0]]

    raise FileNotFoundError(f"❌ No matching folder found for '{album}' under {artist_path}")


def load_combined_lyrics_map(artist: str, album: str) -> dict:
    folder = find_album_folder_path(artist, album)
    lyrics_map = {}

    if folder.exists():
        for txt_file in folder.glob("*.txt"):
            key = normalize_for_match(txt_file.stem)
            print(f"📂 Loaded lyric file: {txt_file.name} --> key: {key}")
            if key in lyrics_map:
                print(f"⚠️ DUPLICATE KEY: '{key}' already mapped. Skipping {txt_file.name}")
                continue
            with open(txt_file, "r", encoding="utf-8") as f:
                lyrics_map[key] = f.read().strip()
    else:
        print(f"🚫 Folder does not exist: {folder}")

    return lyrics_map


def match_lyrics(song_title: str, lyrics_map: dict, match_log: list) -> str:
    simplified_song = normalize_for_match(song_title)
    print(f"🔍 Matching: '{song_title}' -> '{simplified_song}'")
    print(f"🔑 Available keys: {list(lyrics_map.keys())[:5]}{' ...' if len(lyrics_map) > 5 else ''}")

    if simplified_song in lyrics_map:
        match_log.append(f"{song_title} --> {simplified_song} (exact)")
        return lyrics_map[simplified_song]

    for key in lyrics_map:
        if key.startswith(simplified_song[:10]):
            match_log.append(f"{song_title} --> {key} (prefix)")
            return lyrics_map[key]

    close = get_close_matches(simplified_song, list(lyrics_map.keys()), n=1, cutoff=0.6)
    if close:
        match_log.append(f"{song_title} --> {close[0]} (fuzzy)")
        return lyrics_map[close[0]]

    match_log.append(f"{song_title} --> ❌ No match")
    print(f"🔍 No match for '{song_title}'. Available keys: {list(lyrics_map.keys())}")
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
        if not lyrics_map:
            raise ValueError(f"❌ No lyrics loaded for {artist} - {album}. Make sure .txt files exist and are readable.")
        else:
            print(f"✅ Loaded {len(lyrics_map)} lyrics for matching")
            print(f"📝 Sample keys: {list(lyrics_map.keys())[:5]}{' ...' if len(lyrics_map) > 5 else ''}")

        match_log = []
        df["Lyrics"] = df["SongName"].apply(lambda name: match_lyrics(name, lyrics_map, match_log))

        if df['Lyrics'].eq('').all():
            print(f"⚠️ WARNING: No lyrics matched any song in {artist} - {album}. Check normalization logic.")

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
    genius_path = Path("transformations/GENIUS")
    logs = []
    successes = []

    for artist_dir in genius_path.iterdir():
        if artist_dir.is_dir():
            artist_name = artist_dir.name
            for album_dir in artist_dir.iterdir():
                if album_dir.is_dir():
                    join_album(artist_name, album_dir.name, logs, successes)

    if logs:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"failed_merging_lyrics_metadata_{timestamp}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))
        print(f"⚠️ {len(logs)} errors occurred. Logged in: {log_file}")

    print(f"\n📊 SUMMARY")
    print(f"✅ Successful albums: {len(successes)}")
    print(f"❌ Failed albums: {len(logs)}")

if __name__ == "__main__":
    run_full_processing()