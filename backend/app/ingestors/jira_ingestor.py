# Minimal Jira ingestor skeleton. In production: use OAuth, paging, mapping of users.
import os
import requests
import json
from datetime import date
from ..db import get_driver
from ..scoring import recompute_skill_levels_for_employees

JIRA_BASE = os.getenv('JIRA_BASE', '')
JIRA_USER = os.getenv('JIRA_USER', '')
JIRA_TOKEN = os.getenv('JIRA_TOKEN', '')


def ingest_closed_issues(jql='project = PROJ AND status = Done'):
    url = f'{JIRA_BASE}/rest/api/2/search'
    auth = (JIRA_USER, JIRA_TOKEN) if JIRA_USER else None
    params = {'jql': jql, 'maxResults': 50}

    r = requests.get(url, params=params, auth=auth)
    r.raise_for_status()
    data = r.json()
    issues = data.get('issues', [])

    driver = get_driver()
    processed_issues = 0

    for iss in issues:
        key = iss['key']
        fields = iss['fields']
        reporter = fields.get('reporter', {}).get('name')
        assignee = fields.get('assignee', {}).get('name') if fields.get('assignee') else None
        labels = fields.get('labels', [])

        # Map labels to skills
        updated_emps = set()
        issue_had_skill = False
        for label in labels:
            eid = assignee or reporter
            if not eid:
                continue
            evidence_obj = {
                'url': f'{JIRA_BASE}/browse/{key}',
                'date': date.today().isoformat(),
                'actor': eid,
                'type': 'issue',
                'source': 'jira',
                'id': key
            }
            ev_json = json.dumps(evidence_obj)
            with driver.session() as s:
                # ensure Employee and Skill exist
                s.run("MERGE (e:Empleado {id:$eid}) MERGE (s:Skill {name:$skill})", eid=eid, skill=label)
                # create Evidence node and relationships
                cy = '''
                MERGE (ev:Evidence {uid:$uid})
                SET ev.url = $url, ev.date = $date, ev.actor = $actor, ev.type = $type, ev.source = $source, ev.raw = $raw
                WITH ev
                MATCH (e:Empleado {id:$eid}), (s:Skill {name:$skill})
                MERGE (e)-[he:HAS_EVIDENCE]->(ev)
                MERGE (ev)-[ab:ABOUT]->(s)
                MERGE (e)-[r:DEMUESTRA_COMPETENCIA]->(s)
                SET r.ultimaDemostracion = CASE WHEN $date IS NOT NULL THEN date($date) ELSE r.ultimaDemostracion END
                RETURN ev
                '''
                uid = f"{evidence_obj['source']}:{evidence_obj['id']}" if evidence_obj.get('id') else f"{evidence_obj['source']}:{eid}:{label}:{evidence_obj['url']}"
                s.run(
                    cy,
                    uid=uid,
                    url=evidence_obj['url'],
                    date=evidence_obj['date'],
                    actor=evidence_obj['actor'],
                    type=evidence_obj['type'],
                    source=evidence_obj['source'],
                    raw=ev_json,
                    eid=eid,
                    skill=label,
                )
                updated_emps.add(eid)
                issue_had_skill = True
        # recompute levels for affected employees
        if updated_emps:
            try:
                recompute_skill_levels_for_employees(get_driver(), list(updated_emps))
            except Exception as e:
                print('warning: recompute_skill_levels_for_employees failed for', updated_emps, e)
        if issue_had_skill:
            processed_issues += 1

    return processed_issues
