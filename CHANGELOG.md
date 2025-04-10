# 📦 Changelog

All notable changes to this project are documented in this file.

## [1.1.0] - 2025-04-10

### ✨ Highlights

- Enhanced user-facing documentation with demo media and creative branding
- Fixed extraction bug in Genius pipeline
- Strengthened identity and readability of the project

### 🚀 New Features

- 📸 Added `docs/gifs/` folder with animated ETL stage demos
- 🪄 Embedded visual walkthroughs directly in `README.md` using GIFs

### 🛠️ Refactors

- Rewrote `README.md` with Dylan/Swift-themed subtitles for each section
- Reorganized project badges for clarity and logical grouping
- Improved structure of "Contributing" and "Credits" sections with clever tone

### 🐛 Fixes

- Fixed issue in `src/extraction/genius_extraction.py` affecting lyric retrieval

### 📚 Documentation

- Added badge for project status (`Status: Stable`)
- Updated badges layout to follow best practices
- Extended commit message to reflect visual and functional changes

---

## [1.0.0] - 2025-04-08

### ✨ Highlights

- Complete codebase refactor and modularization
- Full ETL pipeline implemented with clear separation of concerns
- PostgreSQL integration with robust schema
- NLP analysis with readability, sentiment, lexical stats and word frequency

### 🚀 New Features

- Modular scripts for:
  - Spotify, Genius, Wikidata scraping (`src/extraction/`)
  - Data transformation and merging (`src/transformation/`)
  - Lyrics processing and matching (`src/processing/`)
  - PostgreSQL loading (`src/load/`)
  - NLP analysis (`src/analysis/analyze_lyrics.py`)

- CLI-based interfaces for all phases
- Static typing (`List`, `Dict`, `Optional`, etc.) throughout the code
- Batch logging for lyrics matched/missing
- Smart handling of missing or malformed files

### 🛠️ Refactors

- All functions documented with English docstrings
- Clean separation between logic layers
- File structure aligned with SOLID principles
- Logging and CSV outputs organized by artist/album

### 📚 Documentation

- Updated `README.md` to reflect pipeline, usage and structure
- Updated `docs/`:
  - `installation.md`
  - `overview.md`
  - `usage.md`
- Structured `requirements.txt` with grouped, versioned dependencies

### 🧪 Improvements

- Dependency validation (NLTK, spaCy)
- Idempotent execution for all pipeline stages
- Compatibility with DBeaver and CLI PostgreSQL clients

---

## [0.1.0] - 2024-11-20

- Initial script for Spotify scraping using `spotipy`
- Basic lyrics retrieval via `lyricsgenius`
- Manual merging of tracks and lyrics
- First iteration of CSV output per album

