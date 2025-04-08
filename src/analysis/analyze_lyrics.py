import os
import string
from collections import Counter, defaultdict
from typing import Tuple, Optional, Dict

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from textstat import flesch_reading_ease
import spacy

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv

# ========================
# === ENVIRONMENT SETUP ===
# ========================

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

# Ensure NLTK resources

def ensure_nltk_resource(resource_path: str, download_name: Optional[str] = None) -> None:
    try:
        nltk.data.find(resource_path)
    except LookupError:
        name = download_name or resource_path.split("/")[-1]
        print(f"🔄 Downloading NLTK resource: {name}")
        nltk.download(name)
        print(f"✅ Downloaded: {name}")

for res in ["sentiment/vader_lexicon", "tokenizers/punkt", "corpora/stopwords"]:
    ensure_nltk_resource(res)

sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words("english"))

# Ensure spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("🔄 Downloading spaCy model 'en_core_web_sm'")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy model loaded")

punctuation = set(string.punctuation)

# ============================
# === TEXT ANALYSIS UTILS ===
# ============================

def compute_readability(text: str) -> Optional[float]:
    try:
        return flesch_reading_ease(text)
    except:
        return None

def compute_sentiment(text: str) -> Optional[float]:
    try:
        return sia.polarity_scores(text)["compound"]
    except:
        return None

def compute_basic_stats(text: str) -> Tuple[int, int, int]:
    words = len(text.split())
    lines = text.count("\n") + 1
    chars = len(text)
    return words, lines, chars

def compute_lexical_density(text: str) -> Optional[float]:
    try:
        doc = nlp(text)
        content = [t for t in doc if t.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]]
        return len(content) / max(1, len(doc))
    except:
        return None

def tokenize_and_count(text: str) -> Counter:
    tokens = word_tokenize(text.lower())
    clean_tokens = [t for t in tokens if t.isalpha() and t not in stop_words and t not in punctuation]
    return Counter(clean_tokens)

# ============================
# === DB RESOLUTION UTILS ===
# ============================

def get_artist_id(cursor, artist_name: str) -> Optional[int]:
    cursor.execute("SELECT id FROM artists WHERE name = %s", (artist_name,))
    result = cursor.fetchone()
    return result["id"] if result else None

def get_album_id(cursor, album_name: str, artist_id: int) -> Optional[int]:
    cursor.execute("SELECT id FROM albums WHERE name = %s AND artist_id = %s", (album_name, artist_id))
    result = cursor.fetchone()
    return result["id"] if result else None

# ===========================
# === MAIN ANALYSIS FLOW ===
# ===========================

def main() -> None:
    """
    Main CLI entry point to analyze lyrics:
    - Flesch readability
    - Sentiment (VADER)
    - Basic stats: words, lines, chars
    - Lexical density
    - Word frequencies (track/album level)
    """
    print("\n📊 Starting lyrics analysis...\n")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Step 1: Update lyrics table with stats
    cursor.execute("""
        SELECT track_id, text FROM lyrics
        WHERE readability_score IS NULL
           OR sentiment_score IS NULL
           OR word_count IS NULL
           OR line_count IS NULL
           OR char_count IS NULL
           OR lexical_density IS NULL;
    """)
    lyrics = cursor.fetchall()

    for row in lyrics:
        track_id = row['track_id']
        text = row['text'] or ""

        readability = compute_readability(text)
        sentiment = compute_sentiment(text)
        word_count, line_count, char_count = compute_basic_stats(text)
        lexical_density = compute_lexical_density(text)

        cursor.execute("""
            UPDATE lyrics
            SET readability_score = %s,
                sentiment_score = %s,
                word_count = %s,
                line_count = %s,
                char_count = %s,
                lexical_density = %s
            WHERE track_id = %s;
        """, (
            readability, sentiment, word_count, line_count,
            char_count, lexical_density, track_id
        ))

        print(f"✅ Track {track_id} | Words: {word_count} | Lexical Density: {lexical_density:.2f}")

    conn.commit()

    # Step 2: Generate word frequencies
    print("\n🧠 Generating word frequencies...")

    cursor.execute("""
        SELECT
            l.track_id, l.text, t.name AS track_name,
            a.name AS album, ar.name AS artist
        FROM lyrics l
        JOIN tracks t ON l.track_id = t.id
        JOIN albums a ON t.album_id = a.id
        JOIN artists ar ON a.artist_id = ar.id
        WHERE l.text IS NOT NULL;
    """)
    all_data = cursor.fetchall()

    track_word_rows = []
    album_word_counts: Dict[Tuple[str, str], Counter] = defaultdict(Counter)

    for row in all_data:
        text = row["text"] or ""
        tokens = tokenize_and_count(text)

        for word, count in tokens.items():
            track_word_rows.append((row["track_id"], word, count))
            album_key = (row["artist"], row["album"])
            album_word_counts[album_key][word] += count

    # Reset previous word frequencies
    cursor.execute("DELETE FROM word_frequencies_track;")
    cursor.execute("DELETE FROM word_frequencies_album;")

    # Insert per-track word counts
    if track_word_rows:
        execute_values(cursor, """
            INSERT INTO word_frequencies_track (track_id, word, count)
            VALUES %s
            ON CONFLICT (track_id, word) DO UPDATE SET count = EXCLUDED.count;
        """, track_word_rows)
        print(f"✅ Inserted {len(track_word_rows)} track-level word frequencies.")
    else:
        print("⚠️ No track-level word frequencies generated.")

    # Insert per-album word counts
    values_album = []
    for (artist, album), counter in album_word_counts.items():
        artist_id = get_artist_id(cursor, artist)
        album_id = get_album_id(cursor, album, artist_id)
        if artist_id is None or album_id is None:
            print(f"⚠️ Could not resolve ID for {artist} - {album}. Skipping.")
            continue
        for word, count in counter.items():
            values_album.append((album_id, word, count))

    if values_album:
        execute_values(cursor, """
            INSERT INTO word_frequencies_album (album_id, word, count)
            VALUES %s
            ON CONFLICT (album_id, word) DO UPDATE SET count = EXCLUDED.count;
        """, values_album)
        print(f"✅ Inserted {len(values_album)} album-level word frequencies.")
    else:
        print("⚠️ No album-level word frequencies generated.")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Lyrics analysis complete.")

if __name__ == "__main__":
    main()
