# ================================================================
# 🔗 join_lyrics_and_metadata_cleaned.py
# Combina los .csv de SPOTIFY (transformados) con las letras limpias de GENIUS.
# Guarda un nuevo .csv en processed/<artist>/<album>/_final.csv
# y copia los metadatos a nivel artista.
# ================================================================

import unicodedata
import pandas as pd
import shutil
import re
from pathlib import Path
from datetime import datetime
from difflib import get_close_matches
import numpy as np

# ================================================================
# 🔧 Normalización
# ================================================================

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
    text = normalize_unicode(text)
    text = text.replace('[', '(').replace(']', ')')
    text = re.sub(r'\s*\((.*?version.*?)\)', r' \1', text, flags=re.IGNORECASE)
    text = re.sub(r'(feat\..*|explicit|remix|pop mix|radio edit|slow version|vault)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[^\w\s\(\)]', '', text)
    return text.strip().lower()

# ================================================================
# 🗂 Acceso a carpetas y archivos
# ================================================================

def find_album_folder_path(artist: str, album: str) -> Path:
    artist_path = Path("transformations/GENIUS") / artist
    album_folders = [f for f in artist_path.iterdir() if f.is_dir()]
    normalized_album = normalize_unicode(album).lower()
    folder_map = {normalize_unicode(f.name).lower(): f for f in album_folders}

    if normalized_album in folder_map:
        return folder_map[normalized_album]

    match = get_close_matches(normalized_album, folder_map.keys(), n=1, cutoff=0.85)
    if match:
        return folder_map[match[0]]

    raise FileNotFoundError(f"❌ No matching folder found for '{album}' under {artist_path}")

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

# ================================================================
# 🎤 Carga de letras
# ================================================================

def load_combined_lyrics_map(artist: str, album: str) -> dict:
    folder = find_album_folder_path(artist, album)
    lyrics_map = {}

    for txt_file in folder.glob("*.txt"):
        key = normalize_for_match(txt_file.stem)
        print(f"📂 Loaded lyric file: {txt_file.name} --> key: {key}")
        if key in lyrics_map:
            print(f"⚠️ DUPLICATE KEY: '{key}' already mapped. Skipping {txt_file.name}")
            continue
        with open(txt_file, "r", encoding="utf-8") as f:
            lyrics_map[key] = f.read().strip()

    return lyrics_map

def match_lyrics(song_title: str, lyrics_map: dict, match_log: list) -> str:
    simplified = normalize_for_match(song_title)
    print(f"🔍 Matching: '{song_title}' -> '{simplified}'")
    print(f"🔑 Available keys: {list(lyrics_map.keys())[:5]}{' ...' if len(lyrics_map) > 5 else ''}")

    if simplified in lyrics_map:
        match_log.append(f"{song_title} --> {simplified} (exact)")
        return lyrics_map[simplified]

    for key in lyrics_map:
        if key.startswith(simplified[:10]):
            match_log.append(f"{song_title} --> {key} (prefix)")
            return lyrics_map[key]

    close = get_close_matches(simplified, list(lyrics_map.keys()), n=1, cutoff=0.6)
    if close:
        match_log.append(f"{song_title} --> {close[0]} (fuzzy)")
        return lyrics_map[close[0]]

    match_log.append(f"{song_title} --> ❌ No match")
    print(f"🔍 No match for '{song_title}'")
    return ""

# ================================================================
# 🧠 Normalización de tipos (antes de guardar .csv final)
# ================================================================

def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["TrackNumber", "SongPopularity", "DurationMs", "AlbumPopularity"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if not pd.isna(x) else None)
    if "Explicit" in df.columns:
        df["Explicit"] = df["Explicit"].apply(lambda x: bool(x) if not pd.isna(x) else False)
    return df

# ================================================================
# 🧩 Lógica principal por álbum
# ================================================================

def join_album(artist: str, album: str, logs: list, successes: list):
    try:
        artist = normalize_unicode(artist)
        album = normalize_unicode(album)

        album_dir = find_album_dir_by_csv(artist, album)
        spotify_csv_files = list(album_dir.glob("*_transformed.csv"))
        if not spotify_csv_files:
            raise FileNotFoundError(f"No *_transformed.csv found in {album_dir}")

        df = pd.read_csv(spotify_csv_files[0])
        df.insert(0, "TrackNumber", range(1, len(df) + 1))

        lyrics_map = load_combined_lyrics_map(artist, album)
        if not lyrics_map:
            raise ValueError(f"❌ No lyrics loaded for {artist} - {album}")

        match_log = []
        df["Lyrics"] = df["SongName"].apply(lambda name: match_lyrics(name, lyrics_map, match_log))

        if df['Lyrics'].eq('').all():
            print(f"⚠️ WARNING: No lyrics matched any song in {artist} - {album}")

        # Guardar logs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        if match_log:
            with open(log_dir / f"matched_lyrics_{artist}_{album}_{timestamp}.log", "w", encoding="utf-8") as f:
                f.write("\n".join(match_log))

        missing = df[df["Lyrics"] == ""]["SongName"].tolist()
        if missing:
            with open(log_dir / f"missing_lyrics_{artist}_{album}_{timestamp}.log", "w", encoding="utf-8") as f:
                f.write("\n".join(missing))

        print(f"📝 Lyrics found for {len(df) - len(missing)}/{len(df)} songs")

        # Guardar CSV final
        df = convert_types(df)
        output_dir = Path(f"processed/{artist}/{album}")
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_dir / f"{album}_final.csv", index=False)
        print(f"✅ Merged: {artist} - {album}")
        successes.append(f"{artist} - {album}")

        # Copiar metadatos a nivel artista
        metadata_src = Path(f"transformations/SPOTIFY/{artist}/{artist}_merged_metadata.csv")
        metadata_dst = Path(f"processed/{artist}/{artist}_merged_metadata.csv")
        if metadata_src.exists():
            shutil.copy(metadata_src, metadata_dst)
            print(f"📎 Copied metadata for: {artist}")

    except Exception as e:
        logs.append(f"{artist} - {album}: {str(e)}")

# ================================================================
# 🔁 Loop principal
# ================================================================

def run_full_processing():
    genius_path = Path("transformations/GENIUS")
    logs = []
    successes = []

    for artist_dir in genius_path.iterdir():
        if artist_dir.is_dir():
            for album_dir in artist_dir.iterdir():
                if album_dir.is_dir():
                    join_album(artist_dir.name, album_dir.name, logs, successes)

    if logs:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(Path("logs") / f"failed_merging_lyrics_metadata_{timestamp}.log", "w", encoding="utf-8") as f:
            f.write("\n".join(logs))
        print(f"⚠️ {len(logs)} errors occurred")

    print(f"\n📊 SUMMARY")
    print(f"✅ Successful albums: {len(successes)}")
    print(f"❌ Failed albums: {len(logs)}")

if __name__ == "__main__":
    run_full_processing()
