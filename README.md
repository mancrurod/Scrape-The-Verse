# 🎶 Scrape The Verse

*Because sometimes the API gives you nothing, and you still need to know what track 3 on “Red (Taylor’s Version)” is about.*


> 📚 This project is a data-driven investigation into a simple but profound question:  
> **Can Taylor Swift win the Nobel Prize in Literature?**  
> (Spoiler: if Bob Dylan did, why not her?)

> *“There’s no success like failure, and failure’s no success at all.”*  
> — Bob Dylan

> *“I want to be defined by the things that I love.”*  
> — Taylor Swift

---

## 🚀 What is this?

**Scrape The Verse** is a modular Python project for scraping both **Spotify metadata** and **Genius lyrics** — by artist, by album, or in batch. It's designed to keep your scraping organized, retry failed requests, and give you clean data to play with.

Built to handle cases like:
- You want all Bob Dylan albums in a structured folder with tracklists and metadata ✅  
- You want all Taylor Swift lyrics saved as `.txt` files for a specific album ✅  
- You need to retry that one album that failed because Genius was feeling moody ✅

Yes — this is overkill. But it’s fun.

---


## 🧠 Project Status

**WIP** – Work in Progress. This project is evolving into a full **ETL pipeline**.

What we got so far:

- ✅ Modularized scraping system
- ✅ Batch support (multiple albums, multiple artists)
- ✅ Local caching of downloads
- ✅ Logging for retrying failed albums or songs

Planned and ongoing components:
- ⏳ Data cleaning (normalize casing, remove duplicates, handle typos)
- ⏳ Data merging (match Spotify tracks with Genius lyrics)
- ⏳ Load to database (likely SQLite or PostgreSQL)
- ⏳ Data visualization (dashboards, word frequency, sentiment?)
- ❌ No full tests yet
- ❌ No CLI or frontend (yet)

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

This scraper keeps things tidy. You’ll get:

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

---

## 🧪 Usage

> “Don't think twice, just run the script.”

### 🎤 Genius (lyrics)

Run the batch mode (predefined artists and albums):

```bash
python -m src.scraping.GENIUS.main_genius_scrap
```

It'll scrape albums from artists like **Taylor Swift** and **Bob Dylan**, one by one. Lyrics go into `.txt` files, summaries into `.csv`.

### 🎧 Spotify (metadata)

Interactive mode:

```bash
python -m src.scraping.SPOTIFY.main_spoty_scrap
```

Retry mode (albums that failed previously):

```bash
python -m src.scraping.SPOTIFY.retry_failed_albums
```

---

## ⚠️ Important Notes

- Always run the modules **from the project root** with `python -m ...`
- Requires a `.env` file with credentials:
  - `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI`
  - `GENIUS_CLIENT_ACCESS_TOKEN`

---

## 🧰 Requirements

- Python 3.10+
- `spotipy`, `lyricsgenius`, `requests`, `beautifulsoup4`, `python-dotenv`

Install with:

```bash
pip install -r requirements.txt
```

---

## 🧵 Why?

Because scraping lyrics by hand is boring. Because APIs are flaky.  
Because we once lost all lyrics from “Blonde on Blonde” in a crash.  
And because if Dylan got a Nobel, we want the **data** to argue Swift could, too.  

---

## 🛠 To Do

This project is focused on one question: **Can Taylor Swift win the Nobel Prize in Literature?**  
The ETL pipeline will support that goal by enabling structured, analyzable lyric and metadata collection.

- [ ] Data cleaning (remove noise, normalize titles and structure)
- [ ] Data merging (align Genius lyrics with Spotify track data)
- [ ] Load to database for querying and cross-analysis
- [ ] Build visualizations (lyric patterns, complexity, sentiment)
- [ ] Final output: interactive or printable “lyricsbook”
- [ ] Unit tests and robust error handling

---

## 🤝 Contributing

Pull requests are welcome. Just don’t start a flame war about which Dylan era is better.

---

## ✨ Credits

Built by a language-loving dev with an unhealthy playlist history.  
Helped by ChatGPT. Inspired by verses.

> “You’re on your own, kid — but the script runs fine.”  
> — T. Swift, sort of.