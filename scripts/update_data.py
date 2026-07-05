"""Update local JSON data for the ETF tracker.

This script is intentionally kept as a placeholder for future data-source integration.
It can be extended to fetch ETF lists, holdings, institution trades, and price history,
then write the normalized output into the data/ directory.
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    print(f"Data directory ready: {DATA_DIR}")
    print("Connect official or licensed data sources here, then write JSON files into data/.")


if __name__ == "__main__":
    main()
