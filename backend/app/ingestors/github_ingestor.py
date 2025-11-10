import os
import requests
import json
from ..db import get_driver
from dateutil import parser
from ..scoring import recompute_skill_levels_for_employees

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# Minimal extractor: fetch recent commits by author in a repo, map file extensions -> skills
EXTENSION_SKILL_MAP = {
    '.java': 'Java',
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tf': 'Terraform',
    'Dockerfile': 'Docker',
    '.yml': 'YAML',
}


def map_files_to_skills(files):
    skills = set()
    for f in files:
        fname = f.get('filename', '')
        for ext, skill in EXTENSION_SKILL_MAP.items():
            if fname.endswith(ext) or (ext == 'Dockerfile' and 'Dockerfile' in fname):
                skills.add(skill)
    return list(skills)


def ingest_commit(repo_fullname, commit_sha, author_login):
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
    url = f'https://api.github.com/repos/{repo_fullname}/commits/{commit_sha}'
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    files = data.get('files', [])
    skills = map_files_to_skills(files)
    commit_url = data.get('html_url')
    date = data.get('commit', {}).get('committer', {}).get('date')

    # Insert evidence rows into Neo4j as objects (url, date, actor, type, id)
    driver = get_driver()
    evidence_obj = {
        'url': commit_url,
        'date': (date[:10] if date else None),
        'actor': author_login,
        'type': 'commit',
        'source': 'github',
        'id': commit_sha
    }
    evidence_json = json.dumps(evidence_obj)
    with driver.session() as s:
        for sk in skills:
            # ensure Employee and Skill exist
            s.run("MERGE (e:Empleado {id:$eid}) MERGE (s:Skill {name:$skill})", eid=author_login, skill=sk)
            # create or update Evidence node and relationships
            cy = '''
            MERGE (ev:Evidence {uid:$uid})
            SET ev.url = $url, ev.date = $date, ev.actor = $actor, ev.type = $type, ev.source = $source, ev.raw = $raw
            WITH ev
            MATCH (e:Empleado {id:$eid}), (s:Skill {name:$skill})
            MERGE (e)-[he:HAS_EVIDENCE]->(ev)
            MERGE (ev)-[ab:ABOUT]->(s)
            // keep compatibility: ensure the old relation exists and update ultimaDemostracion
            MERGE (e)-[r:DEMUESTRA_COMPETENCIA]->(s)
            SET r.ultimaDemostracion = CASE WHEN $date IS NOT NULL THEN date($date) ELSE r.ultimaDemostracion END
            RETURN ev
            '''
            uid = f"{evidence_obj['source']}:{evidence_obj['id']}" if evidence_obj.get('id') else f"{evidence_obj['source']}:{author_login}:{sk}:{evidence_obj['url']}"
            s.run(cy, uid=uid, url=evidence_obj['url'], date=evidence_obj['date'], actor=evidence_obj['actor'], type=evidence_obj['type'], source=evidence_obj['source'], raw=evidence_json, eid=author_login, skill=sk)
        # after processing all skills, recompute levels for the affected employee
        try:
            recompute_skill_levels_for_employees(get_driver(), [author_login])
        except Exception as e:
            # do not fail ingestion on recompute error
            print('warning: recompute_skill_levels_for_employees failed for', author_login, e)
