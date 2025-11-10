from datetime import date
import hashlib
import json
import math
from typing import List, Optional, Union


def _parse_evidence_date(ev) -> Optional[str]:
    """Try to extract an ISO date string (YYYY-MM-DD) from an evidence item.
    Evidence may be a string (old format) or a dict with keys like 'date', 'fecha' or 'created_at'.
    Returns date string or None.
    """
    if not ev:
        return None
    # string legacy format: no date
    if isinstance(ev, str):
        # legacy: plain URL string, or JSON-serialized object
        s = ev.strip()
        if s.startswith('{') and s.endswith('}'):
            try:
                obj = json.loads(s)
                # recursively try dict branch
                return _parse_evidence_date(obj)
            except Exception:
                return None
        return None
    if isinstance(ev, dict):
        for k in ('date', 'fecha', 'created_at', 'when'):
            if k in ev and ev[k]:
                # accept already ISO date or full datetime
                v = str(ev[k])
                try:
                    # if contains 'T' assume datetime
                    if 'T' in v:
                        return v.split('T')[0]
                    return v[:10]
                except Exception:
                    continue
    return None

def _days_since(d: Optional[str]) -> Optional[int]:
    if not d:
        return None
    try:
        # Neo4j date may be returned as string 'YYYY-MM-DD'
        dt = date.fromisoformat(str(d))
        return (date.today() - dt).days
    except Exception:
        return None

def _compute_freq_score(count: int) -> float:
    """Log-based saturation so that >10 evidences quickly approach max contribution."""
    if count <= 0:
        return 0.0
    score = math.log(1 + count) / math.log(1 + 10)
    return min(1.0, score)


def _compute_recency_score(days_since: Optional[int]) -> float:
    """Map recency into [0,1]; fall back to conservative default when unknown."""
    if days_since is None:
        return 0.2
    return max(0.0, 1.0 - (days_since / 365.0))


def make_evidence_uid(url: Optional[str], when: Optional[str], actor: Optional[str]) -> str:
    """Generate deterministic uid `evidence-{sha1(url|date|actor)}`; tolerate missing fields."""
    parts = [url or '', when or '', actor or '']
    payload = '|'.join(parts)
    digest = hashlib.sha1(payload.encode('utf-8')).hexdigest()
    return f"evidence-{digest}"


def compute_skill_level_from_relation(evidences: Optional[List[Union[str, dict]]], ultima: Optional[str]) -> float:
    """
    Compute a level in range [1.0, 5.0] from evidences list and last demonstration date.

    Simple, transparent formula (configurable later):
      - freq_score = log(1 + n_evidences) / log(1 + 10)  (saturates at ~10 evidences)
      - recency_score = max(0, 1 - days/365)
      - combine = 0.6*freq_score + 0.4*recency_score
      - level = 1 + 4 * combine

    Returns a float rounded to 2 decimals.
    """
    # Support evidences as list of strings (legacy) or list of objects with dates
    n = len(evidences) if evidences else 0
    freq_score = _compute_freq_score(n)

    # If ultima not provided, try to infer latest date from evidence objects
    inferred_ultima = None
    if not ultima and evidences:
        dates = []
        for ev in evidences:
            d = _parse_evidence_date(ev)
            if d:
                dates.append(d)
        if dates:
            inferred_ultima = max(dates)

    days = _days_since(ultima or inferred_ultima)
    recency_score = _compute_recency_score(days)

    combine = 0.6 * freq_score + 0.4 * recency_score
    level = 1.0 + 4.0 * combine
    # clamp
    level = max(1.0, min(5.0, level))
    return round(level, 2)


def recompute_all_skill_levels(driver):
    """
    Iterate over all DEMUESTRA_COMPETENCIA relationships and recompute `r.nivel` based on evidences and ultimaDemostracion.
    Writes the value back into the relationship.
    """
    # Prefer evidence nodes when present; fall back to relationship property r.evidencias (legacy)
    cypher_read = """
    MATCH (e:Empleado)-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
    OPTIONAL MATCH (e)-[:HAS_EVIDENCE]->(ev:Evidence)-[:ABOUT]->(s)
    WITH e, r, s, collect(CASE WHEN ev IS NULL THEN NULL ELSE {url:ev.url, date:ev.date, actor:ev.actor, source:ev.source, id:ev.uid, raw:ev.raw} END) AS evs
    RETURN e.id AS eid, s.name AS skill, evs AS evidencias_nodes, r.evidencias AS evidencias_legacy, r.ultimaDemostracion AS ultima
    """

    update_q = """
    MATCH (e:Empleado {id:$eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill {name:$skill})
    SET r.nivel = $nivel, r._nivel_computed_at = date()
    RETURN r
    """

    with driver.session() as s:
        res = s.run(cypher_read)
        count = 0
        for r in res:
            eid = r['eid']
            skill = r['skill']
            evidencias_nodes = r.get('evidencias_nodes') or []
            evidencias_legacy = r.get('evidencias_legacy') or []
            # prefer nodes; if none, use legacy list
            evidencias = []
            if evidencias_nodes and any(e for e in evidencias_nodes if e is not None):
                for ev in evidencias_nodes:
                    if not ev:
                        continue
                    evidencias.append(ev)
            else:
                # legacy entries may be URL strings or JSON strings
                evidencias = evidencias_legacy
            ultima = r.get('ultima')
            nivel = compute_skill_level_from_relation(evidencias, ultima)
            s.run(update_q, eid=eid, skill=skill, nivel=nivel)
            count += 1
    return { 'updated': count }


def recompute_skill_levels_for_employees(driver, employee_ids: List[str]):
    """
    Recompute r.nivel only for DEMUESTRA_COMPETENCIA relationships where the employee is in employee_ids.
    """
    if not employee_ids:
        return { 'updated': 0 }

    cypher_read = """
    UNWIND $ids AS eid
    MATCH (e:Empleado {id:eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
    OPTIONAL MATCH (e)-[:HAS_EVIDENCE]->(ev:Evidence)-[:ABOUT]->(s)
    WITH e, r, s, collect(CASE WHEN ev IS NULL THEN NULL ELSE {url:ev.url, date:ev.date, actor:ev.actor, source:ev.source, id:ev.uid, raw:ev.raw} END) AS evs
    RETURN e.id AS eid, s.name AS skill, evs AS evidencias_nodes, r.evidencias AS evidencias_legacy, r.ultimaDemostracion AS ultima
    """

    update_q = """
    MATCH (e:Empleado {id:$eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill {name:$skill})
    SET r.nivel = $nivel, r._nivel_computed_at = date()
    RETURN r
    """

    with driver.session() as s:
        res = s.run(cypher_read, ids=employee_ids)
        count = 0
        for r in res:
            eid = r['eid']
            skill = r['skill']
            evidencias_nodes = r.get('evidencias_nodes') or []
            evidencias_legacy = r.get('evidencias_legacy') or []
            evidencias = []
            if evidencias_nodes and any(e for e in evidencias_nodes if e is not None):
                for ev in evidencias_nodes:
                    if not ev:
                        continue
                    evidencias.append(ev)
            else:
                evidencias = evidencias_legacy
            ultima = r.get('ultima')
            nivel = compute_skill_level_from_relation(evidencias, ultima)
            s.run(update_q, eid=eid, skill=skill, nivel=nivel)
            count += 1
    return { 'updated': count }
