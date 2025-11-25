"""Operational pipeline helpers to run ingestion, normalize evidence and recompute scores."""

from __future__ import annotations

import argparse
import json
import logging
from typing import Dict, Iterable, Sequence

from ..db import get_driver
from ..scoring import recompute_all_skill_levels
from ..uid_normalizer import apply_updates, fetch_evidence_rows, propose_uid_updates
from .run import run_sources

logger = logging.getLogger(__name__)


def _normalize_evidence_uids() -> Dict[str, object]:
    driver = get_driver()
    rows = fetch_evidence_rows(driver)
    updates, duplicates = propose_uid_updates(rows)

    # keep only true duplicates (same uid assigned to multiple node ids)
    blocking_duplicates = {uid: sorted(set(node_ids)) for uid, node_ids in duplicates.items() if len(set(node_ids)) > 1}
    applied = apply_updates(driver, updates, blocking_duplicates)

    return {
        "scanned": len(rows),
        "proposed": len(updates),
        "applied": applied,
        "blocked": {uid: ids for uid, ids in blocking_duplicates.items()},
    }


def run_pipeline(
    sources: Iterable[str],
    *,
    max_commits: int | None = None,
    skip_normalization: bool = False,
    skip_recompute: bool = False,
) -> Dict[str, object]:
    summary: Dict[str, object] = {}

    ingest_summary = run_sources(sources, max_commits=max_commits)
    summary["ingest"] = ingest_summary
    logger.info("Ingestion summary: %s", json.dumps(ingest_summary))

    if not skip_normalization:
        normalization = _normalize_evidence_uids()
        summary["normalize"] = normalization
        logger.info("Normalization summary: %s", json.dumps(normalization))
    else:
        logger.info("Skipping evidence uid normalization")

    if not skip_recompute:
        recompute = recompute_all_skill_levels(get_driver())
        summary["recompute"] = recompute
        logger.info("Recompute summary: %s", json.dumps(recompute))
    else:
        logger.info("Skipping skill level recompute")

    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run nightly ingestion + normalization + recompute pipeline")
    parser.add_argument(
        "--sources",
        default="github",
        help="Comma separated sources to run (defaults to 'github'). Order respected.",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        help="Optional limit for GitHub commits per repo (overrides env)",
    )
    parser.add_argument(
        "--skip-normalization",
        action="store_true",
        help="Skip UID normalization step",
    )
    parser.add_argument(
        "--skip-recompute",
        action="store_true",
        help="Skip skill recompute step",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (INFO, DEBUG, ...)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> Dict[str, object]:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="[%(levelname)s] %(message)s")

    sources = [src.strip() for src in args.sources.split(",") if src.strip()]
    if not sources:
        logger.warning("No sources specified; nothing to execute")
        return {}

    summary = run_pipeline(
        sources,
        max_commits=args.max_commits,
        skip_normalization=args.skip_normalization,
        skip_recompute=args.skip_recompute,
    )
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":  # pragma: no cover
    main()
