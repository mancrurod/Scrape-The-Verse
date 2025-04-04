import pandas as pd
from pathlib import Path
from datetime import datetime

def parse_artist_csv(artist_csv_path: Path) -> dict:
    """
    Parses a CSV file containing artist information and returns a dictionary with the artist's details.

    Args:
        artist_csv_path (Path): Path to the CSV file containing artist data.

    Returns:
        dict: A dictionary with the artist's details, including name, birth name, birth date, etc.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(artist_csv_path)

    # Only take the first row (one artist per file)
    row = df.iloc[0]
    return {
        "name": row.get("Name"),  # Artist's name
        "birth_name": row.get("BirthName"),  # Artist's birth name
        "birth_date": _parse_date(row.get("DateOfBirth")),  # Artist's birth date
        "birth_place": row.get("PlaceOfBirth"),  # Artist's place of birth
        "country": row.get("CountryOfCitizenship"),  # Artist's country of citizenship
        "active_years": _parse_year(row.get("WorkPeriodStart")),  # Start year of artist's active period
        "genres": _combine_fields(row, ["GenresWikidata", "GenresSpotify"]),  # Combined genres from multiple sources
        "instruments": row.get("Instruments"),  # Instruments played by the artist
        "vocal_type": row.get("VoiceType"),  # Artist's vocal type
    }

def parse_album_csv(album_csv_path: Path, artist_id: int) -> tuple[dict, list[dict]]:
    """
    Parses a CSV file containing album and track information and returns album metadata and track details.

    Args:
        album_csv_path (Path): Path to the CSV file containing album and track data.
        artist_id (int): ID of the artist associated with the album.

    Returns:
        tuple[dict, list[dict]]: A tuple containing:
            - A dictionary with album metadata.
            - A list of dictionaries with track details.
    """
    # Read the CSV file into a DataFrame
    df = pd.read_csv(album_csv_path)
    # Replace NaN values with empty strings
    df.fillna("", inplace=True)

    # Extract album metadata from the first row
    first = df.iloc[0]
    album_data = {
        "name": first["AlbumName"],  # Album name
        "artist_id": artist_id,  # Associated artist ID
        "release_date": _parse_date(first["ReleaseDateAlbum"]),  # Album release date
        "popularity": int(first["AlbumPopularity"]),  # Album popularity score
    }

    # Extract track details
    tracks_data = []
    for _, row in df.iterrows():
        tracks_data.append({
            "name": row["SongName"],  # Track name
            "track_number": int(row["TrackNumber"]),  # Track number in the album
            "duration_ms": int(row["DurationMs"]),  # Track duration in milliseconds
            "explicit": bool(row["Explicit"]),  # Whether the track is explicit
            "popularity": int(row["SongPopularity"]),  # Track popularity score
            "lyrics": row["Lyrics"],  # Track lyrics
        })

    return album_data, tracks_data

# Internal utilities
def _parse_date(date_str):
    """
    Parses a date string in the format 'YYYY-MM-DD' and returns a date object.

    Args:
        date_str (str): Date string to parse.

    Returns:
        datetime.date or None: Parsed date object, or None if parsing fails.
    """
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except Exception:
        return None

def _parse_year(year_str):
    """
    Parses a year string and returns it as an integer.

    Args:
        year_str (str): Year string to parse.

    Returns:
        int or None: Parsed year as an integer, or None if parsing fails.
    """
    try:
        return int(str(year_str))
    except Exception:
        return None

def _combine_fields(row, fields):
    """
    Combines values from multiple fields in a row into a single string, separated by commas.

    Args:
        row (pd.Series): A row from a DataFrame.
        fields (list[str]): List of field names to combine.

    Returns:
        str: Combined string of non-empty field values.
    """
    # Extract non-empty values from the specified fields
    values = [str(row[f]) for f in fields if pd.notna(row.get(f)) and row.get(f)]
    return ", ".join(values)  # Join the values with commas
