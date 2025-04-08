# 🧠 Project Overview

**Scrape The Verse** is a full-featured ETL and NLP pipeline that builds an analyzable dataset of lyrics and metadata for music artists, combining Spotify, Genius, and Wikidata sources.

---

## 🎯 Goals

- Analyze songwriting quality with NLP and literary metrics
- Compare artists (e.g. Dylan vs Swift) on structure, vocabulary, sentiment
- Prepare data for dashboards, machine learning, and visualizations

---

## 🧱 Architecture

```
[Spotify API] ─┐
              ├──► [Extract] ─┐
[Genius API] ──┘             ├──► [Transform] ─┐
[Wikidata API] ─────────────┘                ├──► [Process Lyrics + Metadata] ─┐
                                             │                                 │
                                             └────────► [Load to PostgreSQL] ─► [Analyze]
```

---

## 🧩 Components

### 🟦 Extraction (`src/extraction`)
- `spotify_extraction.py`: track + album data
- `genius_extraction.py`: lyrics by album
- `wikidata_extraction.py`: biography, genres, instruments

### 🟨 Transformation (`src/transformation`)
- Cleans + standardizes Spotify and Genius metadata
- Merges Wikidata + Spotify at the artist level

### 🟩 Processing (`src/processing/process.py`)
- Fuzzy-match lyrics to tracks
- Joins lyrics + song metadata
- Logs missing + matched lyrics

### 🟥 Loading (`src/load/load.py`)
- PostgreSQL loader with full schema creation
- Type coercion, conflict resolution

### 🟪 Analysis (`src/analysis/analyze_lyrics.py`)
- Sentiment (VADER)
- Readability (Flesch)
- Lexical density
- Word/line/character counts
- Word frequency tables (track + album)

---

## 🧰 Tools & Technologies

- **Python 3.10**
- `spotipy`, `lyricsgenius`, `wikipedia-api`
- `spaCy`, `nltk`, `textstat`, `transformers`
- `psycopg2-binary`, PostgreSQL 14+
- `pandas`, `dotenv`, `tqdm`

---

## 🧪 Testing & Reproducibility

- Fully typed functions (`List`, `Dict`, `Optional`, `Tuple`)
- CLI-driven scripts for all stages
- Logs written to `/logs/`
- External dependencies documented in `requirements.txt`

---

## ✅ Output

- Clean CSVs (raw, transformed, processed)
- Fully populated PostgreSQL database
- NLP-enriched lyrics table
- Word frequency tables for NLP or visualization

