# 🎶 Scrape The Verse

*He wrote “Tangled Up in Blue,” she wrote “The Story of Us”—we wrote the code to ask if Swift could follow Dylan to Stockholm.*

> 📚 This project is a full-blown, ETL-powered attempt to answer one brilliant, nerdy, and slightly unhinged question:  
> **Can Taylor Swift win the Nobel Prize in Literature?**  
> (Spoiler: if Bob Dylan did, why not her?)

> *“There’s no success like failure, and failure’s no success at all.”* — Bob Dylan  
> *“I want to be defined by the things that I love.”* — Taylor Swift

---

## 🚀 What is this?

**Scrape The Verse** is a modular ETL pipeline built in Python to scrape and analyze:

- 🎧 Spotify metadata (artists, albums, songs)
- 📝 Genius lyrics (by album)
- 🧠 Wikidata metadata (biographical and artistic traits)

...with one literary mission:  
Build a clean, analyzable dataset to explore **songwriting quality** through the lens of literary merit.

---

## 🧠 Project Status

**Stable and modular** – The project is fully functional and organized as a clean ETL pipeline with plug-and-play components.

### ✅ Core Features

- Spotify, Genius & Wikidata scrapers  
- Lyrics + metadata merging and transformation  
- Song-level stats: readability, sentiment, lexical density  
- Album- and track-level word frequency tables (for word clouds!)  
- PostgreSQL loader with relational schema  
- Fully interactive CLI for each pipeline step  
- Batch processing & log tracking for errors or missing data

---

## 📁 Project Structure

```text
src/
├── analysis/
│   └── analyze_lyrics.py
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

raw/
├── GENIUS/
├── SPOTIFY/
└── WIKIDATA/

transformations/
├── GENIUS/
└── SPOTIFY/

processed/
└── <artist>/
    └── <album>_final.csv

logs/
```

---

## ⚙️ Setup

1. Clone the repo

```bash
git clone https://github.com/<your-username>/Scrape-The-Verse.git
cd Scrape-The-Verse
```

2. Create your `.env` file:

```dotenv
SPOTIPY_CLIENT_ID=your_spotify_id
SPOTIPY_CLIENT_SECRET=your_spotify_secret
SPOTIPY_REDIRECT_URI=http://localhost:8080
GENIUS_CLIENT_ACCESS_TOKEN=your_genius_token
POSTGRES_DB=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

3. Install dependencies:

```bash
# Using pip
pip install -r requirements.txt

# Or using conda
conda env create -f environment.yml
conda activate scrape_the_verse
```

---

## ▶️ How to Run the Pipeline

You can run the full flow manually via:

```bash
python main.py
```

---

## 📊 Database Schema

Includes:

- `artists`: identity & biography  
- `albums`: linked to artist  
- `tracks`: song-level data  
- `lyrics`: raw text + readability, sentiment, lexical stats  
- `word_frequencies_track`: for song-level word clouds  
- `word_frequencies_album`: for album-level word clouds

---

## 💡 Example Use Cases

- Compare **lexical density** of Bob Dylan vs Taylor Swift  
- Visualize **frequent motifs** (love, time, silence...) by album  
- Track evolution of **sentiment** or **explicitness** across eras  
- Build dashboards to answer: *"Is this Nobel-worthy poetry?"*

---

## 🤝 Contributing

Pull requests welcome – especially from Swifties who know SQL.  
Just… please don’t fight about *Folklore* vs *1989* in the issues.

---

## ✨ Credits

Built by a language nerd with an overactive playlist.  
Inspired by literature, lyrics, and one very specific Nobel Prize.

> “You’re on your own, kid—but the script runs fine.”  
> — T. Swift, sort of.