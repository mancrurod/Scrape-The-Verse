import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv
from textstat import flesch_reading_ease
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter, defaultdict
import nltk
import spacy
import string

# === SETUP ===
load_dotenv()

# Download required NLTK resources
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')

# Initialize tools for analysis
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

sia = SentimentIntensityAnalyzer()
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))
punctuation = set(string.punctuation)

# Load database connection parameters from .env
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

# === ANALYSIS FUNCTIONS ===

def compute_readability(text):
    """
    Compute Flesch Reading Ease score for a given text.
    Returns None if computation fails.
    """
    try:
        return flesch_reading_ease(text)
    except:
        return None

def compute_sentiment(text):
    """
    Compute compound sentiment score using VADER.
    Returns None if computation fails.
    """
    try:
        return sia.polarity_scores(text)['compound']
    except:
        return None

def compute_basic_stats(text):
    """
    Compute basic statistics: word count, line count, character count.
    """
    words = len(text.split())
    lines = text.count('\n') + 1
    chars = len(text)
    return words, lines, chars

def compute_lexical_density(text):
    """
    Compute lexical density (ratio of content words to total words) using spaCy.
    Returns None if analysis fails.
    """
    try:
        doc = nlp(text)
        content_words = [token for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']]
        return len(content_words) / max(1, len(doc))
    except:
        return None

def tokenize_and_count(text):
    """
    Tokenize the text, remove stopwords and punctuation,
    and return a Counter with word frequencies.
    """
    tokens = word_tokenize(text.lower())
    clean_tokens = [t for t in tokens if t.isalpha() and t not in stop_words and t not in punctuation]
    return Counter(clean_tokens)

# === MAIN WORKFLOW ===

def main():
    """
    Analyze song lyrics stored in the database by computing:
    - Readability
    - Sentiment
    - Basic stats (word/line/char count)
    - Lexical density

    Then generate:
    - Word frequency table per track
    - Word frequency table per album
    """
    print("\n📊 Starting lyrics analysis (readability + sentiment + word frequencies)...\n")

    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # === STEP 1: Update missing per-track statistics ===
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

        # Compute all stats
        readability = compute_readability(text)
        sentiment = compute_sentiment(text)
        word_count, line_count, char_count = compute_basic_stats(text)
        lexical_density = compute_lexical_density(text)

        # Update database
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
            readability,
            sentiment,
            word_count,
            line_count,
            char_count,
            lexical_density,
            track_id
        ))

        print(f"✅ Track {track_id} | Words: {word_count} | Lexical Density: {lexical_density:.2f}")

    conn.commit()

    # === STEP 2: Generate word frequencies ===
    print("\n🧠 Generating word frequencies...")

    # Get all lyrics with corresponding track, album, and artist metadata
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

    # Track-level word frequencies
    track_word_rows = []
    # Album-level word aggregations
    album_word_counts = defaultdict(Counter)

    for row in all_data:
        text = row["text"] or ""
        tokens = tokenize_and_count(text)

        for word, count in tokens.items():
            # Track-level
            track_word_rows.append((
                row["track_id"], row["artist"], row["album"], row["track_name"], word, count
            ))
            # Accumulate per album
            album_word_counts[(row["artist"], row["album"])][word] += count

    # Clear old frequencies before inserting updated ones
    cursor.execute("DELETE FROM word_frequencies_track;")
    cursor.execute("DELETE FROM word_frequencies_album;")

    # Insert track-level word frequencies
    execute_values(cursor, """
        INSERT INTO word_frequencies_track (track_id, artist, album, track_name, word, count)
        VALUES %s;
    """, track_word_rows)

    # Insert album-level word frequencies
    album_word_rows = [
        (artist, album, word, count)
        for (artist, album), counts in album_word_counts.items()
        for word, count in counts.items()
    ]

    execute_values(cursor, """
        INSERT INTO word_frequencies_album (artist, album, word, count)
        VALUES %s;
    """, album_word_rows)

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Lyrics analysis and word frequencies completed.")

if __name__ == "__main__":
    main()
