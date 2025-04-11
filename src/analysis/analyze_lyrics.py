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

# Load environment variables from a .env file into the runtime environment
load_dotenv()

# Define database connection parameters using values from the environment
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),          # Database name
    "user": os.getenv("POSTGRES_USER"),          # Database user
    "password": os.getenv("POSTGRES_PASSWORD"),  # User password
    "host": os.getenv("POSTGRES_HOST", "localhost"),  # Hostname (default: localhost)
    "port": os.getenv("POSTGRES_PORT", 5432),         # Port (default: 5432)
}


# ================================
# === Ensure NLTK Resources Exist ===
# ================================

def ensure_nltk_resource(resource_path: str, download_name: Optional[str] = None) -> None:
    """
    Ensure the specified NLTK resource is available; download it if missing.

    Args:
        resource_path (str): The NLTK resource path (e.g., "corpora/stopwords").
        download_name (Optional[str]): The resource name to pass to nltk.download().
                                       If None, it is inferred from the path.
    """
    try:
        # Check if the resource is already available locally
        nltk.data.find(resource_path)
    except LookupError:
        # If not found, attempt to download it
        name = download_name or resource_path.split("/")[-1]
        print(f"🔄 Downloading NLTK resource: {name}")
        nltk.download(name)
        print(f"✅ Downloaded: {name}")

# List of required NLTK resources for sentiment and text processing
for res in ["sentiment/vader_lexicon", "tokenizers/punkt", "corpora/stopwords"]:
    ensure_nltk_resource(res)

# Initialize NLTK sentiment analyzer and English stopword list
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words("english"))


# ============================
# === Ensure spaCy Model ===
# ============================

try:
    # Try to load the English spaCy model
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If not found, download it via spaCy's CLI
    print("🔄 Downloading spaCy model 'en_core_web_sm'")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")
    print("✅ spaCy model loaded")

# Define a reusable set of punctuation characters for text cleaning/tokenization
punctuation = set(string.punctuation)


# ============================
# === TEXT ANALYSIS UTILS ===
# ============================

def compute_readability(text: str) -> Optional[float]:
    """
    Compute the Flesch Reading Ease score for a given text.

    Args:
        text (str): The input text to analyze.

    Returns:
        Optional[float]: The readability score, or None if computation fails.
    """
    try:
        # Attempt to compute the Flesch Reading Ease score
        return flesch_reading_ease(text)
    except:
        # Return None if the calculation raises any exception (e.g., empty or malformed input)
        return None


def compute_sentiment(text: str) -> Optional[float]:
    """
    Compute the compound sentiment score of a given text using VADER.

    Args:
        text (str): The input text to analyze.

    Returns:
        Optional[float]: The compound sentiment score between -1 (negative) and 1 (positive),
                         or None if the analysis fails.
    """
    try:
        # Use NLTK's SentimentIntensityAnalyzer to compute sentiment
        return sia.polarity_scores(text)["compound"]
    except:
        # Return None if the sentiment analysis fails (e.g., due to missing model or invalid input)
        return None


def compute_basic_stats(text: str) -> Tuple[int, int, int]:
    """
    Compute basic statistics for a given text: word count, line count, and character count.

    Args:
        text (str): The input text (e.g., song lyrics).

    Returns:
        Tuple[int, int, int]: A tuple containing:
            - Number of words
            - Number of lines
            - Number of characters
    """
    # Count the number of words by splitting on whitespace
    words = len(text.split())

    # Count the number of lines based on newline characters
    lines = text.count("\n") + 1

    # Count the total number of characters (including whitespace and punctuation)
    chars = len(text)

    return words, lines, chars


def compute_lexical_density(text: str) -> Optional[float]:
    """
    Compute the lexical density of a text using spaCy part-of-speech tagging.

    Lexical density is defined as the ratio of content words (nouns, verbs,
    adjectives, adverbs) to the total number of tokens.

    Args:
        text (str): The input text to analyze.

    Returns:
        Optional[float]: Lexical density score, or None if the computation fails.
    """
    try:
        # Use spaCy to tokenize and tag parts of speech
        doc = nlp(text)

        # Filter for content words
        content = [t for t in doc if t.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]]

        # Return the ratio of content words to total tokens
        return len(content) / max(1, len(doc))  # Avoid division by zero
    except:
        # Return None if processing fails (e.g., due to missing model or bad input)
        return None


