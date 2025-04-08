# 🎶 Scrape The Verse

*He wrote “Tangled Up in Blue,” she wrote “The Story of Us”—we wrote the code to ask if Swift could follow Dylan to Stockholm.*

> 📚 This project is a full-blown, ETL-powered attempt to answer one brilliant, nerdy, and slightly unhinged question:  
> **Can Taylor Swift win the Nobel Prize in Literature?**  
> (Spoiler: if Bob Dylan did, why not her?)

> *“There’s no success like failure, and failure’s no success at all.”* — Bob Dylan  
> *“I want to be defined by the things that I love.”* — Taylor Swift

---

## 🚀 What is this?

**Scrape The Verse** is a modular ETL + NLP pipeline built in Python to scrape and analyze:

- 🎧 Spotify metadata (artists, albums, songs)
- 📝 Genius lyrics (by album)
- 🧠 Wikidata metadata (biographical and artistic traits)

With one literary mission:  
**Build a clean, analyzable dataset to explore songwriting quality through the lens of literary merit.**

---

## 🧠 Project Status

**Stable and modular** — the project is fully functional and structured as a clear ETL pipeline with reusable components and database integration.

### ✅ Core Features

- Modular scrapers for Spotify, Genius, and Wikidata
- Lyrics + metadata transformation and merging
- Track-level NLP analysis:
  - Flesch readability
  - Sentiment (VADER)
  - Lexical density
  - Word/line/character counts
- Word frequency tables for tracks and albums
- PostgreSQL loader with relational schema + data integrity
- Robust dependency validation (`nltk`, `spaCy`, etc.)
- Batch logging of missing or matched lyrics
- Fully interactive CLI for all pipeline stages
- Clean, testable, documented and type-annotated Python code (SOLID-ready)

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
├── processing/
│   └── process.py
├── load/
│   ├── load.py

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
db/
└── create_schema.sql
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/Scrape-The-Verse.git
cd Scrape-The-Verse
```

### 2. Create your `.env` file

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

### 3. Create and activate the Conda environment

```bash
conda create -n scraptheverse python=3.10
conda activate scraptheverse
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## 🧪 Initialize the Database

Before loading data, create the PostgreSQL schema:

```bash
psql -U <your_user> -d <your_database> -f db/create_schema.sql
```

Or run it directly in DBeaver.

---

## ▶️ Run the Pipeline

Run each step of the pipeline via CLI:

```bash
# Step 1: Scrape data
python src/extraction/spotify_extraction.py
python src/extraction/genius_extraction.py
python src/extraction/wikidata_extraction.py

# Step 2: Clean & transform
python src/transformation/spotify_transformation.py
python src/transformation/genius_transformation.py
python src/transformation/wikidata_transformation.py

# Step 3: Merge lyrics with tracks
python src/processing/process.py

# Step 4: Load to PostgreSQL
python src/load/load.py

# Step 5: Analyze lyrics
python src/analysis/analyze_lyrics.py
```

You can run every step at once, too.

```bash
python main.py
```

---

## 📊 Database Schema Overview

Includes:

- `artists`: identity & biography  
- `albums`: linked to artist  
- `tracks`: song-level data  
- `lyrics`: raw text + readability, sentiment, lexical stats  
- `word_frequencies_track`: for song-level word clouds  
- `word_frequencies_album`: for album-level word clouds

Defined in [`db/create_schema.sql`](db/create_schema.sql)

---

## 💡 Example Use Cases

- Compare **lexical density** of Bob Dylan vs Taylor Swift  
- Visualize **frequent motifs** (love, time, silence...) by album  
- Track evolution of **sentiment** or **explicitness** across eras  
- Build dashboards to answer: *"Is this Nobel-worthy poetry?"*

---

## 🤝 Contributing

Pull requests welcome — especially from Swifties who know SQL.  
Just… please don’t fight about *Folklore* vs *1989* in the issues.

---

## ✨ Credits

Built by a language nerd with an overactive playlist.  
Inspired by literature, lyrics, and one very specific Nobel Prize.

> “You’re on your own, kid—but the script runs fine.”  
> — T. Swift, sort of.
