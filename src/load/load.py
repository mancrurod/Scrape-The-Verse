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
# === CONFIGURATION   ===
# =======================

# Load environment variables from .env file
load_dotenv(Path(".env"))

# PostgreSQL connection parameters loaded from environment
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),  # Default to localhost if not provided
    "port": os.getenv("POSTGRES_PORT", 5432),         # Default port for PostgreSQL
}

# Path to the root directory containing processed datasets
PROCESSED_DIR = Path("processed")

# =======================
# === UTILITY METHODS ===
# =======================

def to_python_type(val: Any) -> Any:
    """Convert NumPy types to native Python types for DB insertion.

    Args:
        val (Any): The input value (could be NumPy or native Python type).

    Returns:
        Any: Native Python type or None if the value is NaN.
    """
    if pd.isna(val):
        return None  # Handle missing values as NULL in database
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val  # Return as-is if already native or not convertible


def is_valid_album_name(name: str) -> bool:
    """Check whether the album name should be included (filters out 'deluxe' or 'live' editions).

    Args:
        name (str): The name of the album.

    Returns:
        bool: True if the album is considered valid, False if it should be excluded.
    """
    excluded_keywords = ["deluxe", "live"]
    return not any(kw in name.lower() for kw in excluded_keywords)


# ============================
# === DATABASE CONNECTION ===
# ============================

def connect_db() -> psycopg2.extensions.connection:
    """Establish a connection to the PostgreSQL database using credentials from the .env file.

    Returns:
        psycopg2.extensions.connection: A live PostgreSQL connection object.
    """
    # Connect to PostgreSQL using parameters loaded from environment variables
    return psycopg2.connect(**DB_PARAMS)


def create_tables(cursor: psycopg2.extensions.cursor) -> None:
    """
    Create all required PostgreSQL tables if they do not exist.

    Args:
        cursor (psycopg2.extensions.cursor): Active database cursor.
    """
    table_definitions = [
        # Table: artists — stores artist-level metadata from Spotify and Wikidata
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
            UNIQUE (name, birth_date)  -- Avoid duplicates on key identity fields
        );
        """,
        # Table: albums — stores album-level metadata linked to an artist
        """
        CREATE TABLE IF NOT EXISTS albums (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
            release_date DATE,
            popularity INTEGER,
            image_url TEXT,
            UNIQUE (name, artist_id)  -- Prevent duplicate albums per artist
        );
        """,
        # Table: tracks — stores track-level metadata linked to an album
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
            track_number INTEGER,
            duration_ms INTEGER,
            explicit BOOLEAN,
            popularity INTEGER,
            UNIQUE (name, album_id)  -- Prevent duplicate track entries
        );
        """,
        # Table: lyrics — stores processed lyrics and linguistic analysis per track
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
        # Table: word_frequencies_track — stores word counts per track
        """
        CREATE TABLE IF NOT EXISTS word_frequencies_track (
            track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
            word TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (track_id, word)  -- Composite key to avoid duplicates
        );
        """,
        # Table: word_frequencies_album — stores aggregated word counts per album
        """
        CREATE TABLE IF NOT EXISTS word_frequencies_album (
            album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
            word TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (album_id, word)  -- Composite key to avoid duplicates
        );
        """
    ]

    # Execute each CREATE TABLE statement
    for statement in table_definitions:
        cursor.execute(statement)

# ====================
# === CSV PARSERS ===
# ====================

