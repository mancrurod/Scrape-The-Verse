# 🧠 Project Overview

This page explains the architecture and logic behind the **Scrape The Verse** ETL pipeline.

---

## 🏗️ Pipeline Architecture

```
Spotify API ─────┐
                 │
Genius API ──────┼──► [Extraction] ─► [Transformation] ─► [Processing] ─► [Analysis] ─► [Load to PostgreSQL]
                 │
Wikidata API ────┘
```

Each source has its own extraction and transformation logic. All data is eventually merged and loaded into a relational database.

---

## 📁 Project Structure

```
src/
├── extraction/       # Scrapers for Spotify, Genius, Wikidata
├── transformation/   # Cleaning and formatting data
├── process/          # Match lyrics to tracks
├── analysis/         # NLP: readability, sentiment, frequency
├── load/             # PostgreSQL schema and loader

data/
├── raw/              # Raw downloaded data
├── transformations/  # Cleaned CSVs
├── processed/        # Final datasets (lyrics + metadata)
├── logs/             # Logs of missing or failed items
```

---

## 🧩 Key Concepts

- **Multi-source integration**: Combines musical, textual, and biographical data
- **Lyrics mapping**: Matches Genius lyrics to Spotify songs with fuzzy matching
- **Text analysis**: Measures readability, sentiment, lexical density
- **Word clouds**: Generates word frequency data by track and album
- **PostgreSQL schema**: Normalized DB ready for queries and dashboards

---

## 📊 Final Output

Data is stored in a PostgreSQL database, including:

- Artist and album metadata
- Track-level info
- Clean lyrics
- Word frequencies
- Sentiment and readability metrics

Ready to be explored in SQL or Power BI.