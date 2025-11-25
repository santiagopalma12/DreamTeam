from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .db import driver


def _to_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return None


def _days_since(value: Optional[str]) -> Optional[int]:
    dt = _to_date(value)
    if not dt:
        return None
    return (date.today() - dt).days


def _normalize_evidence(raw_ev: Any) -> Optional[Dict[str, Any]]:
    if not raw_ev:
        return None

    if isinstance(raw_ev, dict):
        ev_dict = raw_ev
    else:
        try:
            ev_dict = dict(raw_ev.items())
        except Exception:
            return None

    return {
        "uid": ev_dict.get("uid") or ev_dict.get("id"),
        "url": ev_dict.get("url"),
        "date": ev_dict.get("date"),
        "actor": ev_dict.get("actor"),
        "source": ev_dict.get("source"),
        "type": ev_dict.get("type"),
        "raw": ev_dict,
    }


def _fetch_skill_rows(team_ids: Sequence[str], driver_instance) -> Iterable[Dict[str, Any]]:
    if not team_ids:
        return []

    query = """
    UNWIND $team AS eid
    MATCH (e:Empleado {id: eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
    OPTIONAL MATCH (e)-[:HAS_EVIDENCE]->(ev:Evidence)-[:ABOUT]->(s)
    WITH eid, e, s, r, collect(ev) AS evidence_nodes
    RETURN eid AS employee_id,
           e.nombre AS employee_name,
           e.rol AS employee_role,
           s.name AS skill,
           r.nivel AS nivel,
           r.ultimaDemostracion AS ultima,
           r.validadoPor AS validado_por,
           evidence_nodes
    ORDER BY skill, employee_name
    """

    with driver_instance.session() as session:
        records = session.run(query, team=list(team_ids))
        for record in records:
            evidences = []
            for node in record.get("evidence_nodes", []) or []:
                normalized = _normalize_evidence(node)
                if normalized:
                    evidences.append(normalized)

            yield {
                "employee_id": record.get("employee_id"),
                "employee_name": record.get("employee_name"),
                "employee_role": record.get("employee_role"),
                "skill": record.get("skill"),
                "nivel": record.get("nivel") or 0.0,
                "ultima": record.get("ultima"),
                "validado_por": record.get("validado_por"),
                "evidences": evidences,
            }


def build_dossier(
    team_ids: Sequence[str],
    mission_profile: Optional[str] = None,
    *,
    evidence_limit: int = 5,
    driver_instance=None,
) -> Dict[str, Any]:
    """Aggregate evidence details per skill for the given team."""

    driver_instance = driver_instance or driver
    rows = list(_fetch_skill_rows(team_ids, driver_instance))

    skill_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    member_registry: Dict[str, Dict[str, Optional[str]]] = {}
    total_sources: Counter[str] = Counter()
    total_evidences = 0
    frequency_values: List[int] = []
    latest_dates: List[date] = []

    for row in rows:
        evidences = sorted(
            row.get("evidences", []),
            key=lambda ev: ev.get("date") or "",
            reverse=True,
        )
        frequency = len(evidences)
        frequency_values.append(frequency)
        total_evidences += frequency

        sources = Counter()
        for ev in evidences:
            src = ev.get("source") or "unknown"
            sources[src] += 1
            total_sources[src] += 1

            ev_date = _to_date(ev.get("date"))
            if ev_date:
                latest_dates.append(ev_date)

        latest = evidences[0]["date"] if evidences else row.get("ultima")
        recency_days = _days_since(latest) if latest else None
        if latest:
            dt = _to_date(latest)
            if dt:
                latest_dates.append(dt)

        contributor = {
            "employee_id": row.get("employee_id"),
            "employee_name": row.get("employee_name") or row.get("employee_id"),
            "employee_role": row.get("employee_role"),
            "nivel": row.get("nivel") or 0.0,
            "ultima_demostracion": row.get("ultima"),
            "recency_days": recency_days,
            "frequency": frequency,
            "validated_by": row.get("validado_por"),
            "sources": dict(sources),
            "evidences": evidences[:evidence_limit] if evidence_limit else evidences,
        }

        skill_key = row.get("skill") or "unknown"
        skill_groups[skill_key].append(contributor)

        employee_id = row.get("employee_id")
        if employee_id and employee_id not in member_registry:
            member_registry[employee_id] = {
                "id": employee_id,
                "name": row.get("employee_name") or employee_id,
                "role": row.get("employee_role"),
            }

    skills_payload = []
    for skill, contributors in sorted(skill_groups.items(), key=lambda item: item[0]):
        skill_sources = Counter()
        for contributor in contributors:
            skill_sources.update(contributor.get("sources", {}))

        skills_payload.append(
            {
                "skill": skill,
                "sources": dict(skill_sources),
                "contributors": contributors,
            }
        )

    average_frequency = (
        round(total_evidences / max(1, len(frequency_values)), 2)
        if frequency_values
        else 0.0
    )
    min_frequency = min(frequency_values) if frequency_values else 0
    latest_dt = max(latest_dates) if latest_dates else None

    generated_at = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    summary = {
        "team_size": len(set(team_ids)),
        "skill_count": len(skills_payload),
        "total_evidences": total_evidences,
        "average_frequency": average_frequency,
        "min_frequency": min_frequency,
        "source_breakdown": dict(total_sources),
        "generated_at": generated_at,
        "latest_evidence": latest_dt.isoformat() if latest_dt else None,
    }

    return {
        "mission_profile": mission_profile,
        "team": list(dict.fromkeys(team_ids)),
        "members": list(member_registry.values()),
        "skills": skills_payload,
        "summary": summary,
    }
