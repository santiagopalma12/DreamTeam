from typing import List, Dict, Any
from .db import driver
from datetime import date
import networkx as nx
import math

# Helpers: obtener candidatos que cumplen hard reqs
def filter_candidates(hard: dict) -> List[Dict]:
    # hard example: {'skills':['Facturación','Java'], 'acceso':['sistemaX'], 'zona':['PE/Lima']}
    # Devuelve lista de empleados (id, nombre, metadata)
    query = """
    MATCH (e:Empleado)
    WHERE ALL(s IN $skills WHERE EXISTS((e)-[:DEMUESTRA_COMPETENCIA]->(:Skill {name:s})))
      AND ($acceso IS NULL OR ANY(a IN $acceso WHERE a IN coalesce(e.acceso,[])))
      AND ($zonas IS NULL OR e.zona IN $zonas)
    RETURN e.id as id, e.nombre as nombre, e
    """
    with driver.session() as session:
        result = session.run(query, skills=hard.get('skills',[]), acceso=hard.get('acceso',None), zonas=hard.get('zona',None))
        return [r.data()['e'] if 'e' in r.data() else {'id':r['id'],'nombre':r['nombre']} for r in result]

# Construye grafo local de colaboración entre candidatos y extrae métricas
def build_local_graph(candidate_ids: List[str]) -> nx.Graph:
    G = nx.Graph()
    G.add_nodes_from(candidate_ids)
    # recuperar relaciones factuales entre candidatos
    query = """
    UNWIND $ids AS id1
    MATCH (a:Empleado {id:id1})-[r:HA_COLABORADO_CON]-(b:Empleado)
    WHERE b.id IN $ids
    RETURN a.id as a, b.id as b, r.proyectosComunes as proyectos, r.interaccionesPositivas as pos,
           r.interaccionesConflictivas as conf, r.frecuencia as freq, r.recencia as rec
    """
    with driver.session() as s:
        res = s.run(query, ids=candidate_ids)
        for r in res:
            a = r['a']; b = r['b']
            weight = compute_edge_strength(r)
            G.add_edge(a,b, weight=weight,
                       proyectos=r.get('proyectos',[]),
                       pos=r.get('pos',0),
                       conf=r.get('conf',0),
                       freq=r.get('freq',0),
                       rec=r.get('rec', None))
    return G

def compute_edge_strength(rec):
    # heurística: (pos - conf*2) * log(1+freq) * freshness_factor
    pos = rec.get('pos',0) or 0
    conf = rec.get('conf',0) or 0
    freq = rec.get('freq',0) or 0.0
    freshness = 1.0
    # si recencia es vieja, bajar
    try:
        rec_date = rec.get('rec')
        if rec_date:
            # asume ISO date
            d = date.fromisoformat(rec_date)
            days = (date.today() - d).days
            freshness = 1.0 if days < 90 else max(0.2, 1 - days/365.0)
    except:
        freshness = 1.0
    score = max(0.0, (pos - 2*conf)) * math.log(1+freq+1) * freshness
    return score

