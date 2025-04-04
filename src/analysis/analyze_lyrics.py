import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from textstat import flesch_reading_ease
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# === SETUP ===
load_dotenv()
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
}

# === ANALYSIS FUNCTIONS ===
def compute_readability(text):
    try:
        return flesch_reading_ease(text)
    except:
        return None

def compute_sentiment(text):
    try:
        return sia.polarity_scores(text)['compound']
    except:
        return None

# === MAIN ===
def main():
    print("\n📊 Starting lyrics analysis (readability + sentiment)...\n")

    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch all lyrics that still need scoring
    cursor.execute("""
        SELECT track_id, text FROM lyrics
        WHERE readability_score IS NULL OR sentiment_score IS NULL;
    """)
    lyrics = cursor.fetchall()

    if not lyrics:
        print("✅ All lyrics are already analyzed. Nothing to update.")
        cursor.close()
        conn.close()
        return

    for row in lyrics:
        track_id = row['track_id']
        text = row['text'] or ""

        readability = compute_readability(text)
        sentiment = compute_sentiment(text)

        cursor.execute("""
            UPDATE lyrics
            SET readability_score = %s,
                sentiment_score = %s
            WHERE track_id = %s;
        """, (readability, sentiment, track_id))

        print(f"✅ Updated track_id {track_id} | Readability: {readability:.2f} | Sentiment: {sentiment:.2f}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n🎉 All lyrics updated successfully.")

if __name__ == "__main__":
    main()
