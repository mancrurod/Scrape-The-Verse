import subprocess

STEPS = [
    # === EXTRACTION ===
    ("🌐 Wikidata Extraction", "src/extraction/wikidata_extraction.py"),
    ("🎧 Spotify Extraction", "src/extraction/spotify_extraction.py"),
    ("🎤 Genius Extraction", "src/extraction/genius_extraction.py"),

    # === TRANSFORMATION ===
    ("🧬 Wikidata Transformation", "src/transformation/wikidata_transformation.py"),
    ("🎛️ Spotify Transformation", "src/transformation/spotify_transformation.py"),
    ("🧼 Genius Transformation", "src/transformation/genius_transformation.py"),

    # === PROCESSING ===
    ("🔗 Join Lyrics + Metadata", "src/process/process.py"),

    # === LOAD ===
    ("🚀 Load to PostgreSQL", "src/load/load.py")
]

def run_step(name, script_path):
    print(f"\n{name}\n{'=' * len(name)}")
    result = subprocess.run(["python", script_path])
    if result.returncode != 0:
        print(f"❌ Failed at: {name}")
        exit(1)
    print(f"✅ Completed: {name}")

def main():
    print("\n🚀 Running Full ETL Pipeline\n" + "=" * 30)
    try:
        for name, script in STEPS:
            run_step(name, script)
        print("\n🎉 ETL Pipeline completed successfully!")
    except KeyboardInterrupt:
        print("\n\n🛑 Pipeline cancelled by user. No worries, the verse will wait. 🎤✨")


if __name__ == "__main__":
    main()
