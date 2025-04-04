from pathlib import Path

def get_artist_dirs(base_path="processed"):
    """
    Returns all artist directories within the base path.

    Args:
        base_path (str): The base directory to search for artist folders. Defaults to "processed".

    Returns:
        list[Path]: A list of directories representing artists.
    """
    # Use Path.iterdir() to iterate over the contents of the base path and filter directories
    return [d for d in Path(base_path).iterdir() if d.is_dir()]

def get_artist_metadata_file(artist_dir):
    """
    Returns the metadata file for the artist if it exists.

    Args:
        artist_dir (Path): The directory of the artist.

    Returns:
        Path or None: The metadata file path if found, otherwise None.
    """
    # Look for a file matching the pattern "*_merged_metadata.csv" in the artist directory
    for file in artist_dir.glob("*_merged_metadata.csv"):
        return file  # Return the first match
    return None  # Return None if no match is found

def get_album_csv_files(artist_dir):
    """
    Returns a list of tuples (album_name, album_csv_file) for each album of the artist.

    Args:
        artist_dir (Path): The directory of the artist.

    Returns:
        list[tuple[str, Path]]: A list of tuples where each tuple contains the album name and its CSV file path.
    """
    albums = []
    # Iterate over subdirectories in the artist directory
    for album_dir in artist_dir.iterdir():
        if album_dir.is_dir():  # Check if it's a directory
            # Look for files matching the pattern "*_final.csv" in the album directory
            csv_files = list(album_dir.glob("*_final.csv"))
            if csv_files:  # If CSV files are found
                album_name = album_dir.name  # Use the directory name as the album name
                albums.append((album_name, csv_files[0]))  # Add the album name and the first CSV file
    return albums

def get_all_artist_data(base_path="processed"):
    """
    Returns a list of dictionaries containing artist data.

    Each dictionary has the following structure:
    {
        "artist": str,  # The name of the artist
        "artist_metadata": Path or None,  # The metadata file path for the artist
        "albums": list[dict]  # A list of album data, where each album is represented as:
            {
                "name": str,  # The name of the album
                "csv": Path  # The CSV file path for the album
            }
    }

    Args:
        base_path (str): The base directory to search for artist data. Defaults to "processed".

    Returns:
        list[dict]: A list of dictionaries containing artist data.
    """
    data = []
    # Get all artist directories within the base path
    for artist_dir in get_artist_dirs(base_path):
        # Get the metadata file for the artist
        artist_metadata = get_artist_metadata_file(artist_dir)
        # Get the album data for the artist
        albums = get_album_csv_files(artist_dir)
        if albums:  # Only include the artist if they have albums
            data.append({
                "artist": artist_dir.name,  # Use the directory name as the artist name
                "artist_metadata": artist_metadata,  # Metadata file path (or None)
                "albums": [{"name": name, "csv": csv} for name, csv in albums]  # List of album data
            })
    return data
