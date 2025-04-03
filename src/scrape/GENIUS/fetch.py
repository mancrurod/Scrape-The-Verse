import requests
from bs4 import BeautifulSoup
from src.scraping.GENIUS.utils import slugify, clean_up

def get_all_songs_from_album(artist: str, album_name: str):
    """
    Fetch all song titles from a specific album on Genius.

    Args:
        artist (str): The name of the artist.
        album_name (str): The name of the album.

    Returns:
        list: A list of tuples where each tuple contains the song's index (int) 
              and its cleaned-up title (str). Returns an empty list if an error occurs.
    """
    # Convert artist and album names to URL-friendly slugs
    artist_slug = slugify(artist)
    album_slug = slugify(album_name)

    try:
        # Fetch the album page from Genius
        response = requests.get(f"https://genius.com/albums/{artist_slug}/{album_slug}", timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except Exception as e:
        # Handle errors during the request
        print(f"❌ Error fetching album page: {e}")
        return []

    # Parse the HTML content of the page
    html_string = response.text
    document = BeautifulSoup(html_string, "html.parser")
    
    # Find all song title elements on the page
    song_title_tags = document.find_all("h3", attrs={"class": "chart_row-content-title"})

    # Extract and clean up song titles
    song_titles = [song_title.text for song_title in song_title_tags]
    clean_songs = [(i + 1, clean_up(title)) for i, title in enumerate(song_titles)]
    
    return clean_songs
