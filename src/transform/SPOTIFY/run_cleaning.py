# ================================================================
# 📝 IMPORTANT:
# This script must be run from the project root like this:
#
#     python -m src.transform.SPOTIFY.run_cleaning
#
# DO NOT run it directly (e.g., `python run_cleaning`)
# or you'll get ModuleNotFoundError due to package context.
# ================================================================

from src.transform.SPOTIFY.clean_metadata import run_transformation

def main():
    run_transformation()


if __name__ == "__main__":
    main()