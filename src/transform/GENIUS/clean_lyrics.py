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