def parse_artist_csv(path: Path) -> Dict[str, Any]:
    """
    Parse merged Spotify + Wikidata metadata for a single artist.

    Args:
        path (Path): Path to the artist's merged metadata CSV file.

    Returns:
        Dict[str, Any]: Dictionary containing cleaned artist metadata.
    """
    # Load the first (and only) row of the CSV into a pandas Series
    row = pd.read_csv(path).iloc[0]

    # Build a dictionary with standardized artist metadata fields
    return {
        "name": row.get("Name"),
        "birth_name": row.get("BirthName"),
        "birth_date": row.get("DateOfBirth"),
        "birth_place": row.get("PlaceOfBirth"),
        "country": str(row.get("CountryOfCitizenship", "")).strip(),
        "active_years": row.get("WorkPeriodStart"),

        # Combine genres from Wikidata and Spotify, if both are present
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
    """
    Parse a processed album CSV containing both album metadata and track-level details.

    Args:
        path (Path): Path to the album-level CSV file.

    Returns:
        Tuple[Dict[str, Any], List[Dict[str, Any]]]: 
            - A dictionary with album metadata.
            - A list of dictionaries, one per track (with optional lyrics).
    """
    # Load the CSV into a DataFrame and fill missing values with empty strings
    df = pd.read_csv(path).fillna("")

    # Extract album metadata from the first row (shared across all tracks)
    album = df.iloc[0]
    album_data = {
        "name": album["AlbumName"],
        "release_date": album["ReleaseDateAlbum"],
        "popularity": album["AlbumPopularity"],
        "image_url": album.get("ImageURL", "")
    }

    # Extract and structure track-level data (including lyrics if present)
    tracks = [{
        "name": row["SongName"],
        "track_number": i + 1,  # Assign track number based on row index
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
    """
    Insert an artist record into the 'artists' table.

    Args:
        cursor: Active psycopg2 cursor.
        artist (Dict[str, Any]): Dictionary containing artist metadata.

    Returns:
        Optional[int]: The inserted artist's ID, or None if the record already exists.
    """
    # Execute INSERT query with ON CONFLICT clause to avoid duplicates
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

    # Fetch the inserted ID (if new), or None if skipped due to conflict
    result = cursor.fetchone()
    return result[0] if result else None


def insert_album(cursor, album: Dict[str, Any], artist_id: int) -> Optional[int]:
    """
    Insert an album record into the 'albums' table, linked to a given artist.

    Args:
        cursor: Active psycopg2 cursor.
        album (Dict[str, Any]): Dictionary containing album metadata.
        artist_id (int): ID of the artist the album belongs to.

    Returns:
        Optional[int]: The inserted album's ID, or None if the album already exists.
    """
    # Execute the INSERT with conflict resolution on (name, artist_id)
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

    # Retrieve the album ID if it was inserted, otherwise return None
    result = cursor.fetchone()
    return result[0] if result else None


def insert_tracks(cursor, tracks: List[Dict[str, Any]], album_id: int) -> None:
    """
    Bulk insert track records into the 'tracks' table for a given album.

    Args:
        cursor: Active psycopg2 cursor.
        tracks (List[Dict[str, Any]]): List of track metadata dictionaries.
        album_id (int): ID of the album to which the tracks belong.
    """
    # Prepare cleaned values for each track, converting NumPy to native Python types
    values = [(
        to_python_type(t["name"]),
        to_python_type(album_id),
        to_python_type(t["track_number"]),
        to_python_type(t["duration_ms"]),
        to_python_type(t["explicit"]),
        to_python_type(t["popularity"])
    ) for t in tracks]

    # Bulk insert using psycopg2's execute_values for performance
    # Conflict resolution ensures no duplicate (name, album_id) pairs are inserted
    execute_values(cursor, """
        INSERT INTO tracks (name, album_id, track_number, duration_ms, explicit, popularity)
        VALUES %s
        ON CONFLICT (name, album_id) DO NOTHING;
    """, values)


def get_track_name_to_id(cursor, album_id: int) -> Dict[str, int]:
    """
    Retrieve a mapping of track names to their IDs for a given album.

    Args:
        cursor: Active psycopg2 cursor.
        album_id (int): The ID of the album whose tracks should be queried.

    Returns:
        Dict[str, int]: Dictionary mapping track names to their corresponding database IDs.
    """
    # Fetch all track IDs and names associated with the album
    cursor.execute("SELECT id, name FROM tracks WHERE album_id = %s", (album_id,))

    # Build a name → id dictionary from the result
    return {name: tid for tid, name in cursor.fetchall()}


def insert_lyrics(cursor, tracks: List[Dict[str, Any]], track_name_to_id: Dict[str, int]) -> None:
    """
    Insert lyrics for a list of tracks into the 'lyrics' table.

    Args:
        cursor: Active psycopg2 cursor.
        tracks (List[Dict[str, Any]]): List of track dictionaries with 'name' and 'lyrics'.
        track_name_to_id (Dict[str, int]): Mapping of track names to their database IDs.
    """
    for t in tracks:
        # Retrieve the track ID using the track name
        track_id = track_name_to_id.get(t["name"])

        # Skip if no matching track ID was found (likely due to naming mismatch)
        if not track_id:
            print(f"  ⚠️ No match for lyrics: {t['name']}")
            continue

        # Insert the lyrics into the lyrics table with NULL values for scores (to be computed later)
        cursor.execute("""
            INSERT INTO lyrics (track_id, text, readability_score, sentiment_score)
            VALUES (%s, %s, NULL, NULL)
            ON CONFLICT (track_id) DO NOTHING;
        """, (track_id, to_python_type(t["lyrics"])))


# ====================
# === MAIN ROUTINE ===
# ====================

def main() -> None:
    """
    CLI to load cleaned data from the 'processed' directory into PostgreSQL.

    This tool:
    - Connects to the database and creates required tables.
    - Prompts for artist names to load their processed data.
    - Inserts artist, album, track, and lyric records into the database.
    - Logs skipped or invalid albums.
    """
    # Establish database connection and initialize schema
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SET search_path TO public;")
    create_tables(cursor)
    conn.commit()

    # Prepare logging for skipped albums
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(f"logs/skipped_albums_{timestamp}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w", encoding="utf-8")

    print("\n🚀 PostgreSQL Loader (multi-artist mode)")

    while True:
        # Prompt user for artist name
        artist = input("\n🎤 Enter artist name to load (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting loader. Goodbye!")
            break

        # Check for processed artist directory and merged metadata
        artist_dir = PROCESSED_DIR / artist
        artist_csv = artist_dir / f"{artist}_merged_metadata.csv"
        if not artist_csv.exists():
            print(f"⚠️ No metadata for: {artist}")
            continue

        # Parse artist metadata and insert into database
        artist_data = parse_artist_csv(artist_csv)
        artist_id = insert_artist(cursor, artist_data)

        # If already exists, retrieve artist ID
        if not artist_id:
            cursor.execute("SELECT id FROM artists WHERE name = %s", (to_python_type(artist_data["name"]),))
            result = cursor.fetchone()
            artist_id = result[0] if result else None

        if not artist_id:
            print("❌ Could not insert or retrieve artist ID.")
            continue

        # Iterate over album folders for the artist
        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir() or not is_valid_album_name(album_dir.name):
                log_file.write(f"{artist}/{album_dir.name}\n")
                continue

            # Process each *_final.csv file inside the album folder
            for file in album_dir.glob("*_final.csv"):
                album_data, tracks = parse_album_csv(file)
                album_id = insert_album(cursor, album_data, artist_id)

                # If already exists, retrieve album ID
                if not album_id:
                    cursor.execute("SELECT id FROM albums WHERE name = %s AND artist_id = %s", (
                        to_python_type(album_data["name"]), to_python_type(artist_id)))
                    result = cursor.fetchone()
                    album_id = result[0] if result else None

                if not album_id:
                    print("❌ Could not insert or retrieve album ID.")
                    continue

                # Insert track records and lyrics for this album
                insert_tracks(cursor, tracks, album_id)
                track_ids = get_track_name_to_id(cursor, album_id)
                insert_lyrics(cursor, tracks, track_ids)

                # Commit all changes for this album
                conn.commit()

    # Clean up resources
    cursor.close()
    log_file.close()
    conn.close()
    print("\n✅ Load complete.")


if __name__ == "__main__":
    main()