#!/usr/bin/env python3
"""
Script de migración:
- Lee relaciones (Empleado)-[r:DEMUESTRA_COMPETENCIA]->(Skill) y su propiedad r.evidencias
- Para cada item en r.evidencias (string URL o JSON-string), crea un nodo :Evidence{uid, url, date, actor, type, source, raw}
- Crea relaciones (Empleado)-[:HAS_EVIDENCE]->(Evidence)-[:ABOUT]->(Skill)
- Marca la relación original r._migrated = true para evitar re-migrar
- Imprime un resumen al final

USO:
  Ejecutar desde el root del repo con las variables de entorno del compose disponibles (o usando las mismas credenciales):
    python scripts/migrate_evidences_to_nodes.py

Nota: Hice el script de forma segura: si evidence ya existe (por uid) no la duplicará.

"""
import json
import os
import sys
from uuid import uuid4
from datetime import datetime

# Import the project's Neo4j driver helper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app.db import get_driver
except Exception as e:
    print('No pude importar get_driver desde backend.app.db:', e)
    print('Asegúrate de ejecutar este script desde la raíz del repo y que backend esté instalado / en PYTHONPATH')
    raise


def parse_evidence_item(item):
    """Devuelve un dict con keys: url, date, actor, type, source, id, raw
    item puede ser:
      - string simple (URL)
      - JSON string serializado
      - dict (si alguna vez lo hubo)
    """
    if not item:
        return None
    if isinstance(item, dict):
        base = dict(item)
        base.setdefault('raw', json.dumps(item, ensure_ascii=False))
        return base
    if isinstance(item, str):
        s = item.strip()
        # try parse json
        if s.startswith('{') and s.endswith('}'):
            try:
                obj = json.loads(s)
                obj.setdefault('raw', s)
                return obj
            except Exception:
                # fallthrough: treat as URL
                pass
        # treat as URL
        return {
            'url': s,
            'date': None,
            'actor': None,
            'type': 'unknown',
            'source': None,
            'id': None,
            'raw': s,
        }
    # unknown type
    return { 'url': str(item), 'raw': str(item) }


def uid_for_evidence(ev):
    # prefer source+id when available
    if not ev:
        return None
    sid = ev.get('source') or 'unknown'
    iid = ev.get('id') or ev.get('url') or str(uuid4())
    return f"{sid}:{iid}"


def main():
    driver = get_driver()
    migrated = 0
    created_evidence = 0
    touched_relations = 0

    # read all relations with evidences not yet migrated
    read_q = """
    MATCH (e:Empleado)-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
    WHERE r.evidencias IS NOT NULL AND coalesce(r._migrated, false) = false
    RETURN e.id AS eid, s.name AS skill, r.evidencias AS evidencias
    """

    with driver.session() as s:
        res = s.run(read_q)
        rows = list(res)

    print(f'Encontradas {len(rows)} relaciones con evidencias no migradas')

    for row in rows:
        eid = row['eid']
        skill = row['skill']
        evids = row.get('evidencias') or []
        if not evids:
            continue
        touched_relations += 1
        for item in evids:
            ev = parse_evidence_item(item)
            if not ev:
                continue
            uid = uid_for_evidence(ev)
            ev_date = ev.get('date')
            # normalize date to yyyy-mm-dd if possible
            if ev_date:
                ev_date = str(ev_date)[:10]
            url = ev.get('url')
            actor = ev.get('actor')
            etype = ev.get('type') or 'unknown'
            source = ev.get('source') or 'legacy'
            raw = ev.get('raw') or json.dumps(ev, ensure_ascii=False)

            # create Evidence node if not exists and relationships
            cy = '''
            MERGE (ev:Evidence {uid:$uid})
            SET ev.url = $url, ev.date = $date, ev.actor = $actor, ev.type = $type, ev.source = $source, ev.raw = $raw
            WITH ev
            MATCH (e:Empleado {id:$eid}), (s:Skill {name:$skill})
            MERGE (e)-[he:HAS_EVIDENCE]->(ev)
            MERGE (ev)-[ab:ABOUT]->(s)
            RETURN ev, he, ab
            '''
            with driver.session() as s:
                s.run(cy, uid=uid, url=url, date=ev_date, actor=actor, type=etype, source=source, raw=raw, eid=eid, skill=skill)
                created_evidence += 1
        # mark the original relation as migrated
        mark_q = '''
        MATCH (e:Empleado {id:$eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill {name:$skill})
        SET r._migrated = true
        RETURN r
        '''
        with driver.session() as s:
            s.run(mark_q, eid=eid, skill=skill)
        migrated += 1

    print('--- Informe de migración ---')
    print('Relaciones procesadas:', touched_relations)
    print('Nuevos nodos Evidence creados (intentos):', created_evidence)
    print('Relaciones DEMUESTRA_COMPETENCIA marcadas como migradas:', migrated)
    print('Nota: el script MERGEa por uid así que no duplicará evidencias idénticas en múltiples ejecuciones')


if __name__ == '__main__':
    main()
