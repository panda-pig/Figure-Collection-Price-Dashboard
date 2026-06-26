from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import engine, import_prices


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "price_records.csv"
    with engine.begin() as db:
        import_prices(db, csv_path)
    print(f"Imported prices from {csv_path}")


if __name__ == "__main__":
    main()
