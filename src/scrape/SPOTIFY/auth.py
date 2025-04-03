import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy

def load_credentials():
    """
    Load Spotify API credentials from a .env file and validate them.
    
    Returns:
        tuple: A tuple containing client_id, client_secret, and redirect_uri.
    
    Raises:
        Exception: If any of the required credentials are missing.
    """
    # Construct the path to the .env file
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    load_dotenv(dotenv_path)

    # Load credentials from environment variables
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    # Validate credentials
    if not client_id or not client_secret or not redirect_uri:
        raise Exception("Missing Spotify credentials in .env")

    # Handle deprecated or incomplete redirect URIs
    if 'localhost' in redirect_uri:
        port = redirect_uri.split(':')[-1] if ':' in redirect_uri.split('//')[1] else '8080'
        redirect_uri = f"http://127.0.0.1:{port}"
        print(f"⚠️ Warning: 'localhost' is deprecated. Using '{redirect_uri}' instead")
    elif '127.0.0.1' in redirect_uri and ':' not in redirect_uri.split('//')[1]:
        redirect_uri = "http://127.0.0.1:8080"
        print(f"⚠️ Warning: No port specified in redirect URI. Using '{redirect_uri}'")

    # Log the final redirect URI
    print(f"🔗 Using redirect URI: {redirect_uri}")
    return client_id, client_secret, redirect_uri

def connect_to_spotify():
    """
    Authenticate and connect to the Spotify API using Spotipy.
    
    Returns:
        spotipy.Spotify: An authenticated Spotipy client instance.
    
    Raises:
        Exception: If connection verification fails.
    """
    # Load credentials and set up the authentication manager
    client_id, client_secret, redirect_uri = load_credentials()
    scope = "user-library-read user-read-private playlist-read-private"
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,
        cache_path=".spotify_cache"  # Cache token to avoid re-authentication
    )

    # Create a Spotipy client instance
    sp = spotipy.Spotify(auth_manager=auth_manager)
    try:
        # Verify connection by fetching the current user's information
        user_info = sp.current_user()
        print(f"✅ Connected as: {user_info['display_name']}")
    except Exception as e:
        print(f"⚠️ Connection verification failed: {e}")
        raise
    return sp
