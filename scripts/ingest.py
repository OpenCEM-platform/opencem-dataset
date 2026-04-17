#!/usr/bin/env python3
"""
OpenCEM Data Ingestion Script

Exports new data from a local SQLite database into monthly CSV partitions
ready to be committed and pushed to the opencem-dataset repo.

Usage:
    python scripts/ingest.py --db /path/to/opencem_dataset.db

What it does:
    1. Reads the current data/ directory to find the latest timestamp already exported
    2. Queries the SQLite database for all records after that timestamp
    3. Writes new records into monthly CSV partitions under data/measurements/ and data/context/
    4. Prints a summary of what was added

After running, commit and push:
    git add data/
    git commit -m "Data update: $(date +%Y-%m-%d)"
    git push
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MEASUREMENTS_DIR = REPO_ROOT / "data" / "measurements"
CONTEXT_DIR = REPO_ROOT / "data" / "context"


def get_latest_timestamp(data_dir: Path) -> int:
    """Find the latest timestamp already in the exported CSVs."""
    latest = 0
    if not data_dir.exists():
        return latest

    for csv_file in sorted(data_dir.glob("*.csv"), reverse=True):
        # Read the last few lines of the most recent file
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                continue
            ts_idx = 0  # read_ts or recorded is always first column
            last_row = None
            for row in reader:
                last_row = row
            if last_row:
                try:
                    latest = max(latest, int(last_row[ts_idx]))
                except (ValueError, IndexError):
                    pass
        if latest > 0:
            break

    return latest


MAX_FILE_SIZE = 90 * 1024 * 1024  # 90 MB — stay under GitHub's 100 MB limit


def export_measurements(conn: sqlite3.Connection, after_ts: int) -> int:
    """Export new measurement rows into monthly CSV partitions. Returns count.

    If a monthly file would exceed 90 MB, it is automatically split into
    half-month parts (YYYY-MM-a.csv for days 1-15, YYYY-MM-b.csv for 16+).
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(analog_measurements)")
    columns = [row[1] for row in cur.fetchall()]

    cur.execute(
        "SELECT * FROM analog_measurements WHERE read_ts > ? ORDER BY read_ts",
        (after_ts,),
    )

    MEASUREMENTS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    open_files = {}  # file_key -> (file_handle, csv_writer)

    try:
        for row in cur:
            ts = row[0]
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            # Split into half-months to stay under GitHub's 100 MB file limit
            half = "a" if dt.day <= 15 else "b"
            file_key = f"{dt.strftime('%Y-%m')}-{half}"

            if file_key not in open_files:
                filepath = MEASUREMENTS_DIR / f"{file_key}.csv"
                file_exists = filepath.exists() and filepath.stat().st_size > 0
                fh = open(filepath, "a", newline="")
                writer = csv.writer(fh)
                if not file_exists:
                    writer.writerow(columns)
                open_files[file_key] = (fh, writer)

            _, writer = open_files[file_key]
            writer.writerow(row)
            count += 1

            if count % 50000 == 0:
                print(f"  ... exported {count:,} measurement rows")
    finally:
        for fh, _ in open_files.values():
            fh.close()

    return count


def export_context(conn: sqlite3.Connection, after_ts: int) -> int:
    """Export new context rows into monthly CSV partitions. Returns count."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(context)")
    columns = [row[1] for row in cur.fetchall()]

    cur.execute(
        "SELECT * FROM context WHERE recorded > ? ORDER BY recorded",
        (after_ts,),
    )

    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    open_files = {}

    try:
        for row in cur:
            # recorded is the second column (id, recorded, start, end, value)
            ts = row[1]
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            month_key = dt.strftime("%Y-%m")

            if month_key not in open_files:
                filepath = CONTEXT_DIR / f"{month_key}.csv"
                file_exists = filepath.exists() and filepath.stat().st_size > 0
                fh = open(filepath, "a", newline="")
                writer = csv.writer(fh)
                if not file_exists:
                    writer.writerow(columns)
                open_files[month_key] = (fh, writer)

            _, writer = open_files[month_key]
            writer.writerow(row)
            count += 1
    finally:
        for fh, _ in open_files.values():
            fh.close()

    return count


def main():
    parser = argparse.ArgumentParser(description="Export new OpenCEM data to CSV partitions")
    parser.add_argument("--db", required=True, help="Path to the SQLite database")
    parser.add_argument("--full", action="store_true", help="Export all data (ignore existing CSVs)")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"Error: Database not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.db)

    # Find what we already have
    if args.full:
        meas_after = 0
        ctx_after = 0
        print("Full export mode: exporting all data")
    else:
        meas_after = get_latest_timestamp(MEASUREMENTS_DIR)
        ctx_after = get_latest_timestamp(CONTEXT_DIR)
        if meas_after > 0:
            print(f"Last measurement: {datetime.fromtimestamp(meas_after, tz=timezone.utc)}")
        if ctx_after > 0:
            print(f"Last context:     {datetime.fromtimestamp(ctx_after, tz=timezone.utc)}")

    # Export
    print("\nExporting measurements...")
    m_count = export_measurements(conn, meas_after)
    print(f"  Added {m_count:,} measurement rows")

    print("Exporting context records...")
    c_count = export_context(conn, ctx_after)
    print(f"  Added {c_count:,} context records")

    conn.close()

    if m_count == 0 and c_count == 0:
        print("\nNo new data to export.")
    else:
        print(f"\nDone! Now commit and push:")
        print(f"  git add data/")
        print(f'  git commit -m "Data update: {datetime.now().strftime("%Y-%m-%d")}"')
        print(f"  git push")


if __name__ == "__main__":
    main()
