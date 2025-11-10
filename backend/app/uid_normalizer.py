from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from neo4j import Driver

from .scoring import make_evidence_uid


@dataclass(frozen=True)
class EvidenceRow:
    node_id: int
    uid: Optional[str]
    url: Optional[str]
    date: Optional[str]
    actor: Optional[str]
    source: Optional[str]


def fetch_evidence_rows(driver: Driver) -> List[EvidenceRow]:
    query = (
        "MATCH (ev:Evidence) "
        "RETURN id(ev) AS node_id, ev.uid AS uid, ev.url AS url, ev.date AS date, "
        "ev.actor AS actor, ev.source AS source"
    )
    rows: List[EvidenceRow] = []
    with driver.session() as session:
        for record in session.run(query):
            data = record.data()
            rows.append(
                EvidenceRow(
                    node_id=data["node_id"],
                    uid=data.get("uid"),
                    url=data.get("url"),
                    date=data.get("date"),
                    actor=data.get("actor"),
                    source=data.get("source"),
                )
            )
    return rows


def propose_uid_updates(rows: Sequence[EvidenceRow]) -> Tuple[List[Dict[str, object]], Dict[str, List[int]]]:
    updates: List[Dict[str, object]] = []
    bucket: Dict[str, List[int]] = {}

    for row in rows:
        proposed = make_evidence_uid(row.url, row.date, row.actor)
        bucket.setdefault(proposed, []).append(row.node_id)
        if row.uid != proposed:
            updates.append(
                {
                    "node_id": row.node_id,
                    "current_uid": row.uid,
                    "proposed_uid": proposed,
                    "url": row.url,
                    "date": row.date,
                    "actor": row.actor,
                    "source": row.source,
                }
            )

    duplicates = {uid: node_ids for uid, node_ids in bucket.items() if len(set(node_ids)) > 1}
    return updates, duplicates


def apply_updates(driver: Driver, updates: Iterable[Dict[str, object]], duplicates: Dict[str, List[int]]) -> int:
    blocked_uids = {uid for uid, node_ids in duplicates.items() if len(set(node_ids)) > 1}
    applied = 0
    with driver.session() as session:
        for update in updates:
            if update["proposed_uid"] in blocked_uids:
                continue
            session.run(
                "MATCH (ev:Evidence) WHERE id(ev) = $node_id SET ev.uid = $uid",
                node_id=update["node_id"],
                uid=update["proposed_uid"],
            )
            applied += 1
    return applied
