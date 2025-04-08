import os
import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime
from pathlib import Path
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from typing import Optional, List, Tuple, Dict, Any

# =======================
# === CONFIGURATION  ===
# =======================

load_dotenv(Path(".env"))

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

PROCESSED_DIR = Path("processed")

# =======================
# === UTILITY METHODS ===
# =======================

def to_python_type(val: Any) -> Any:
    """Convert NumPy types to native Python types for DB insertion."""
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val

def is_valid_album_name(name: str) -> bool:
    """Check if album name should be included based on keywords."""
    excluded_keywords = ["deluxe", "live"]
    return not any(kw in name.lower() for kw in excluded_keywords)

# ============================
# === DATABASE CONNECTION ===
# ============================

def connect_db() -> psycopg2.extensions.connection:
    """Establish connection with PostgreSQL using credentials from .env."""
    return psycopg2.connect(**DB_PARAMS)

def create_tables(cursor: psycopg2.extensions.cursor) -> None:
    """Create all required PostgreSQL tables if they do not exist."""
    table_definitions = [
        # Artists
        """
        CREATE TABLE IF NOT EXISTS artists (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            birth_name TEXT,
            birth_date DATE,
            birth_place TEXT,
            country TEXT,
            active_years INTEGER,
            genres TEXT,
            instruments TEXT,
            vocal_type TEXT,
            popularity INTEGER,
            followers BIGINT,
            image_url TEXT,
            UNIQUE (name, birth_date)
        );
        """,
        # Albums
        """
        CREATE TABLE IF NOT EXISTS albums (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
            release_date DATE,
            popularity INTEGER,
            image_url TEXT,
            UNIQUE (name, artist_id)
        );
        """,
        # Tracks
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
            track_number INTEGER,
            duration_ms INTEGER,
            explicit BOOLEAN,
            popularity INTEGER,
            UNIQUE (name, album_id)
        );
        """,
        # Lyrics
        """
        CREATE TABLE IF NOT EXISTS lyrics (
            track_id INTEGER PRIMARY KEY REFERENCES tracks(id) ON DELETE CASCADE,
            text TEXT,
            readability_score REAL,
            sentiment_score REAL,
            word_count INTEGER,
            line_count INTEGER,
            char_count INTEGER,
            lexical_density REAL
        );
        """,
        # Word frequencies (track)
        """
        CREATE TABLE IF NOT EXISTS word_frequencies_track (
            track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
            word TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (track_id, word)
        );
        """,
        # Word frequencies (album)
        """
        CREATE TABLE IF NOT EXISTS word_frequencies_album (
            album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
            word TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (album_id, word)
        );
        """
    ]
    for statement in table_definitions:
        cursor.execute(statement)

# ====================
# === CSV PARSERS ===
# ====================

def parse_artist_csv(path: Path) -> Dict[str, Any]:
    """Parse merged metadata for a single artist.

    Args:
        path (Path): Path to artist metadata CSV.

    Returns:
        Dict[str, Any]: Dictionary with artist metadata.
    """
    row = pd.read_csv(path).iloc[0]
    return {
        "name": row.get("Name"),
        "birth_name": row.get("BirthName"),
        "birth_date": row.get("DateOfBirth"),
        "birth_place": row.get("PlaceOfBirth"),
        "country": str(row.get("CountryOfCitizenship", "")).strip(),
        "active_years": row.get("WorkPeriodStart"),
        "genres": ", ".join(filter(None, [
            str(row.get("GenresWikidata", "")).strip(),
            str(row.get("GenresSpotify", "")).strip()
        ])),
        "instruments": row.get("Instruments"),
        "vocal_type": row.get("VoiceType"),
        "popularity": row.get("Popularity"),
        "followers": row.get("Followers"),
        "image_url": row.get("ImageURL"),
    }

def parse_album_csv(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parse a processed album CSV with track and lyric information.

    Args:
        path (Path): Path to album-level CSV.

    Returns:
        Tuple: Album metadata and list of tracks with optional lyrics.
    """
    df = pd.read_csv(path).fillna("")
    album = df.iloc[0]
    album_data = {
        "name": album["AlbumName"],
        "release_date": album["ReleaseDateAlbum"],
        "popularity": album["AlbumPopularity"],
        "image_url": album.get("ImageURL", "")
    }
    tracks = [{
        "name": row["SongName"],
        "track_number": i + 1,
        "duration_ms": row["DurationMs"],
        "explicit": row["Explicit"],
        "popularity": row["SongPopularity"],
        "lyrics": row.get("Lyrics", "")
    } for i, row in df.iterrows()]
    return album_data, tracks

