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

**Scrape The Verse** is a modular Python project for scraping and processing **Spotify metadata**, **Genius lyrics**, and **Wikidata metadata**—by artist and album—with one literary mission in mind:  
Build a clean, analyzable, structured dataset that helps us explore Taylor Swift’s lyrics like a Nobel committee might.

---

## 🧠 Project Status

**Stable** – This is a complete **ETL pipeline** for comparing Taylor Swift's songwriting to Bob Dylan's—the only musician to win the Nobel Prize in Literature.

What we’ve got:

- ✅ Modular and interactive scraping (Spotify, Genius, Wikidata)
- ✅ Skips already processed items (no duplicate API calls)
- ✅ Batch support: process multiple albums and artists
- ✅ Logs for missing items and failed lyrics
- ✅ Lyrics text cleaning and transformation
- ✅ Metadata merging: Genius + Spotify + Wikidata
- ✅ Multi-artist support for loading into PostgreSQL
- ✅ Readability + sentiment scoring for every song (Flesch, VADER)

Coming next:

- ⏳ Visual analysis and dashboard
- ⏳ Songwriting evolution tracking

---

## 🗂 Folder Structure (updated)

```bash
src/
├── extraction/
│   ├── genius_extraction.py
│   ├── spotify_extraction.py
│   └── wikidata_extraction.py
├── transformation/
│   ├── genius_transformation.py
│   ├── spotify_transformation.py
│   └── wikidata_transformation.py
├── process/
│   └── process.py
├── load/
│   └── load.py
├── analysis/
│   └── analyze_lyrics.py
```

These folders are generated automatically when running the pipeline:

```bash
logs/

raw/
├── GENIUS/
├── SPOTIFY/
└── WIKIDATA/

transformations/
├── GENIUS/
└── SPOTIFY/

processed/
└── <artist name>/
```

---

## 🧪 How to Run the Full Pipeline

From the root of the project:

```bash
python main.py
```

You’ll be guided step-by-step through scraping, transforming, processing, and loading.

All stages are interactive and **multi-artist ready**. Already processed items are skipped automatically.

---

## 🧰 Setup

1. Clone the repo
2. Create a `.env` file:

```
SPOTIPY_CLIENT_ID=your_spotify_id
SPOTIPY_CLIENT_SECRET=your_spotify_secret
SPOTIPY_REDIRECT_URI=http://localhost:8080
GENIUS_CLIENT_ACCESS_TOKEN=your_genius_token
```

3. Install dependencies:

Using pip:

```bash
pip install -r requirements.txt
```

Or using conda:

```bash
conda env create -f environment.yml
conda activate scrape_the_verse
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
