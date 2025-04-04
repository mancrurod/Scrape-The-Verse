import os
import pandas as pd
import numpy as np
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# === CONFIG ===
load_dotenv(Path(".env"))
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}
PROCESSED_DIR = Path("processed")

# === UTILS ===
def to_python_type(val):
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val

# === DB ===
def connect_db():
    return psycopg2.connect(**DB_PARAMS)

def create_tables(cursor):
    cursor.execute("""
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
            UNIQUE (name, birth_date)
        );
        CREATE TABLE IF NOT EXISTS albums (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            artist_id INTEGER REFERENCES artists(id),
            release_date DATE,
            popularity INTEGER,
            UNIQUE (name, artist_id)
        );
        CREATE TABLE IF NOT EXISTS tracks (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            album_id INTEGER REFERENCES albums(id),
            track_number INTEGER,
            duration_ms INTEGER,
            explicit BOOLEAN,
            popularity INTEGER,
            UNIQUE (name, album_id)
        );
        CREATE TABLE IF NOT EXISTS lyrics (
            track_id INTEGER PRIMARY KEY REFERENCES tracks(id),
            text TEXT,
            readability_score REAL,
            sentiment_score REAL
        );
    """)

# === PARSING ===
def parse_artist_csv(path: Path) -> dict:
    row = pd.read_csv(path).iloc[0]
    return {
        "name": row.get("Name"),
        "birth_name": row.get("BirthName"),
        "birth_date": row.get("DateOfBirth"),
        "birth_place": row.get("PlaceOfBirth"),
        "country": row.get("CountryOfCitizenship"),
        "active_years": row.get("WorkPeriodStart"),
        "genres": ", ".join(filter(None, [str(row.get("GenresWikidata", "")), str(row.get("GenresSpotify", ""))])),
        "instruments": row.get("Instruments"),
        "vocal_type": row.get("VoiceType"),
    }

def parse_album_csv(path: Path):
    df = pd.read_csv(path)
    df.fillna("", inplace=True)
    album = df.iloc[0]
    album_data = {
        "name": album["AlbumName"],
        "release_date": album["ReleaseDateAlbum"],
        "popularity": album["AlbumPopularity"],
    }
    tracks = []
    for i, row in df.iterrows():
        tracks.append({
            "name": row["SongName"],
            "track_number": i + 1,
            "duration_ms": row["DurationMs"],
            "explicit": row["Explicit"],
            "popularity": row["SongPopularity"],
            "lyrics": row.get("Lyrics", ""),
        })
    return album_data, tracks

# === INSERTS ===
def insert_artist(cursor, artist):
    cursor.execute("""
        INSERT INTO artists (name, birth_name, birth_date, birth_place, country,
        active_years, genres, instruments, vocal_type)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (name, birth_date) DO NOTHING RETURNING id;
    """, tuple(to_python_type(artist[k]) for k in artist))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_album(cursor, album, artist_id):
    cursor.execute("""
        INSERT INTO albums (name, artist_id, release_date, popularity)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name, artist_id) DO NOTHING RETURNING id;
    """, (
        to_python_type(album["name"]),
        to_python_type(artist_id),
        to_python_type(album["release_date"]),
        to_python_type(album["popularity"])
    ))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_tracks(cursor, tracks, album_id):
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

def get_track_name_to_id(cursor, album_id):
    cursor.execute("SELECT id, name FROM tracks WHERE album_id = %s;", (album_id,))
    return {name: track_id for track_id, name in cursor.fetchall()}

def insert_lyrics(cursor, tracks, track_name_to_id):
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

# === MAIN ===
def main():
    conn = connect_db()
    cursor = conn.cursor()
    create_tables(cursor)
    conn.commit()

    print("\n🚀 PostgreSQL Loader (multi-artist mode)")

    while True:
        artist_input = input("\n🎤 Enter artist name to load (or type 'exit' to quit): ").strip()
        if artist_input.lower() == "exit":
            print("\n👋 Exiting loader. Goodbye!")
            break

        artist_dir = PROCESSED_DIR / artist_input
        artist_csv = artist_dir / f"{artist_input}_merged_metadata.csv"
        if not artist_csv.exists():
            print(f"⚠️ No metadata for: {artist_input}")
            continue

        print(f"\n🎤 Processing artist: {artist_input}")
        artist_data = parse_artist_csv(artist_csv)
        artist_id = insert_artist(cursor, artist_data)
        if not artist_id:
            cursor.execute(
                "SELECT id FROM artists WHERE name = %s",
                (to_python_type(artist_data["name"]),)
            )
            res = cursor.fetchone()
            artist_id = res[0] if res else None

        if not artist_id:
            print("❌ Could not insert or retrieve the artist ID.")
            continue

        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir():
                continue
            for file in album_dir.glob("*_final.csv"):
                print(f"\n   💿 Album: {album_dir.name}")
                album_data, tracks_data = parse_album_csv(file)
                album_id = insert_album(cursor, album_data, artist_id)
            if not album_id:
                cursor.execute(
                    "SELECT id FROM albums WHERE name = %s AND artist_id = %s",
                    (to_python_type(str(album_data["name"])), to_python_type(artist_id))
                )
                res = cursor.fetchone()
                album_id = res[0] if res else None

                if not album_id:
                    print("❌ Could not insert or retrieve the album ID.")
                    continue
                insert_tracks(cursor, tracks_data, album_id)
                track_id_map = get_track_name_to_id(cursor, album_id)
                insert_lyrics(cursor, tracks_data, track_id_map)
                conn.commit()

    cursor.close()
    conn.close()
    print("\n✅ Load complete.")

if __name__ == "__main__":
    main()
