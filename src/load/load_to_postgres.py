import os
import psycopg2
import pandas as pd
from pathlib import Path

def connect_db():
    """
    Establish a connection to the PostgreSQL database.

    Returns:
        psycopg2.connection: A connection object to the database.
    """
    return psycopg2.connect(**DB_PARAMS)

def create_tables(cursor):
    """
    Create the necessary tables in the database if they do not already exist.

    Args:
        cursor (psycopg2.cursor): A cursor object to execute SQL commands.
    """
    # Create the 'artists' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        spotify_id TEXT UNIQUE,
        wikidata_qid TEXT,
        birth_name TEXT,
        birth_date DATE,
        birth_place TEXT,
        country TEXT,
        career_start_year INTEGER,
        genres TEXT,
        instruments TEXT,
        vocal_type TEXT
    );
    """)

    # Create the 'albums' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS albums (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        artist_id INTEGER REFERENCES artists(id),
        release_date DATE,
        popularity INTEGER,
    );
    """)

    # Create the 'tracks' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        spotify_id TEXT,
        album_id INTEGER REFERENCES albums(id),
        track_number INTEGER,
        duration_ms INTEGER,
        explicit BOOLEAN,
        popularity INTEGER
    );
    """)

    # Create the 'lyrics' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lyrics (
        track_id INTEGER PRIMARY KEY REFERENCES tracks(id),
        text TEXT,
        readability_score REAL,
        sentiment_score REAL
    );
    """)


def insert_artist(cursor, artist_csv):
    df = pd.read_csv(artist_csv)
    row = df.iloc[0]

    # Comprobamos si ya existe el artista
    cursor.execute("SELECT id FROM artists WHERE name = %s;", (row["Name"],))
    result = cursor.fetchone()
    if result:
        print(f"ℹ️ Artista ya existe en la base de datos: {row['Name']}")
        return result[0]

    # Insertar nuevo artista
    cursor.execute("""
    INSERT INTO artists (
        name, birth_name, birth_date, birth_place, country,
        career_start_year, genres, instruments, vocal_type
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    RETURNING id;
    """, (
        row["Name"], row["BirthName"], row["DateOfBirth"], row["PlaceOfBirth"], row["CountryOfCitizenship"],
        row["WorkPeriodStart"], f"{row['GenresWikidata']}, {row['GenresSpotify']}", row["Instruments"], row["VoiceType"]
    ))
    artist_id = cursor.fetchone()[0]
    print(f"✅ Insertado nuevo artista: {row['Name']} (ID: {artist_id})")
    return artist_id


def insert_album(cursor, df_album, artist_id):
    album_name = df_album["AlbumName"].iloc[0]
    release_date = df_album["ReleaseDateAlbum"].iloc[0]
    popularity = df_album["AlbumPopularity"].iloc[0]

    # Comprobar si el álbum ya existe
    cursor.execute("SELECT id FROM albums WHERE name = %s AND artist_id = %s;", (album_name, artist_id))
    result = cursor.fetchone()
    if result:
        print(f"ℹ️ Álbum ya existe: {album_name}")
        return result[0]

    # Insertar nuevo álbum
    cursor.execute("""
    INSERT INTO albums (name, artist_id, release_date, popularity)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """, (
        album_name, artist_id, release_date, popularity
    ))
    album_id = cursor.fetchone()[0]
    print(f"✅ Insertado álbum: {album_name} (ID: {album_id})")
    return album_id


def insert_tracks(cursor, df_album, album_id):
    for _, row in df_album.iterrows():
        song_name = row["SongName"]
        track_number = row["TrackNumber"]
        duration_ms = row["DurationMs"]
        explicit = row["Explicit"]
        popularity = row["SongPopularity"]

        # Comprobar si la canción ya existe
        cursor.execute("SELECT id FROM tracks WHERE name = %s AND album_id = %s;", (song_name, album_id))
        result = cursor.fetchone()
        if result:
            print(f"  ℹ️ Canción ya existe: {song_name}")
            continue

        # Insertar canción
        cursor.execute("""
        INSERT INTO tracks (name, album_id, track_number, duration_ms, explicit, popularity)
        VALUES (%s, %s, %s, %s, %s, %s);
        """, (song_name, album_id, track_number, duration_ms, explicit, popularity))
        print(f"  ✅ Canción insertada: {song_name}")


def insert_lyrics(cursor, df_album):
    for _, row in df_album.iterrows():
        song_name = row["SongName"]
        lyrics = row.get("Lyrics", "")

        # Buscar el track_id por nombre y número de pista (para precisión)
        cursor.execute("SELECT id FROM tracks WHERE name = %s AND track_number = %s;", (song_name, row["TrackNumber"]))
        result = cursor.fetchone()
        if not result:
            print(f"  ⚠️ No se encontró la canción para insertar letra: {song_name}")
            continue

        track_id = result[0]

        # Verificar si ya existen letras
        cursor.execute("SELECT 1 FROM lyrics WHERE track_id = %s;", (track_id,))
        if cursor.fetchone():
            print(f"  ℹ️ Letra ya existe para: {song_name}")
            continue

        cursor.execute("""
        INSERT INTO lyrics (track_id, text, readability_score, sentiment_score)
        VALUES (%s, %s, NULL, NULL);
        """, (track_id, lyrics))
        print(f"  📝 Letra insertada para: {song_name}")


def main():
    conn = connect_db()
    cursor = conn.cursor()
    create_tables(cursor)
    conn.commit()
    print("✅ Tablas creadas (si no existían)")

    base_path = Path("processed")
    if not base_path.exists():
        print("❌ No se encuentra la carpeta 'processed'.")
        return

    print("📂 Recorriendo artistas...")
    for artist_dir in base_path.iterdir():
        if not artist_dir.is_dir():
            continue

        print(f"🎤 Procesando artista: {artist_dir.name}")

        artist_metadata_file = artist_dir / f"{artist_dir.name}_merged_metadata.csv"
        if artist_metadata_file.exists():
            print(f"📄 Encontrado metadata de artista: {artist_metadata_file.name}")
            artist_id = insert_artist(cursor, artist_metadata_file)
        else:
            print(f"⚠️ No se encontró metadata para {artist_dir.name}")
            continue

        for album_dir in artist_dir.iterdir():
            if not album_dir.is_dir():
                continue
            for file in album_dir.glob("*_final.csv"):
                print(f"📀 Encontrado CSV de álbum: {file.name}")
                # Aquí se cargará el contenido de cada álbum

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
