import time
from src.scrape.SPOTIFY.fetch import get_album_tracks, extract_track_metadata
from src.scrape.SPOTIFY.storage import (
    album_fully_scraped,
    save_album_data,
    save_album_metadata,
    save_artist_metadata
)
from src.scrape.SPOTIFY.fetch import get_artist_id, get_artist_metadata
from src.scrape.SPOTIFY.logging import log_failed_album
from src.scrape.SPOTIFY.utils import with_retry
from src.utils.fallback_manager import (
    load_fallbacks,
    save_fallbacks,
    auto_resolve_album_id,
    resolve_album_id_from_user
)
def scrape_artist_albums(sp, artist_name, albums):
    """
    Scrapes metadata and track data for a list of albums by a specific artist.

    Args:
        sp: Spotify API client instance.
        artist_name (str): Name of the artist.
        albums (list): List of album dicts with 'name' and 'id'.

    Returns:
        None
    """
    for album in albums:
        album_name = album.get('name')
        album_id = album.get('id')

        if not album_name or not album_id:
            print(f"⚠️ Skipping invalid album entry: {album}")
            continue

        if album_fully_scraped(artist_name, album_name):
            print(f"⏭️  Skipping '{album_name}' by {artist_name} (already scraped)")
            continue

        print(f"🎵 Processing album '{album_name}' for artist '{artist_name}'...")

        try:
            album_metadata = with_retry(sp.album, album_id)

            simplified_album_metadata = {
                "Name": album_metadata.get("name"),
                "Release Date": album_metadata.get("release_date"),
                "Total Tracks": album_metadata.get("total_tracks"),
                "Label": album_metadata.get("label"),
                "Popularity": album_metadata.get("popularity"),
                "Genres": ", ".join(album_metadata.get("genres", [])),
                "Album Type": album_metadata.get("album_type"),
                "URI": album_metadata.get("uri")
            }
            save_album_metadata(artist_name, album_name, simplified_album_metadata)

            tracks = get_album_tracks(sp, album_id)
            time.sleep(2)

            track_data = []
            for track in tracks:
                track_metadata = extract_track_metadata(sp, track["id"])
                if track_metadata:
                    track_data.append(track_metadata)
                time.sleep(0.4)

            save_album_data(artist_name, album_name, track_data)
        except Exception as e:
            print(f"❌ Error processing album '{album_name}': {e}")
            log_failed_album(artist_name, album_name)# Log if the album is not found
            print(f"⚠️ Album '{album_name}' by artist '{artist_name}' not found.")
            log_failed_album(artist_name, album_name)

def scrape_single_album(sp, artist_name, album_name):
    """
    Scrapes metadata and track data for a single album by a specific artist.

    Args:
        sp: Spotify API client instance.
        artist_name (str): Name of the artist.
        album_name (str): Name of the album to scrape.

    Returns:
        None
    """
    print(f"🎵 Manually scraping album '{album_name}' for artist '{artist_name}'...")

    # Skip if the album has already been scraped
    if album_fully_scraped(artist_name, album_name):
        print(f"⏭️  Skipping '{album_name}' by {artist_name} (already scraped)")
        return

    # Attempt to load album ID from fallbacks
    key = f"{artist_name.strip()}|||{album_name.strip()}"
    fallbacks = load_fallbacks()
    album_id = fallbacks.get(key)

    if not album_id:
        # Perform a fuzzy search for the album
        print("🔍 Attempting fuzzy search...")
        album_results = with_retry(sp.search, q=f"album:{album_name} artist:{artist_name}", type="album", limit=10)
        items = album_results["albums"]["items"]

        # Match album name and artist name
        for item in items:
            result_album_name = item["name"].strip().lower()
            result_artist_names = [a["name"].lower() for a in item["artists"]]
            if album_name.lower().strip() == result_album_name and artist_name.lower() in result_artist_names:
                album_id = item["id"]
                break

    if not album_id:
        # Attempt automatic resolution of album ID
        print(f"⚠️ Could not match '{album_name}' by {artist_name}. Attempting automatic resolution...")
        album_id = auto_resolve_album_id(sp, artist_name, album_name)

    if not album_id:
        # Attempt manual resolution of album ID
        print(f"⚠️ Automatic resolution failed. Trying manual fallback...")
        album_id = resolve_album_id_from_user(sp, artist_name, album_name)

        if album_id:
            # Save resolved album ID to fallbacks
            fallbacks[key] = album_id
            save_fallbacks(fallbacks)
            print(f"✅ Manually resolved and saved album ID for '{album_name}' by '{artist_name}'")
        else:
            print(f"❌ Could not resolve album '{album_name}' by '{artist_name}'")
            return

    elif key not in fallbacks:
        # Save resolved album ID to fallbacks if not already saved
        fallbacks[key] = album_id
        save_fallbacks(fallbacks)
        print(f"✅ Resolved and saved album ID for '{album_name}' by '{artist_name}'")

    # Fetch and save artist metadata
    artist_id = get_artist_id(sp, artist_name)
    if artist_id:
        artist_metadata_raw = get_artist_metadata(sp, artist_id)
        simplified_artist_metadata = {
            "Name": artist_metadata_raw.get("name"),
            "Genres": ", ".join(artist_metadata_raw.get("genres", [])),
            "Followers": artist_metadata_raw.get("followers", {}).get("total"),
            "Popularity": artist_metadata_raw.get("popularity"),
            "URI": artist_metadata_raw.get("uri")
        }
        save_artist_metadata(artist_name, simplified_artist_metadata)

    # Fetch and save album metadata
    album_metadata = with_retry(sp.album, album_id)
    simplified_album_metadata = {
        "Name": album_metadata.get("name"),
        "Release Date": album_metadata.get("release_date"),
        "Total Tracks": album_metadata.get("total_tracks"),
        "Label": album_metadata.get("label"),
        "Popularity": album_metadata.get("popularity"),
        "Genres": ", ".join(album_metadata.get("genres", [])),
        "Album Type": album_metadata.get("album_type"),
        "URI": album_metadata.get("uri")
    }
    save_album_metadata(artist_name, album_name, simplified_album_metadata)

    # Fetch and process track data
    tracks = get_album_tracks(sp, album_id)
    time.sleep(2)  # Pause to avoid hitting API rate limits

    track_data = []
    for track in tracks:
        track_metadata = extract_track_metadata(sp, track["id"])
        if track_metadata:
            track_data.append(track_metadata)
        time.sleep(0.4)  # Pause between track requests

    # Save track data
    save_album_data(artist_name, album_name, track_data)
    print(f"✅ Finished manual scrape: '{album_name}' by {artist_name}")
