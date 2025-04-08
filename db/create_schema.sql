-- ==========================================
-- Scrape-The-Verse: PostgreSQL DB Schema
-- This script defines all tables needed for
-- storing artist metadata, albums, tracks,
-- lyrics, and word frequency analysis.
-- ==========================================

-- === ARTISTS TABLE ===
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

-- === ALBUMS TABLE ===
CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    artist_id INTEGER REFERENCES artists(id),
    release_date DATE,
    popularity INTEGER,
    UNIQUE (name, artist_id)
);

-- === TRACKS TABLE ===
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

-- === LYRICS TABLE ===
CREATE TABLE IF NOT EXISTS lyrics (
    track_id INTEGER PRIMARY KEY REFERENCES tracks(id),
    text TEXT,
    readability_score REAL,
    sentiment_score REAL,
    word_count INTEGER,
    line_count INTEGER,
    char_count INTEGER,
    lexical_density REAL
);

-- === WORD FREQUENCIES BY TRACK ===
CREATE TABLE IF NOT EXISTS word_frequencies_track (
    track_id INTEGER REFERENCES tracks(id),
    artist TEXT,
    album TEXT,
    track_name TEXT,
    word TEXT,
    count INTEGER,
    UNIQUE (track_id, word)
);

-- === WORD FREQUENCIES BY ALBUM ===
CREATE TABLE IF NOT EXISTS word_frequencies_album (
    artist TEXT,
    album TEXT,
    word TEXT,
    count INTEGER,
    UNIQUE (artist, album, word)
);