# Obtiene competencia (nivel) por skill de un empleado
def get_employee_skill_levels(emp_id, skills):
    # Prefer Evidence nodes model; fall back to legacy r.evidencias
    q = """
    MATCH (e:Empleado {id:$eid})-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
    WHERE s.name IN $skills
    OPTIONAL MATCH (e)-[:HAS_EVIDENCE]->(ev:Evidence)-[:ABOUT]->(s)
    WITH s, r, collect(CASE WHEN ev IS NULL THEN NULL ELSE {url:ev.url, date:ev.date, actor:ev.actor, source:ev.source, id:ev.uid, raw:ev.raw} END) AS evs
    RETURN s.name as skill, r.nivel as nivel, evs AS evidencias_nodes, r.evidencias AS evidencias_legacy, r.ultimaDemostracion as ultima
    """
    with driver.session() as s:
        res = s.run(q, eid=emp_id, skills=skills)
        out = {}
        for r in res:
            skill = r['skill']
            nivel = r['nivel'] or 0.0
            ev_nodes = r.get('evidencias_nodes') or []
            ev_legacy = r.get('evidencias_legacy') or []
            evids = []
            # use nodes when present
            if ev_nodes and any(e for e in ev_nodes if e is not None):
                for ev in ev_nodes:
                    if not ev:
                        continue
                    evids.append({'url': ev.get('url'), 'date': ev.get('date'), 'actor': ev.get('actor'), 'source': ev.get('source'), 'id': ev.get('id'), 'raw': ev.get('raw')})
            else:
                # parse legacy entries: could be plain URL or JSON string
                for it in ev_legacy:
                    if not it:
                        continue
                    if isinstance(it, str):
                        s_it = it.strip()
                        if s_it.startswith('{') and s_it.endswith('}'):
                            try:
                                obj = __import__('json').loads(s_it)
                                evids.append({'url': obj.get('url'), 'date': obj.get('date'), 'actor': obj.get('actor'), 'source': obj.get('source'), 'id': obj.get('id'), 'raw': s_it})
                                continue
                            except Exception:
                                pass
                        # plain url
                        evids.append({'url': s_it, 'date': None, 'actor': None, 'source': None, 'id': None, 'raw': s_it})
                    else:
                        # unknown type
                        evids.append({'url': str(it), 'date': None, 'actor': None, 'source': None, 'id': None, 'raw': str(it)})
            out[skill] = {'nivel': nivel, 'evidencias': evids, 'ultima': r.get('ultima')}
        return out

# Scoring parcial explicable
def compute_team_metrics(team_ids: List[str], required_skills: List[str], G: nx.Graph):
    # Cobertura de skills:
    covered = set()
    profs = []
    for eid in team_ids:
        levels = get_employee_skill_levels(eid, required_skills)
        for s,info in levels.items():
            if info['nivel'] and info['nivel'] >= 1:
                covered.add(s)
                profs.append(info['nivel'])
    S_skill = len(covered)/max(1,len(required_skills))
    S_exp = (sum(profs)/len(profs)/5.0) if profs else 0.0
    # Cohesión: densidad weighted
    sub = G.subgraph(team_ids)
    if sub.number_of_nodes() <= 1:
        cohesion = 0.0
    else:
        total_possible = sub.number_of_nodes() * (sub.number_of_nodes()-1) / 2
        actual_sum = sum([d['weight'] for _,_,d in sub.edges(data=True)])
        # Normalize: divide por total_possible * max_edge_empiric (tuneable)
        cohesion = actual_sum / (total_possible * 10.0)  # 10.0 ~ expected max weight
        cohesion = min(1.0, cohesion)
    # SPoF: contar skills that have single employee coverage
    skill_count = {}
    for s in required_skills:
        skill_count[s] = 0
        for eid in team_ids:
            levels = get_employee_skill_levels(eid, [s])
            if levels.get(s) and levels[s]['nivel'] >= 3:  # threshold
                skill_count[s] += 1
    spof = sum(1 for v in skill_count.values() if v==1)
    spof_risk = spof / max(1,len(required_skills))
    return {
        'S_skill': S_skill,
        'S_exp': S_exp,
        'Cohesion': cohesion,
        'SPoF_risk': spof_risk
    }

# Núcleo: buscar linchpins (puentes con skills críticos y alta conectividad)
def find_linchpins(candidate_ids: List[str], required_skills: List[str], G: nx.Graph, top_k=2):
    scores = {}
    for eid in candidate_ids:
        # skill coverage on required
        levels = get_employee_skill_levels(eid, required_skills)
        coverage = sum(1 for s in levels if levels[s]['nivel'] >= 3)
        degree = G.degree(eid, weight='weight') if eid in G else 0
        # combinar: priorizar coverage then connectivity
        scores[eid] = coverage * 10 + degree
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in ordered[:top_k]]

