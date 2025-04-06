# ⚙️ Installation Guide

This page explains how to set up **Scrape The Verse** on your local machine.

---

## 🧩 Requirements

- Python 3.9+
- Git
- (Optional) Conda
- Spotify Developer Account
- Genius API Token
- PostgreSQL (local or Docker)

---

## 📝 Step 1: Clone the repository

```bash
git clone https://github.com/your-username/Scrape-The-Verse.git
cd Scrape-The-Verse
```

---

## 🔐 Step 2: Create a `.env` file

Inside the project root, create a `.env` file with:

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

## 📦 Step 3: Install dependencies

**With pip:**

```bash
pip install -r requirements.txt
```

**With conda:**

```bash
conda env create -f environment.yml
conda activate scrape_the_verse
```

---

## 🛠 Step 4: Set up PostgreSQL with Docker

You can launch a local database using:

```bash
docker run --name postgres-verse -e POSTGRES_DB=lyrics -e POSTGRES_USER=verse_user -e POSTGRES_PASSWORD=yourpass -p 5432:5432 -d postgres
```

---

You’re now ready to run the ETL pipeline!