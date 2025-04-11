from pathlib import Path
from typing import Optional

# ===========================
# === CLEANING FUNCTION  ===
# ===========================

def clean_lyrics_folder_recursive(input_base: str, output_base: str) -> None:
    """
    Recursively clean raw .txt lyrics files from Genius by removing non-lyrical
    headers and extraneous elements like "Read More" buttons.

    Args:
        input_base (str): Root directory containing raw lyrics (organized by artist/album).
        output_base (str): Output directory where cleaned lyrics will be saved.
    """
    # Convert input and output base paths to Path objects
    input_path = Path(input_base)
    output_path = Path(output_base)

    # Recursively iterate through all .txt files in input directory
    for txt_file in input_path.rglob("*.txt"):
        # Compute relative path to preserve folder structure in output
        relative_path = txt_file.relative_to(input_path)
        output_file = output_path / relative_path

        # Ensure target directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Read the raw lines from the file
        with txt_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        start_index: Optional[int] = None

        # Identify the line after the "Lyrics" marker (usually marks start of actual lyrics)
        for i, line in enumerate(lines):
            if "Lyrics" in line:
                start_index = i + 1
                break

        if start_index is not None:
            # Skip empty lines or non-lyrical leftovers like "Read More"
            while start_index < len(lines):
                line = lines[start_index].strip()
                if not line or line.endswith("Read More") or line.endswith("Read More\xa0"):
                    start_index += 1
                else:
                    break
            # Keep only the actual lyrics from the identified start index
            cleaned_lines = lines[start_index:]
        else:
            # If no marker found, keep all content (as fallback)
            cleaned_lines = lines

        # Write cleaned lyrics to output file, preserving folder structure
        with output_file.open("w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)

        # Log progress
        print(f"✅ Cleaned: {relative_path}")


# =========================
# === CLI ENTRY POINT  ===
# =========================

def main() -> None:
    """
    Command-line interface to clean lyrics for multiple artists.
    Prompts the user for artist names, then cleans and saves lyrics into
    the 'transformations/GENIUS/' folder, preserving structure.
    """
    print("\n🧼 Genius Lyrics Cleaner (multi-artist mode)\n")

    while True:
        # Prompt user for artist name or exit command
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting lyrics cleaner. See you next time!\n")
            break

        # Warn if input is empty
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        # Define input and output folder paths for the given artist
        input_folder = Path(f"raw/GENIUS/{artist}")
        output_folder = Path(f"transformations/GENIUS/{artist}")

        # Check if input folder exists
        if not input_folder.exists():
            print(f"❌ No raw lyrics found for: {artist}\n")
            continue

        # Inform user that cleaning is starting
        print(f"🔄 Overwriting cleaned lyrics for '{artist}'...\n")

        # Run cleaning routine
        clean_lyrics_folder_recursive(str(input_folder), str(output_folder))

        # Confirm completion
        print(f"\n🎉 All lyrics for '{artist}' have been cleaned and saved to: {output_folder}\n")


if __name__ == "__main__":
    main()
