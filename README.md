# 🎶 Scrape The Verse

*He wrote “Tangled Up in Blue,” she wrote “The Story of Us”—we wrote the code to ask if Swift could follow Dylan to Stockholm.*

> 📚 This project is a full-blown, ETL-powered attempt to answer one brilliant, nerdy, and slightly unhinged question:  
> **Can Taylor Swift win the Nobel Prize in Literature?**  
> (Spoiler: if Bob Dylan did, why not her?)

> *“There’s no success like failure, and failure’s no success at all.”*  
> — Bob Dylan

> *“I want to be defined by the things that I love.”*  
> — Taylor Swift

---

## 🚀 What is this?

**Scrape The Verse** is a modular Python project for scraping **Spotify metadata**, **Genius lyrics**, and **Wikidata metadata**—by artist, album, or batch—with one literary mission in mind:  
Build a clean, analyzable, structured dataset that helps us explore Taylor Swift’s lyrics like a Nobel committee might.

This is more than scraping. It’s data for a cultural argument.

Think of it as building the corpus for a PhD dissertation that never got written… until now.

---

## 🧠 Project Status

**WIP** – This is a growing **ETL pipeline** for comparing Taylor Swift's songwriting to Bob Dylan's—the only musician to win the Nobel Prize in Literature.

What we’ve got:

- ✅ Modular scraping (Spotify, Genius, Wikidata)
- ✅ Batch support (multiple artists, albums)
- ✅ Local file caching
- ✅ Logging for retrying failed scrapes
- ✅ Lyrics text normalization and cleaning
- ✅ Matching Genius lyrics with Spotify metadata
- ✅ Matching Spotify artist metadata with Wikidata metadata

What’s coming:

- ⏳ Load into a queryable database (SQLite/PostgreSQL)
- ⏳ Explore lyric complexity, sentiment, word patterns
- ⏳ Visualize trends across albums and eras
- ❌ Tests, CLI, and UI — still on the dream board

---

## 🗂 Folder Structure (simplified)

```
src/
├── scrape/
│   ├── GENIUS/
│   │   ├── auth.py
│   │   ├── fetch.py
│   │   ├── lyrics.py
│   │   ├── logging.py
│   │   ├── storage.py
│   │   ├── utils.py
│   │   └── main_genius_scrap.py
│   ├── SPOTIFY/
│   │   ├── auth.py
│   │   ├── albums.py
│   │   ├── artist.py
│   │   ├── fetch.py
│   │   ├── logging.py
│   │   ├── storage.py
│   │   ├── utils.py
│   │   ├── main_spoty_scrap.py
│   │   └── retry_failed_albums.py
│   └── WIKIDATA/
│       ├── fetch.py
│       ├── logging.py
│       ├── storage.py
│       ├── utils.py
│       └── main_wikidata_scrap.py
├── transform/
│   ├── GENIUS/
│   ├── SPOTIFY/
│   └── WIKIDATA/
├── processing/
└── utils/
```

---

## 🧪 Usage

> “Don't think twice, just run the script.”

### 🎤 Genius (lyrics)

```bash
python -m src.scrape.GENIUS.main_genius_scrap
```

### 🎧 Spotify (metadata)

```bash
python -m src.scrape.SPOTIFY.main_spoty_scrap
```

### 🌐 Wikidata (artist metadata)

```bash
python -m src.scrape.WIKIDATA.main_wikidata_scrap
```

### ♻️ Retry failed albums

```bash
python -m src.scrape.SPOTIFY.retry_failed_albums
```

---

## ⚠️ Setup

Run scripts **from the project root** with `python -m ...`

Create a `.env` file with:

```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=...
GENIUS_CLIENT_ACCESS_TOKEN=...
```

---

## 🧰 Requirements

- Python 3.10+
- `spotipy`, `lyricsgenius`, `requests`, `beautifulsoup4`, `python-dotenv`

Install everything with:

```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

Pull requests welcome. Especially from Swifties with SQL skills.  
Just… don’t fight about *Reputation* vs *Red* in the issues.

---

## ✨ Credits

Built by a language nerd with an overactive playlist.  
Inspired by literature, lyrics, and one very specific Nobel Prize.

> “You’re on your own, kid—but the script runs fine.”  
> — T. Swift, sort of.

