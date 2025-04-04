import psycopg2
from psycopg2.extras import execute_values
import numpy as np

def to_python_type(val):
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val


def insert_artist(cursor, artist_data):
    cursor.execute("""
        INSERT INTO artists (
            name, birth_name, birth_date, birth_place, country,
            active_years, genres, instruments, vocal_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, birth_date) DO NOTHING
        RETURNING id;
    """, (
        to_python_type(artist_data["name"]),
        to_python_type(artist_data["birth_name"]),
        to_python_type(artist_data["birth_date"]),
        to_python_type(artist_data["birth_place"]),
        to_python_type(artist_data["country"]),
        to_python_type(artist_data["active_years"]),
        to_python_type(artist_data["genres"]),
        to_python_type(artist_data["instruments"]),
        to_python_type(artist_data["vocal_type"])
    ))
    result = cursor.fetchone()
    return result[0] if result else None




def insert_album(cursor, album_data, artist_id):
    cursor.execute("""
        INSERT INTO albums (name, artist_id, release_date, popularity)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name, artist_id) DO NOTHING
        RETURNING id;
    """, (
        to_python_type(album_data["name"]),
        to_python_type(artist_id),
        to_python_type(album_data["release_date"]),
        to_python_type(album_data["popularity"])
    ))
    result = cursor.fetchone()
    return result[0] if result else None


def insert_tracks(cursor, tracks_data, album_id):
    track_values = []
    for track in tracks_data:
        track_values.append((
            to_python_type(track["name"]),
            to_python_type(album_id),
            to_python_type(track["track_number"]),
            to_python_type(track["duration_ms"]),
            to_python_type(track["explicit"]),
            to_python_type(track["popularity"])
        ))

    execute_values(cursor, """
        INSERT INTO tracks (name, album_id, track_number, duration_ms, explicit, popularity)
        VALUES %s
        ON CONFLICT (name, album_id) DO NOTHING;
    """, track_values)

def get_track_name_to_id(cursor, album_id):
    """
    Return a dictionary mapping track names to their database IDs for a given album.

    Args:
        cursor: psycopg2 cursor object.
        album_id: The ID of the album to fetch tracks for.

    Returns:
        dict: {track_name: track_id}
    """
    cursor.execute("""
        SELECT id, name FROM tracks WHERE album_id = %s;
    """, (album_id,))

    return {name: track_id for track_id, name in cursor.fetchall()}


def insert_lyrics(cursor, tracks_data, track_name_to_id):
    for track in tracks_data:
        track_name = track["name"]
        track_id = track_name_to_id.get(track_name)

        if track_id is None:
            print(f"⚠️ No match for track '{track_name}' when inserting lyrics.")
            continue

        lyrics_text = to_python_type(track.get("lyrics"))

        cursor.execute("""
            INSERT INTO lyrics (track_id, text, readability_score, sentiment_score)
            VALUES (%s, %s, NULL, NULL)
            ON CONFLICT (track_id) DO NOTHING;
        """, (
            to_python_type(track_id),
            lyrics_text
        ))




