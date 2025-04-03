from src.scraping.SPOTIFY.utils import with_retry

# Retrieves the Spotify ID of an artist by their name
def get_artist_id(sp, artist_name):
    """
    Fetch the Spotify artist ID for a given artist name.

    Args:
        sp: Spotify client instance.
        artist_name (str): Name of the artist.

    Returns:
        str or None: Spotify artist ID if found, otherwise None.
    """
    results = with_retry(sp.search, q=f"artist:{artist_name}", type="artist", limit=1)
    items = results.get("artists", {}).get("items", [])
    return items[0]["id"] if items else None

# Fetches metadata for a specific artist using their Spotify ID
def get_artist_metadata(sp, artist_id):
    """
    Fetch metadata for a given artist by their Spotify ID.

    Args:
        sp: Spotify client instance.
        artist_id (str): Spotify artist ID.

    Returns:
        dict: Metadata of the artist.
    """
    return with_retry(sp.artist, artist_id)

# Retrieves all tracks from a specific album
def get_album_tracks(sp, album_id):
    """
    Fetch all tracks from a given album by its Spotify ID.

    Args:
        sp: Spotify client instance.
        album_id (str): Spotify album ID.

    Returns:
        list: List of tracks in the album.
    """
    results = with_retry(sp.album_tracks, album_id)
    tracks = results['items']
    while results['next']:
        results = with_retry(sp.next, results)
        tracks.extend(results['items'])
    return tracks

# Extracts detailed metadata for a specific track
def extract_track_metadata(sp, track_id):
    """
    Fetch detailed metadata for a given track by its Spotify ID.

    Args:
        sp: Spotify client instance.
        track_id (str): Spotify track ID.

    Returns:
        dict: Metadata of the track, including name, artists, album, release date, popularity, explicit flag, and duration.
    """
    try:
        track_info = with_retry(sp.track, track_id)
        return {
            "Name": track_info.get("name"),
            "Artists": ", ".join([artist["name"] for artist in track_info.get("artists", [])]),
            "Album": track_info.get("album", {}).get("name"),
            "Release Date": track_info.get("album", {}).get("release_date"),
            "Popularity": track_info.get("popularity"),
            "Explicit": track_info.get("explicit"),
            "Duration (ms)": track_info.get("duration_ms")
        }
    except Exception as e:
        # Log an error if track metadata cannot be fetched
        print(f"⚠️ Error fetching track metadata for {track_id}: {e}")
        return {}
