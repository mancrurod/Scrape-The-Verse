# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.load.run_loading
#
# DO NOT run it directly (e.g., `python run_loading.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.load.paths import get_all_artist_data
from src.load.parser import parse_artist_csv, parse_album_csv
from src.load.loader import insert_artist, insert_album, insert_tracks, insert_lyrics
from src.load.database import connect_db, create_tables

def get_track_name_to_id(cursor, album_id):
    """
    Fetches a mapping of track names to their corresponding IDs for a given album.
    
    Args:
        cursor: Database cursor object.
        album_id: The ID of the album to query.

    Returns:
        A dictionary mapping track names to track IDs.
    """
    cursor.execute("SELECT id, name FROM tracks WHERE album_id = %s;", (album_id,))
    return {name: track_id for track_id, name in cursor.fetchall()}

def run_etl():
    """
    Executes the ETL (Extract, Transform, Load) process for loading artist, album, track, and lyrics data
    from the 'processed/' folder into the database.
    """
    print("🚀 Starting data load from the 'processed/' folder...")

    # Retrieve all artist data from the 'processed/' folder
    all_data = get_all_artist_data()

    if not all_data:
        print("❌ No data found in 'processed/'")
        return

    # Connect to the database
    conn = connect_db()
    cursor = conn.cursor()

    # Create necessary tables if they don't exist
    create_tables(cursor)
    conn.commit()

    for artist in all_data:
        print(f"🎤 Processing artist: {artist['artist']}")
        artist_data = parse_artist_csv(artist["artist_metadata"])
        artist_id = insert_artist(cursor, artist_data)
        if not artist_id:
            continue

        for album in artist["albums"]:
            print(f"   💿 Album: {album['name']}")
            album_data, tracks_data = parse_album_csv(album["csv"], artist_id)
            album_id = insert_album(cursor, album_data, artist_id)
            if not album_id:
                continue

        insert_tracks(cursor, tracks_data, album_id)
        track_name_to_id = get_track_name_to_id(cursor, album_id)
        insert_lyrics(cursor, tracks_data, track_name_to_id)


        conn.commit()

    cursor.close()
    conn.close()
    print("\n✅ Data load completed successfully.")

if __name__ == "__main__":
    run_etl()