# Algoritmo Guardián (versión compilable)
def propose_teams(request: dict) -> List[dict]:
    hard = request.get('requisitos_hard', {})
    profile = request.get('perfil_mision','mantenimiento')
    k = request.get('k', 5)
    preferences = request.get('preferences', {})

    # 1) Candidatos
    candidates_raw = filter_candidates(hard)
    candidate_ids = [c['id'] for c in candidates_raw]

    # 2) Build local graph
    G = build_local_graph(candidate_ids)

    # 3) Linchpins (nucleus)
    nucleus = find_linchpins(candidate_ids, hard.get('skills',[]), G, top_k=2)

    proposals = []
    # generamos 3 propuestas: balance, cohesion_max, redundancy_max
    modes = ['balance','cohesion','redundancy']
    for mode in modes:
        team = list(nucleus)
        # iterative augmentation
        remaining = [c for c in candidate_ids if c not in team]
        while len(team) < k and remaining:
            best_candidate = None
            best_utility = -1e9
            best_metrics = None
            for cand in remaining:
                candidate_team = team + [cand]
                metrics = compute_team_metrics(candidate_team, hard.get('skills',[]), G)
                # utility: depende del mode
                if mode == 'balance':
                    # combine skill coverage, cohesion, and penalize spof
                    utility = metrics['S_skill']*0.5 + metrics['Cohesion']*0.35 - metrics['SPoF_risk']*0.15 + metrics['S_exp']*0.2
                elif mode == 'cohesion':
                    utility = metrics['Cohesion']*0.7 + metrics['S_skill']*0.2 + (1-metrics['SPoF_risk'])*0.1
                elif mode == 'redundancy':
                    utility = metrics['S_skill']*0.5 + (1-metrics['SPoF_risk'])*0.4 + metrics['S_exp']*0.1
                if utility > best_utility:
                    best_utility = utility
                    best_candidate = cand
                    best_metrics = metrics
            if best_candidate is None:
                break
            team.append(best_candidate)
            remaining.remove(best_candidate)

        # local search: intentar swaps que mejoren utilidad
        improved = True
        iter_count = 0
        while improved and iter_count < 10:
            improved = False
            current_metrics = compute_team_metrics(team, hard.get('skills',[]), G)
            current_utility = (current_metrics['S_skill']*0.5 + current_metrics['Cohesion']*0.35 - current_metrics['SPoF_risk']*0.15 + current_metrics['S_exp']*0.2)
            for out_idx, out_emp in enumerate(team):
                for cand in remaining:
                    new_team = team.copy()
                    new_team[out_idx] = cand
                    new_metrics = compute_team_metrics(new_team, hard.get('skills',[]), G)
                    new_utility = (new_metrics['S_skill']*0.5 + new_metrics['Cohesion']*0.35 - new_metrics['SPoF_risk']*0.15 + new_metrics['S_exp']*0.2)
                    if new_utility > current_utility + 1e-6:
                        team = new_team
                        remaining.remove(cand)
                        remaining.append(out_emp)
                        improved = True
                        break
                if improved:
                    break
            iter_count += 1

        # Build dossier (explainable)
        dossier = {
            'mode': mode,
            # replace member ids with basic objects (id, nombre, rol) for UI friendliness
            'members': [],
            'metrics': compute_team_metrics(team, hard.get('skills',[]), G),
            'justificaciones': []
        }
        # fetch basic info for each member id
        with driver.session() as s:
            for m in team:
                q = """
                MATCH (e:Empleado {id:$eid})
                RETURN e.id as id, e.nombre as nombre, e.rol as rol
                """
                res = s.run(q, eid=m)
                rec = res.single()
                if rec:
                    dossier['members'].append({'id': rec['id'], 'nombre': rec.get('nombre') or rec.get('id'), 'rol': rec.get('rol')})
                else:
                    dossier['members'].append({'id': m, 'nombre': m, 'rol': None})
        # justificaciones: for each member, fetch top evidences for required skills
        for m in team:
            # obtener skills y evidencias
            skill_info = get_employee_skill_levels(m, hard.get('skills',[]))
            # build structured justifications per skill with top evidences
            skill_justs = []
            for s,info in skill_info.items():
                if info.get('nivel',0) >= 1:
                    evids = info.get('evidencias', []) or []
                    # sort evidences by date desc when date present
                    try:
                        evids_sorted = sorted(evids, key=lambda x: x.get('date') or '', reverse=True)
                    except Exception:
                        evids_sorted = evids
                    top_evid = evids_sorted[:3]
                    skill_justs.append({'skill': s, 'nivel': info.get('nivel',0.0), 'evidencias': top_evid})
            dossier['justificaciones'].append({'id': m, 'skills': skill_justs})
        proposals.append(dossier)

    return proposals
