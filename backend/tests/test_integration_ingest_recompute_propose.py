import uuid
from datetime import date
from app.db import get_driver
from app.scoring import recompute_skill_levels_for_employees
from app.guardian import propose_teams


def test_ingest_evidence_and_recompute_and_propose():
    driver = get_driver()
    eid = f"test-{uuid.uuid4().hex[:8]}"
    skill = f"skill-{uuid.uuid4().hex[:5]}"
    ev_uid = f"test:{uuid.uuid4().hex[:8]}"
    ev_url = f"http://example.local/{ev_uid}"
    today = date.today().isoformat()

    # create employee, skill, and an Evidence node and link them
    with driver.session() as s:
        s.run("MERGE (e:Empleado {id:$eid, nombre:$name})", eid=eid, name=eid)
        s.run("MERGE (sk:Skill {name:$skill})", skill=skill)
        s.run(
            "MERGE (ev:Evidence {uid:$uid}) SET ev.url=$url, ev.date=$date, ev.actor=$actor, ev.type='test', ev.source='pytest', ev.raw=$raw",
            uid=ev_uid, url=ev_url, date=today, actor='pytest', raw=ev_url
        )
        s.run("MATCH (e:Empleado {id:$eid}), (ev:Evidence {uid:$uid}), (sk:Skill {name:$skill}) MERGE (e)-[:HAS_EVIDENCE]->(ev) MERGE (ev)-[:ABOUT]->(sk) MERGE (e)-[r:DEMUESTRA_COMPETENCIA]->(sk) SET r.nivel = 1.0, r.ultimaDemostracion = date($date)", eid=eid, uid=ev_uid, skill=skill, date=today)

    try:
        # recompute for this employee
        res = recompute_skill_levels_for_employees(driver, [eid])
        assert isinstance(res, dict) and res.get('updated', 0) >= 1

        # call propose_teams to get dossier that should include our employee when skill is required
        payload = {'requisitos_hard': {'skills': [skill]}, 'perfil_mision': 'test', 'k': 1}
        proposals = propose_teams(payload)
        assert isinstance(proposals, list) and len(proposals) > 0
        # check that our employee appears in at least one proposal and evidence is present
        found = False
        for p in proposals:
            for j in p.get('justificaciones', []):
                if j.get('id') == eid:
                    # skills should include our skill with evidences
                    for sk in j.get('skills', []):
                        if sk.get('skill') == skill:
                            evids = sk.get('evidencias', [])
                            assert any((ev.get('url') == ev_url or ev.get('raw') == ev_url) for ev in evids)
                            found = True
        assert found
    finally:
        # cleanup created nodes
        with driver.session() as s:
            s.run("MATCH (e:Empleado {id:$eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill {name:$skill}) DELETE r", eid=eid, skill=skill)
            s.run("MATCH (e:Empleado {id:$eid})-[he:HAS_EVIDENCE]->(ev:Evidence)-[ab:ABOUT]->(s:Skill {name:$skill}) DELETE he, ab", eid=eid, skill=skill)
            s.run("MATCH (ev:Evidence {uid:$uid}) DELETE ev", uid=ev_uid)
            s.run("MATCH (e:Empleado {id:$eid}) DELETE e", eid=eid)
            s.run("MATCH (s:Skill {name:$skill}) DELETE s", skill=skill)
