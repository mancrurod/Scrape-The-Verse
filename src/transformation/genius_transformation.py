from pathlib import Path

def clean_lyrics_folder_recursive(input_base: str, output_base: str) -> None:
    """
    Recursively cleans .txt files with raw lyrics from Genius by removing introductory text,
    including header lines and buttons such as "Read More", until the actual lyrics begin.

    Args:
        input_base (str): Root folder containing raw lyrics, organized by artist/album.
        output_base (str): Destination root folder to save cleaned lyrics, maintaining the original structure.
    """
    input_path = Path(input_base)
    output_path = Path(output_base)

    # Iterate over all .txt files recursively in the input directory
    for txt_file in input_path.rglob("*.txt"):
        relative_path = txt_file.relative_to(input_path)
        output_file = output_path / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Read the raw lyric file
        with open(txt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Try to locate the start of the actual lyrics (after 'Lyrics' header)
        start_index = None
        for i, line in enumerate(lines):
            if "Lyrics" in line:
                start_index = i + 1
                break

        # Skip over "Read More" or empty lines immediately after 'Lyrics'
        if start_index is not None:
            while start_index < len(lines):
                line = lines[start_index].strip()
                if not line or line.endswith("Read More") or line.endswith("Read More "):
                    start_index += 1
                else:
                    break
            cleaned_lines = lines[start_index:]
        else:
            # If no 'Lyrics' header found, keep the original file as-is
            cleaned_lines = lines

        # Write the cleaned lyrics to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)

        print(f"✅ Cleaned: {relative_path}")


def main():
    """
    CLI loop to clean lyrics for multiple artists.
    Prompts the user for artist names and processes their raw Genius lyrics folder.
    Saves cleaned lyrics to a mirrored folder structure under 'transformations/GENIUS/'.
    """
    print("\n🧼 Genius Lyrics Cleaner (multi-artist mode)\n")

    while True:
        # Prompt user for artist name
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting lyrics cleaner. See you next time!\n")
            break
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        input_folder = Path(f"raw/GENIUS/{artist}")
        output_folder = Path(f"transformations/GENIUS/{artist}")

        print(f"🔄 Overwriting cleaned lyrics for '{artist}'...\n")

        if not input_folder.exists():
            print(f"❌ No raw lyrics found for: {artist}\n")
            continue

        # Clean and save lyrics
        clean_lyrics_folder_recursive(str(input_folder), str(output_folder))
        print(f"\n🎉 All lyrics for '{artist}' have been cleaned and saved to: {output_folder}\n")


if __name__ == "__main__":
    main()
