# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.scrape.WIKIDATA.main_wikidata_scrap
#
# DO NOT run it directly (e.g., `python main_wikidata_scrap.py`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.scrape.WIKIDATA.get_info import fetch_artist_data_from_wikidata
import pandas as pd
from pathlib import Path


def main():
    artist = input("Enter the artist's name: ").strip()
    info = fetch_artist_data_from_wikidata(artist)

    if info:
        df = pd.DataFrame([info])
        output_path = Path(f"raw/WIKIDATA/{artist}/wikidata_summary.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Data saved to {output_path}")
        print(df)
    else:
        print("❌ No data extracted.")


if __name__ == "__main__":
    main()