# ===========================
# === DATABASE INSERTION ===
# ===========================

def insert_artist(cursor, artist: Dict[str, Any]) -> Optional[int]:
    cursor.execute("""
        INSERT INTO artists (
            name, birth_name, birth_date, birth_place, country,
            active_years, genres, instruments, vocal_type,
            popularity, followers, image_url
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, birth_date) DO NOTHING RETURNING id;
    """, tuple(to_python_type(artist[k]) for k in [
        "name", "birth_name", "birth_date", "birth_place", "country",
        "active_years", "genres", "instruments", "vocal_type",
        "popularity", "followers", "image_url"
    ]))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_album(cursor, album: Dict[str, Any], artist_id: int) -> Optional[int]:
    cursor.execute("""
        INSERT INTO albums (name, artist_id, release_date, popularity, image_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name, artist_id) DO NOTHING RETURNING id;
    """, (
        to_python_type(album["name"]),
        to_python_type(artist_id),
        to_python_type(album["release_date"]),
        to_python_type(album["popularity"]),
        to_python_type(album["image_url"])
    ))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_tracks(cursor, tracks: List[Dict[str, Any]], album_id: int) -> None:
    values = [(
        to_python_type(t["name"]),
        to_python_type(album_id),
        to_python_type(t["track_number"]),
        to_python_type(t["duration_ms"]),
        to_python_type(t["explicit"]),
        to_python_type(t["popularity"])
    ) for t in tracks]

    execute_values(cursor, """
        INSERT INTO tracks (name, album_id, track_number, duration_ms, explicit, popularity)
        VALUES %s
        ON CONFLICT (name, album_id) DO NOTHING;
    """, values)

def get_track_name_to_id(cursor, album_id: int) -> Dict[str, int]:
    cursor.execute("SELECT id, name FROM tracks WHERE album_id = %s", (album_id,))
    return {name: tid for tid, name in cursor.fetchall()}

def insert_lyrics(cursor, tracks: List[Dict[str, Any]], track_name_to_id: Dict[str, int]) -> None:
    for t in tracks:
        track_id = track_name_to_id.get(t["name"])
        if not track_id:
            print(f"  ⚠️ No match for lyrics: {t['name']}")
            continue
        cursor.execute("""
            INSERT INTO lyrics (track_id, text, readability_score, sentiment_score)
            VALUES (%s, %s, NULL, NULL)
            ON CONFLICT (track_id) DO NOTHING;
        """, (track_id, to_python_type(t["lyrics"])))

# ====================
# === MAIN ROUTINE ===
# ====================

def main() -> None:
    """CLI to load cleaned data into PostgreSQL from 'processed' directory."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SET search_path TO public;")
    create_tables(cursor)
    conn.commit()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(f"logs/skipped_albums_{timestamp}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w", encoding="utf-8")

    print("\n🚀 PostgreSQL Loader (multi-artist mode)")

    while True:
        artist = input("\n🎤 Enter artist name to load (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting loader. Goodbye!")
            break

        artist_dir = PROCESSED_DIR / artist
        artist_csv = artist_dir / f"{artist}_merged_metadata.csv"
        if not artist_csv.exists():
            print(f"⚠️ No metadata for: {artist}")
            continue

        artist_data = parse_artist_csv(artist_csv)
        artist_id = insert_artist(cursor, artist_data)
        if not artist_id:
            cursor.execute("SELECT id FROM artists WHERE name = %s", (to_python_type(artist_data["name"]),))
            result = cursor.fetchone()
            artist_id = result[0] if result else None

        if not artist_id:
            print("❌ Could not insert or retrieve artist ID.")
            continue

        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir() or not is_valid_album_name(album_dir.name):
                log_file.write(f"{artist}/{album_dir.name}\n")
                continue

            for file in album_dir.glob("*_final.csv"):
                album_data, tracks = parse_album_csv(file)
                album_id = insert_album(cursor, album_data, artist_id)

                if not album_id:
                    cursor.execute("SELECT id FROM albums WHERE name = %s AND artist_id = %s", (
                        to_python_type(album_data["name"]), to_python_type(artist_id)))
                    result = cursor.fetchone()
                    album_id = result[0] if result else None

                if not album_id:
                    print("❌ Could not insert or retrieve album ID.")
                    continue

                insert_tracks(cursor, tracks, album_id)
                track_ids = get_track_name_to_id(cursor, album_id)
                insert_lyrics(cursor, tracks, track_ids)
                conn.commit()

    cursor.close()
    log_file.close()
    conn.close()
    print("\n✅ Load complete.")

if __name__ == "__main__":
    main()