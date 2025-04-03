import time
import spotipy

def sanitize(name: str) -> str:
    """
    Replaces invalid characters in a string with a hyphen and trims whitespace.

    Args:
        name (str): The string to sanitize.

    Returns:
        str: The sanitized string.
    """
    # List of characters that are not allowed in file or folder names
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    # Replace each invalid character with a hyphen
    for char in invalid_chars:
        name = name.replace(char, '-')
    # Remove leading and trailing whitespace
    return name.strip()

def get_artist_folder(artist_name: str) -> str:
    """
    Sanitizes an artist's name to create a valid folder name.

    Args:
        artist_name (str): The name of the artist.

    Returns:
        str: A sanitized folder name for the artist.
    """
    # Use the sanitize function to clean up the artist's name
    return sanitize(artist_name)

def with_retry(request_fn, *args, max_retries=5, **kwargs):
    """
    Executes a function with retry logic in case of exceptions.

    Args:
        request_fn (callable): The function to execute.
        *args: Positional arguments to pass to the function.
        max_retries (int): Maximum number of retries (default is 5).
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        Any: The result of the function if successful, or None if retries are exhausted.
    """
    retry_count = 0
    # Retry the function until the maximum number of retries is reached
    while retry_count < max_retries:
        try:
            # Attempt to execute the function
            return request_fn(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as e:
            # Handle Spotify-specific rate limit exception
            if e.http_status == 429:
                # Get the retry-after duration from the exception headers
                retry_after = int(e.headers.get("Retry-After", 5))
                print(f"⏳ Rate limit hit. Waiting for {retry_after} seconds (Retry {retry_count+1}/{max_retries})...")
                time.sleep(retry_after)
                retry_count += 1
            else:
                # Raise other Spotify exceptions
                raise
        except Exception as e:
            # Handle unexpected exceptions with exponential backoff
            wait = 2 ** retry_count
            print(f"⚠️ Unexpected error: {e}. Retrying in {wait} seconds (Retry {retry_count+1}/{max_retries})...")
            time.sleep(wait)
            retry_count += 1
    # If all retries are exhausted, log a message and return None
    print("❌ Max retries exceeded.")
    return None
