from pathlib import Path

def clean_lyrics_folder_recursive(input_base: str, output_base: str) -> None:
    """
    Cleans .txt files with song lyrics obtained from Genius by removing
    introductory lines before the actual content (up to the line containing 'Lyrics').

    Args:
        input_base (str): Root folder with raw lyrics organized by artist/album.
        output_base (str): Root folder where cleaned lyrics will be saved, maintaining the structure.
    """
    input_path = Path(input_base)
    output_path = Path(output_base)

    for txt_file in input_path.rglob("*.txt"):
        relative_path = txt_file.relative_to(input_path)
        output_file = output_path / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(txt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the line containing 'Lyrics'
        start_index = None
        for i, line in enumerate(lines):
            if "Lyrics" in line:
                start_index = i + 1
                break

        # Skip possible descriptions like "... Read More" after 'Lyrics'
        if start_index is not None:
            while start_index < len(lines):
                line = lines[start_index].strip()
                if not line or line.endswith("Read More") or line.endswith("Read More "):
                    start_index += 1
                else:
                    break
            cleaned_lines = lines[start_index:]
        else:
            cleaned_lines = lines

        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)

        print(f"✅ Cleaned: {relative_path}")


def main():
    print("\n🧼 Genius Lyrics Cleaner (multi-artist mode)\n")

    while True:
        artist = input("🎤 Enter artist name (or type 'exit' to quit): ").strip()
        if artist.lower() == "exit":
            print("\n👋 Exiting lyrics cleaner. See you next time!\n")
            break
        if not artist:
            print("⚠️ Please enter a valid artist name.\n")
            continue

        input_folder = Path(f"raw/GENIUS/{artist}")
        output_folder = Path(f"transformations/GENIUS/{artist}")

        # Always re-clean lyrics, even if output already exists
        print(f"🔄 Overwriting cleaned lyrics for '{artist}'...\n")

        if not input_folder.exists():
            print(f"❌ No raw lyrics found for: {artist}\n")
            continue

        clean_lyrics_folder_recursive(str(input_folder), str(output_folder))
        print(f"\n🎉 All lyrics for '{artist}' have been cleaned and saved to: {output_folder}\n")


if __name__ == "__main__":
    main()
