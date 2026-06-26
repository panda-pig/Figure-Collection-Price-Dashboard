from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import engine, import_figures


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "figures.csv"
    with engine.begin() as db:
        import_figures(db, csv_path)
    print(f"Imported figures from {csv_path}")


if __name__ == "__main__":
    main()
