import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the .env file in the project root
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path)

def connect_db():
    """
    Establish a connection to the PostgreSQL database using environment variables.

    Returns:
        psycopg2.extensions.connection: A connection object to interact with the database.
    """
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432)
    )

def create_tables(cursor):
    """
    Create the necessary tables in the PostgreSQL database if they do not already exist.

    Args:
        cursor (psycopg2.extensions.cursor): A database cursor object.
    """
    cursor.execute("""
        -- Table: artists (Spotify + Wikidata)
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

        -- Table: albums (Spotify)
        CREATE TABLE IF NOT EXISTS albums (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            artist_id INTEGER REFERENCES artists(id),
            release_date DATE,
            popularity INTEGER,
            UNIQUE (name, artist_id)
        );

        -- Table: tracks (Spotify)
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

        -- Table: lyrics (Genius)
        CREATE TABLE IF NOT EXISTS lyrics (
            track_id INTEGER PRIMARY KEY REFERENCES tracks(id),
            text TEXT,
            readability_score REAL,
            sentiment_score REAL
        );
    """)
