from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import DATABASE, import_figures


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "figures.csv"
    db = sqlite3.connect(DATABASE)
    import_figures(db, csv_path)
    db.commit()
    db.close()
    print(f"Imported figures from {csv_path}")


if __name__ == "__main__":
    main()
