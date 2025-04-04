from src.scrape.SPOTIFY.fetch import get_artist_id, get_artist_metadata
from src.scrape.SPOTIFY.storage import save_artist_metadata
from src.scrape.SPOTIFY.albums import scrape_artist_albums
from src.scrape.SPOTIFY.logging import write_failed_log_to_file
from src.scrape.SPOTIFY.utils import with_retry

def scrape_full_artist(sp, artist_name):
    """
    Scrapes full artist data including metadata and albums.

    Args:
        sp: Spotify API client instance.
        artist_name (str): Name of the artist to scrape.

    Returns:
        None
    """
    # Fetch the artist ID using the artist name
    artist_id = get_artist_id(sp, artist_name)
    if not artist_id:
        print(f"❌ Artist not found: {artist_name}")
        return

    # Fetch artist metadata and simplify it for storage
    artist_metadata_raw = get_artist_metadata(sp, artist_id)
    simplified_artist_metadata = {
        "Name": artist_metadata_raw.get("name"),
        "Genres": ", ".join(artist_metadata_raw.get("genres", [])),
        "Followers": artist_metadata_raw.get("followers", {}).get("total"),
        "Popularity": artist_metadata_raw.get("popularity"),
        "URI": artist_metadata_raw.get("uri")
    }
    # Save the simplified artist metadata
    save_artist_metadata(artist_name, simplified_artist_metadata)

    # Fetch all albums for the artist
    results = sp.artist_albums(artist_id, album_type="album")
    albums = results["items"]
    seen = set()  # To track unique album names

    # Paginate through all album results
    while results["next"]:
        results = with_retry(sp.next, results)
        albums.extend(results["items"])

    # Filter out duplicate albums by name
    unique_albums = []
    for album in albums:
        name = album["name"].lower()
        if name not in seen:
            seen.add(name)
            unique_albums.append(album)

    print(f"📀 Albums found: {len(unique_albums)}")
    album_refs = [{"name": album["name"], "id": album["id"]} for album in unique_albums]
    scrape_artist_albums(sp, artist_name, album_refs)
    # Write any failed logs to a file
    write_failed_log_to_file()
