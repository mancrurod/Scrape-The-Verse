import re
import unicodedata

def sanitize(name: str) -> str:
    """
    Removes invalid characters from a string to make it safe for use as a file or folder name.

    Args:
        name (str): The input string to sanitize.

    Returns:
        str: The sanitized string with invalid characters removed and leading/trailing whitespace stripped.

    Example:
        >>> sanitize("Artist: Name?")
        'Artist Name'
    """
    # List of characters that are not allowed in file or folder names
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        # Replace each invalid character with an empty string
        name = name.replace(char, '')
    return name.strip()


def slugify(text: str) -> str:
    """
    Converts a string into a URL-friendly slug by normalizing, removing special characters, 
    and replacing spaces with hyphens.

    Args:
        text (str): The input string to slugify.

    Returns:
        str: The slugified string.

    Example:
        >>> slugify("Hello World!")
        'hello-world'
    """
    # Convert text to lowercase
    text = text.lower()
    # Normalize the text to remove accents and special characters
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Remove specific punctuation characters
    text = re.sub(r"[’'\"()]", "", text)
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Strip leading and trailing hyphens
    return text.strip("-")

def clean_up(song_title: str) -> str:
    """
    Cleans up a song title by removing specific patterns and unwanted characters.

    This function processes a song title string to remove unnecessary parts such as 
    "Ft" (featuring) sections or "Lyrics" and replaces any forward slashes with hyphens. 
    It ensures the resulting title is clean and formatted for further use.

    Args:
        song_title (str): The original song title to be cleaned.

    Returns:
        str: The cleaned-up song title.

    Example:
        >>> clean_up("Song Name (Ft. Artist) Lyrics")
        'Song Name'
        >>> clean_up("Another Song/Lyrics")
        'Another Song'
    """
    # Check if the song title contains "Ft" and clean accordingly
        # Remove "Lyrics" and replace slashes with hyphens
    if "Ft" in song_title:
        before_ft_pattern = re.compile(r".*(?=\(Ft)")
        song_title_before_ft = before_ft_pattern.search(song_title).group(0)
        clean_song_title = song_title_before_ft.strip().replace("/", "-")
    else:
        song_title_no_lyrics = song_title.replace("Lyrics", "")
        clean_song_title = song_title_no_lyrics.strip().replace("/", "-")
    return clean_song_title

def get_artist_folder(artist_name: str) -> str:
    return sanitize(artist_name)
