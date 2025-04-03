import os
from pathlib import Path
from dotenv import load_dotenv
import lyricsgenius

# Define the project root directory
project_root = Path.cwd()

# Load environment variables from the .env file located in the project root
load_dotenv(dotenv_path=project_root / ".env")

def get_genius_client():
    """
    Initializes and returns a Genius API client.

    This function retrieves the Genius API access token from the environment
    variables, initializes the Genius API client with the token, and configures
    it to remove section headers from lyrics.

    Returns:
        lyricsgenius.Genius: An instance of the Genius API client.

    Raises:
        Exception: If the GENIUS_CLIENT_ACCESS_TOKEN is not found in the environment variables.
    """
    # Retrieve the Genius API access token from environment variables
    access_token = os.getenv("GENIUS_CLIENT_ACCESS_TOKEN")
    if not access_token:
        # Raise an exception if the access token is missing
        raise Exception("❌ Missing GENIUS_CLIENT_ACCESS_TOKEN in .env file.")
    
    # Initialize the Genius API client with the access token and a timeout of 15 seconds
    genius = lyricsgenius.Genius(access_token, timeout=15)
    # Configure the client to remove section headers from the lyrics
    genius.remove_section_headers = True
    return genius
