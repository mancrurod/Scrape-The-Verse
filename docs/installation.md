# 🛠️ Installation Guide

To get the project up and running on your machine, follow these steps.

---

## 📦 Clone the repository

```bash
git clone https://github.com/<your-username>/Scrape-The-Verse.git
cd Scrape-The-Verse
```

---

## 🌱 Create a virtual environment

We recommend using **conda**:

```bash
conda create -n scraptheverse python=3.10
conda activate scraptheverse
```

Or with `venv`:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## 📚 Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

This installs:

- Spotify + Genius APIs
- NLP tools (`spaCy`, `nltk`, `textstat`, etc.)
- PostgreSQL client
- Transformers (optional)

---

## 🧪 Set up your environment variables

Create a `.env` file in the root directory with the following:

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

---

## 🧱 Initialize the PostgreSQL schema

Run this SQL script:

```bash
psql -U <your_user> -d <your_database> -f db/create_schema.sql
```

Or use a GUI tool like DBeaver.

---

You're now ready to run the ETL pipeline!