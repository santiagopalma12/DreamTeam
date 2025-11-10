"""Utility CLI to assign deterministic uid values to Evidence nodes."""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Sequence

from neo4j import Driver, GraphDatabase

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

from app.uid_normalizer import (  # noqa: E402
    apply_updates,
    fetch_evidence_rows,
    propose_uid_updates,
)


def export_csv(path: Path, updates: Sequence[Dict[str, object]]) -> None:
    fieldnames = ["node_id", "current_uid", "proposed_uid", "url", "date", "actor", "source"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for update in updates:
            writer.writerow(update)


def build_driver_from_env() -> Driver:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASS", "neo4j")
    return GraphDatabase.driver(uri, auth=(user, password))


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Evidence.uid values")
    parser.add_argument("--apply", action="store_true", help="Persist the new uid values")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt when using --apply")
    parser.add_argument("--export-csv", dest="export_csv", help="Write proposed updates to the given CSV path")
    parser.add_argument(
        "--log-level",
        default=os.getenv("NORMALIZE_UID_LOG", "INFO"),
        help="Logging level (default: INFO)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="[%(levelname)s] %(message)s")

    driver = build_driver_from_env()
    try:
        rows = fetch_evidence_rows(driver)
        updates, duplicates = propose_uid_updates(rows)
    finally:
        driver.close()

    logging.info("Scanned %s Evidence nodes", len(rows))
    logging.info("Proposed updates: %s", len(updates))
    if duplicates:
        logging.warning("Detected %s conflicting uid(s)", len(duplicates))
        for uid, node_ids in duplicates.items():
            logging.warning("uid %s shared by node ids %s", uid, sorted(set(node_ids)))

    if args.export_csv:
        export_path = Path(args.export_csv)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_csv(export_path, updates)
        logging.info("Exported proposed updates to %s", export_path)

    if args.apply:
        if duplicates:
            logging.warning("Updates with colliding uids will be skipped; review CSV before manual cleanup")
        if not args.yes:
            confirmation = input("Type YES to apply the proposed uid updates: ")
            if confirmation.strip().upper() != "YES":
                logging.info("Aborted by user")
                return 0
        driver = build_driver_from_env()
        try:
            applied = apply_updates(driver, updates, duplicates)
        finally:
            driver.close()
        logging.info("Applied %s updates", applied)
    else:
        logging.info("Dry run complete (use --apply to persist changes)")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
