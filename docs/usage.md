# ▶️ Usage Guide

This document describes how to use the Scrape The Verse pipeline, step by step.

---

## 📁 Folder Setup

Before running any scripts, make sure your folder tree looks like this:

```
project-root/
├── raw/
│   ├── GENIUS/
│   ├── SPOTIFY/
│   └── WIKIDATA/
├── transformations/
├── processed/
├── logs/
├── db/
│   └── create_schema.sql
├── .env
├── requirements.txt
└── src/
    ├── extraction/
    ├── transformation/
    ├── processing/
    ├── load/
    └── analysis/
```

---

## ⛏️ Extract

Scrape raw data from Spotify, Genius, and Wikidata.

```bash
# Spotify artist, albums, tracks
python src/extraction/spotify_extraction.py

# Genius lyrics by album
python src/extraction/genius_extraction.py

# Wikidata artist metadata
python src/extraction/wikidata_extraction.py
```

---

## 🧼 Transform

Clean and restructure the extracted data.

```bash
# Clean Spotify metadata
python src/transformation/spotify_transformation.py

# Clean Genius lyrics (.txt files)
python src/transformation/genius_transformation.py

# Merge Spotify + Wikidata at artist level
python src/transformation/wikidata_transformation.py
```

---

## 🔗 Process

Match Genius lyrics to Spotify songs (fuzzy matching).

```bash
python src/processing/process.py
```

This will output:
- `processed/<artist>/<album>_final.csv`
- Matched/missing lyrics logs

---

## 💾 Load

Load all processed data into PostgreSQL.

```bash
python src/load/load.py
```

This creates and populates all tables:
- `artists`, `albums`, `tracks`, `lyrics`
- `word_frequencies_track`, `word_frequencies_album`

---

## 📊 Analyze

Run NLP metrics and generate word frequencies.

```bash
python src/analysis/analyze_lyrics.py
```

This updates lyrics table with:
- Sentiment
- Readability
- Word/line/char counts
- Lexical density
- Word frequencies by track & album

---

## 🔁 Run it all again

You can rerun any phase with new artists or albums.  
The pipeline is modular and idempotent where possible.

---

Now go explore the poetic potential of pop.

