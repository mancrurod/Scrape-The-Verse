
# 🎶 Scrape The Verse

*He wrote “Tangled Up in Blue,” she wrote “The Story of Us” — we wrote the code to ask if Swift could follow Dylan to Stockholm.*

> 📚 This project is a full-blown, ETL-powered attempt to answer one brilliant, nerdy, and slightly unhinged question:  
> **Can Taylor Swift win the Nobel Prize in Literature?**  
> (Spoiler: if Bob Dylan did, why not her?)

> *“There’s no success like failure, and failure’s no success at all.”*  
> — Bob Dylan

> *“I want to be defined by the things that I love.”*  
> — Taylor Swift

---

## 🚀 What is this?

**Scrape The Verse** is a modular Python project for scraping **Spotify metadata** and **Genius lyrics** — by artist, album, or batch — with one literary mission in mind:  
Build a clean, analyzable, structured dataset that helps us explore Taylor Swift’s lyrics like a Nobel committee might.

This is more than scraping. It’s data for a cultural argument.

Think of it as building the corpus for a PhD dissertation that never got written… until now.

---

## 🧠 Project Status

**WIP** – This is a growing **ETL pipeline** for comparing Taylor Swift's songwriting to Bob Dylan's — the only musician to win the Nobel Prize in Literature.

What we’ve got:

- ✅ Modular scraping (Spotify + Genius)
- ✅ Batch support (multiple artists, albums)
- ✅ Local file caching
- ✅ Logging for retrying failed scrapes

What’s coming:

- ⏳ Clean & normalize text data (titles, casing, typos)
- ⏳ Merge metadata + lyrics (align tracks)
- ⏳ Load into a queryable database (SQLite/PostgreSQL)
- ⏳ Explore lyric complexity, sentiment, word patterns
- ⏳ Visualize trends across albums and eras
- ❌ Tests, CLI, and UI — still on the dream board

---

## 🕵️ The Mission

This isn’t just a scraper. It’s a toolkit to build an argument with data.

We want to know:
- How do Taylor’s lyrics evolve over time?
- Is her storytelling comparable to Dylan’s?
- What poetic devices show up in her writing?
- Can data defend pop as literature?

Whether you're a Swiftie, a skeptic, or just like playing with Python, the goal is the same:
**Put the lyrics under a microscope and see what we find.**

---

## 🗂 Folder Structure (simplified)

```
src/
└── scraping/
    ├── GENIUS/
    │   ├── auth.py
    │   ├── fetch.py
    │   ├── lyrics.py
    │   ├── logging.py
    │   ├── storage.py
    │   ├── utils.py
    │   └── main_genius_scrap.py
    └── SPOTIFY/
        ├── auth.py
        ├── albums.py
        ├── artist.py
        ├── fetch.py
        ├── logging.py
        ├── storage.py
        ├── utils.py
        ├── main_spoty_scrap.py
        └── retry_failed_albums.py
```

---

## 📁 Output Files

```
raw/
├── GENIUS/
│   └── {artist}/{album}/
│       ├── song1.txt
│       ├── song2.txt
│       └── album_summary.csv
└── SPOTIFY/
    └── {artist}/{album}/
        ├── album_metadata.csv
        ├── tracks.csv
        └── ../artist_metadata.csv
logs/
    ├── failed_lyrics_YYYY-MM-DD.log
    └── failed_albums_YYYY-MM-DD.log
```

Everything organized so your future self (or your thesis advisor) will thank you.

---

## 🧪 Usage

> “Don't think twice, just run the script.”

### 🎤 Genius (lyrics)

```bash
python -m src.scraping.GENIUS.main_genius_scrap
```

Scrapes lyrics from predefined albums/artists (yes, Taylor is in there). Outputs `.txt` and `.csv`.

### 🎧 Spotify (metadata)

```bash
python -m src.scraping.SPOTIFY.main_spoty_scrap
```

Interactive — give it artists and albums, and it gives you track/album/artist metadata.

### ♻️ Retry failed albums

```bash
python -m src.scraping.SPOTIFY.retry_failed_albums
```

Genius or Spotify flaked out? This handles retries based on log files.

---

## ⚠️ Setup

1. Run scripts **from the project root** with `python -m ...`
2. Create a `.env` file with the following:

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

## 🛠 To Do

The ETL is in motion — here’s what’s next on the roadmap:

- [ ] Normalize and clean lyric text
- [ ] Match Genius lyrics with Spotify metadata
- [ ] Load everything into a database for analysis
- [ ] Build visualizations (sentiment, complexity, themes)
- [ ] Bonus: generate an interactive “LyricsBook”?
- [ ] Add unit tests and robust exception handling

---

## 🤝 Contributing

Pull requests welcome. Especially from Swifties with SQL skills.  
Just… don’t fight about *Reputation* vs *Red* in the issues.

---

## ✨ Credits

Built by a language nerd with an overactive playlist.  
Inspired by literature, lyrics, and one very specific Nobel Prize.

> “You’re on your own, kid — but the script runs fine.”  
> — T. Swift, sort of.