def tokenize_and_count(text: str) -> Counter:
    """
    Tokenize the input text, remove stopwords and punctuation, and count word frequencies.

    Args:
        text (str): The input text to process (e.g., song lyrics).

    Returns:
        Counter: A Counter object mapping words to their frequency.
    """
    # Tokenize the text into lowercase words
    tokens = word_tokenize(text.lower())

    # Filter out stopwords, punctuation, and non-alphabetic tokens
    clean_tokens = [
        t for t in tokens
        if t.isalpha() and t not in stop_words and t not in punctuation
    ]

    # Return a frequency count of the remaining tokens
    return Counter(clean_tokens)


# ============================
# === DB RESOLUTION UTILS ===
# ============================

def get_artist_id(cursor, artist_name: str) -> Optional[int]:
    """
    Retrieve the ID of an artist from the 'artists' table by name.

    Args:
        cursor: Active psycopg2 cursor.
        artist_name (str): The name of the artist.

    Returns:
        Optional[int]: The artist's ID if found, otherwise None.
    """
    cursor.execute("SELECT id FROM artists WHERE name = %s", (artist_name,))
    result = cursor.fetchone()
    return result["id"] if result else None


def get_album_id(cursor, album_name: str, artist_id: int) -> Optional[int]:
    """
    Retrieve the ID of an album from the 'albums' table by name and artist ID.

    Args:
        cursor: Active psycopg2 cursor.
        album_name (str): The name of the album.
        artist_id (int): The ID of the artist the album belongs to.

    Returns:
        Optional[int]: The album's ID if found, otherwise None.
    """
    cursor.execute(
        "SELECT id FROM albums WHERE name = %s AND artist_id = %s",
        (album_name, artist_id)
    )
    result = cursor.fetchone()
    return result["id"] if result else None

# ===========================
# === MAIN ANALYSIS FLOW ===
# ===========================

def main() -> None:
    """
    Main CLI entry point to analyze lyrics stored in the PostgreSQL database.

    The analysis includes:
    - Flesch Reading Ease (readability)
    - VADER compound sentiment score
    - Basic stats: word count, line count, character count
    - Lexical density (content words / total tokens)
    - Word frequency counts at the track and album level
    """
    print("\n📊 Starting lyrics analysis...\n")

    # Establish database connection and use RealDictCursor for column-based access
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # === STEP 1: Compute and update text-level metrics in the lyrics table ===
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

        # Compute metrics
        readability = compute_readability(text)
        sentiment = compute_sentiment(text)
        word_count, line_count, char_count = compute_basic_stats(text)
        lexical_density = compute_lexical_density(text)

        # Update metrics in the database
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

    # === STEP 2: Generate word frequencies for each track and album ===
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

    track_word_rows = []  # For bulk insert into word_frequencies_track
    album_word_counts: Dict[Tuple[str, str], Counter] = defaultdict(Counter)

    for row in all_data:
        text = row["text"] or ""
        tokens = tokenize_and_count(text)

        # Collect track-level word frequencies
        for word, count in tokens.items():
            track_word_rows.append((row["track_id"], word, count))
            album_key = (row["artist"], row["album"])
            album_word_counts[album_key][word] += count

    # Clear previous frequency records
    cursor.execute("DELETE FROM word_frequencies_track;")
    cursor.execute("DELETE FROM word_frequencies_album;")

    # === STEP 3: Insert per-track word frequencies ===
    if track_word_rows:
        execute_values(cursor, """
            INSERT INTO word_frequencies_track (track_id, word, count)
            VALUES %s
            ON CONFLICT (track_id, word) DO UPDATE SET count = EXCLUDED.count;
        """, track_word_rows)
        print(f"✅ Inserted {len(track_word_rows)} track-level word frequencies.")
    else:
        print("⚠️ No track-level word frequencies generated.")

    # === STEP 4: Insert per-album word frequencies ===
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

    # Finalize DB operations
    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Lyrics analysis complete.")


if __name__ == "__main__":
    main()
