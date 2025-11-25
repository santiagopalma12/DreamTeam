"""
Guardian Core: The Advisor Engine

This module implements the core recommendation logic for Project Chimera.
Philosophy: Constraint Satisfaction First, Optimization Second.

Key Functions:
- find_candidates: Query employees with required skills
- filter_availability: Hard filter by time availability
- filter_conflicts: Hard filter by HR constraints
- generate_dossiers: Main entry point - produces 3 strategic options
"""

from typing import List, Dict, Any, Set
from .db import get_driver
from .schemas import Dossier, Candidate, ExecutiveSummary
import uuid
import statistics


def find_candidates(skills_required: List[str]) -> List[Dict[str, Any]]:
    """
    Find all employees who have ALL required skills.
    
    Args:
        skills_required: List of skill names (e.g., ['Python', 'Docker'])
    
    Returns:
        List of employee dicts with id, nombre, and matched skills
    """
    driver = get_driver()
    query = """
    MATCH (e:Empleado)
    WHERE ALL(skill IN $skills WHERE EXISTS((e)-[:DEMUESTRA_COMPETENCIA]->(:Skill {name: skill})))
    OPTIONAL MATCH (e)-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
    WHERE s.name IN $skills
    RETURN e.id AS id, 
           e.nombre AS nombre,
           collect({skill: s.name, nivel: r.nivel}) AS skills_detail
    """
    
    with driver.session() as session:
        result = session.run(query, skills=skills_required)
        candidates = []
        for record in result:
            candidates.append({
                'id': record['id'],
                'nombre': record.get('nombre', record['id']),
                'skills_detail': record['skills_detail']
            })
        return candidates


def filter_availability(candidates: List[Dict], week: str, min_hours: int) -> List[Dict]:
    """
    HARD FILTER: Exclude candidates with insufficient availability.
    
    Args:
        candidates: List of candidate dicts with 'id' field
        week: ISO week string (e.g., '2025-W01')
        min_hours: Minimum required hours
    
    Returns:
        Filtered list with availability_hours added to each candidate
    """
    if not week or min_hours is None:
        # If no availability requirements, return all with default hours
        for c in candidates:
            c['availability_hours'] = 40  # Default assumption
        return candidates
    
    driver = get_driver()
    candidate_ids = [c['id'] for c in candidates]
    
    query = """
    UNWIND $ids AS eid
    MATCH (e:Empleado {id: eid})
    OPTIONAL MATCH (e)-[:HAS_AVAILABILITY]->(a:Availability {week: $week})
    RETURN e.id AS id, coalesce(a.hours, 0) AS hours
    """
    
    with driver.session() as session:
        result = session.run(query, ids=candidate_ids, week=week)
        availability_map = {r['id']: r['hours'] for r in result}
    
    # Filter and enrich
    filtered = []
    for candidate in candidates:
        hours = availability_map.get(candidate['id'], 0)
        if hours >= min_hours:
            candidate['availability_hours'] = hours
            filtered.append(candidate)
    
    return filtered


# ============================================================================
# PHASE 6: OVERRIDE MECHANISM
# ============================================================================

def apply_overrides(candidates: List[Dict], force_include: List[str], force_exclude: List[str]) -> List[Dict]:
    """
    Apply manager overrides (Phase 6: Policy & Governance).
    
    Managers can:
    - Force-include specific employees (even if they don't meet criteria)
    - Force-exclude specific employees (e.g., on vacation, conflicts)
    
    Args:
        candidates: List of candidate dicts
        force_include: Employee IDs that MUST be included
        force_exclude: Employee IDs that MUST be excluded
    
    Returns:
        Filtered candidates + forced includes
    """
    # Step 1: Remove excluded employees
    filtered = [c for c in candidates if c['id'] not in force_exclude]
    
    # Step 2: Add forced includes (even if they don't meet normal criteria)
    if force_include:
        driver = get_driver()
        for emp_id in force_include:
            # Skip if already in candidates
            if any(c['id'] == emp_id for c in filtered):
                continue
            
            # Fetch employee data
            query = """
            MATCH (e:Empleado {id: $eid})
            OPTIONAL MATCH (e)-[r:DEMUESTRA_COMPETENCIA]->(s:Skill)
            RETURN e.id AS id, 
                   e.nombre AS nombre,
                   collect({skill: s.name, nivel: r.nivel}) AS skills_detail
            """
            
            with driver.session() as session:
                result = session.run(query, eid=emp_id)
                record = result.single()
                if record:
                    # Add to candidates with special flag
                    filtered.append({
                        'id': record['id'],
                        'nombre': record.get('nombre', record['id']),
                        'skills_detail': record['skills_detail'],
                        'forced_include': True,  # Mark as manager override
                        'availability_hours': 40  # Assume full availability
                    })
    
    return filtered


def filter_conflicts(team_ids: List[str]) -> bool:
    """
    Check if proposed team has any pairwise conflicts.
    
    Phase 5: Now checks BOTH:
    - CONFLICT_WITH edges (existing)
    - MANUAL_CONSTRAINT edges (HR overrides)
    
    Args:
        team_ids: List of employee IDs
    
    Returns:
        True if team is VALID (no conflicts), False if conflicts exist
    """
    if len(team_ids) < 2:
        return True  # No conflicts possible
    
    driver = get_driver()
    query = """
    UNWIND $ids AS id1
    MATCH (a:Empleado {id: id1})-[r]-(b:Empleado)
    WHERE b.id IN $ids AND id1 < b.id
      AND (type(r) = 'CONFLICT_WITH' OR type(r) = 'MANUAL_CONSTRAINT')
    RETURN a.id AS person1, b.id AS person2, type(r) AS conflict_type
    LIMIT 1
    """
    
    with driver.session() as session:
        result = session.run(query, ids=team_ids)
        conflicts = list(result)
        return len(conflicts) == 0  # True if no conflicts found


def _calculate_candidate_score(candidate: Dict, skills_required: List[str]) -> float:
    """
    Calculate overall score for a candidate based on skill levels.
    
    Args:
        candidate: Candidate dict with 'skills_detail' field
        skills_required: List of required skills
    
    Returns:
        Score (0.0 to 5.0)
    """
    skills_detail = candidate.get('skills_detail', [])
    if not skills_detail:
        return 1.0  # Minimum score
    
    total_nivel = sum(s.get('nivel', 1.0) for s in skills_detail if s['skill'] in skills_required)
    avg_nivel = total_nivel / len(skills_required) if skills_required else 1.0
    return round(avg_nivel, 2)


# ============================================================================
# PHASE 5: EXECUTIVE SUMMARY GENERATION
# ============================================================================

def _generate_executive_summary(team: List[Candidate], strategy: str) -> ExecutiveSummary:
    """
    Generate Top 3 Pros/Cons for quick decision making (Phase 5).
    
    Args:
        team: List of Candidate objects
        strategy: Strategy name ('safe_bet', 'growth', 'speed')
    
    Returns:
        ExecutiveSummary with pros, cons, and recommendation
    """
    pros = []
    cons = []
    
    if not team:
        return ExecutiveSummary(
            pros=["⚠️ No team members available"],
            cons=["🚨 Cannot form team"],
            recommendation="REJECT"
        )
    
    # Analyze team composition
    avg_score = statistics.mean([c.score for c in team])
    min_avail = min([c.availability_hours for c in team])
    max_avail = max([c.availability_hours for c in team])
    linchpins = [c for c in team if c.linchpin_risk in ['CRITICAL', 'HIGH']]
    
    # Build Pros
    if avg_score >= 4.0:
        pros.append(f"✅ High average skill level ({avg_score:.1f}/5.0)")
    elif avg_score >= 3.5:
        pros.append(f"✅ Solid skill levels ({avg_score:.1f}/5.0)")
    
    if min_avail >= 30:
        pros.append("✅ All members have good availability (30+ hrs/week)")
    elif min_avail >= 20:
        pros.append("✅ Adequate availability across team")
    
    if not linchpins:
        pros.append("✅ No critical dependencies (low Bus Factor risk)")
    
    if strategy == 'growth':
        pros.append("✅ Mentorship opportunities built-in")
    elif strategy == 'speed':
        pros.append("✅ Pre-existing collaboration history")
    
    # Build Cons
    if avg_score < 3.0:
        cons.append(f"⚠️ Below-average skill levels ({avg_score:.1f}/5.0)")
    
    if min_avail < 20:
        cons.append(f"⚠️ Some members have limited availability ({min_avail} hrs/week)")
    
    if linchpins:
        if len(linchpins) == 1:
            cons.append(f"🚨 Team includes 1 linchpin employee ({linchpins[0].linchpin_risk} risk)")
        else:
            cons.append(f"🚨 Team includes {len(linchpins)} linchpin employees")
    
    if max_avail - min_avail > 20:
        cons.append("⚠️ Large availability variance across team")
    
    # Recommendation logic
    critical_issues = len([c for c in cons if c.startswith("🚨")])
    warning_issues = len([c for c in cons if c.startswith("⚠️")])
    
    if critical_issues >= 2 or avg_score < 2.5:
        recommendation = "REJECT"
    elif critical_issues == 1 or warning_issues >= 2:
        recommendation = "REVIEW"
    else:
        recommendation = "APPROVE"
    
    return ExecutiveSummary(
        pros=pros[:3] if pros else ["No significant advantages identified"],
        cons=cons[:3] if cons else [],
        recommendation=recommendation
    )


def _safe_bet_strategy(candidates: List[Dict], skills_required: List[str], k: int) -> Dossier:
    """
    Strategy 1: The Safe Bet
    High skill match + high availability = reliable delivery.
    """
    # Sort by score descending, then by availability
    scored = []
    for c in candidates:
        score = _calculate_candidate_score(c, skills_required)
        scored.append({**c, 'score': score})
    
    scored.sort(key=lambda x: (x['score'], x.get('availability_hours', 0)), reverse=True)
    
    # Take top k
    team = scored[:k]
    
    # Build Candidate objects with linchpin detection (Phase 5)
    from .linchpin_detector import get_linchpin_risk_for_employee
    driver = get_driver()
    
    team_candidates = []
    for member in team:
        linchpin_risk = get_linchpin_risk_for_employee(driver, member['id'])
        team_candidates.append(Candidate(
            id=member['id'],
            skills_matched=skills_required,
            score=member['score'],
            availability_hours=member.get('availability_hours', 40),
            conflict_risk=False,
            linchpin_risk=linchpin_risk
        ))
    
    total_score = sum(m['score'] for m in team)
    
    # Phase 5: Generate executive summary
    executive_summary = _generate_executive_summary(team_candidates, 'safe_bet')
    
    return Dossier(
        title="The Safe Bet",
        description="High-skill, high-availability team optimized for reliable delivery.",
        executive_summary=executive_summary,
        team=team_candidates,
        total_score=round(total_score, 2),
        risk_analysis=[
            "✅ All members have strong skill levels",
            "✅ High availability ensures focus",
            "⚠️ May lack diversity in experience levels"
        ],
        rationale="This team prioritizes proven expertise and time commitment."
    )


def _growth_team_strategy(candidates: List[Dict], skills_required: List[str], k: int) -> Dossier:
    """
    Strategy 2: The Growth Team
    Mix of seniors (nivel > 4) and juniors (nivel < 3) for mentorship.
    """
    scored = []
    for c in candidates:
        score = _calculate_candidate_score(c, skills_required)
        scored.append({**c, 'score': score})
    
    # Separate seniors and juniors
    seniors = [c for c in scored if c['score'] >= 4.0]
    juniors = [c for c in scored if c['score'] < 3.0]
    mid_level = [c for c in scored if 3.0 <= c['score'] < 4.0]
    
    # Build balanced team: 40% seniors, 40% mid, 20% juniors
    team = []
    senior_count = max(1, int(k * 0.4))
    junior_count = max(1, int(k * 0.2))
    mid_count = k - senior_count - junior_count
    
    team.extend(seniors[:senior_count])
    team.extend(mid_level[:mid_count])
    team.extend(juniors[:junior_count])
    
    # Fill remaining slots if needed
    while len(team) < k and scored:
        remaining = [c for c in scored if c not in team]
        if remaining:
            team.append(remaining[0])
        else:
            break
    
    team_candidates = []
    from .linchpin_detector import get_linchpin_risk_for_employee
    driver_inst = get_driver()
    
    for member in team:
        linchpin_risk = get_linchpin_risk_for_employee(driver_inst, member['id'])
        team_candidates.append(Candidate(
            id=member['id'],
            skills_matched=skills_required,
            score=member['score'],
            availability_hours=member.get('availability_hours', 40),
            conflict_risk=False,
            linchpin_risk=linchpin_risk
        ))
    
    total_score = sum(m['score'] for m in team)
    executive_summary = _generate_executive_summary(team_candidates, 'growth')
    
    return Dossier(
        title="The Growth Team",
        description="Balanced mix of senior and junior talent for knowledge transfer.",
        executive_summary=executive_summary,
        team=team_candidates,
        total_score=round(total_score, 2),
        risk_analysis=[
            "✅ Mentorship opportunities for juniors",
            "✅ Knowledge sharing built-in",
            "⚠️ May require more coordination time"
        ],
        rationale="This team optimizes for long-term capability building."
    )


def _speed_squad_strategy(candidates: List[Dict], skills_required: List[str], k: int) -> Dossier:
    """
    Strategy 3: The Speed Squad
    People who have collaborated before (high synergy).
    """
    driver = get_driver()
    candidate_ids = [c['id'] for c in candidates]
    
    # Query collaboration graph
    query = """
    UNWIND $ids AS id1
    MATCH (a:Empleado {id: id1})-[r:HA_COLABORADO_CON]-(b:Empleado)
    WHERE b.id IN $ids AND id1 < b.id
    RETURN a.id AS person1, b.id AS person2, 
           coalesce(r.proyectosComunes, 0) AS projects,
           coalesce(r.frecuencia, 0) AS frequency
    ORDER BY projects DESC, frequency DESC
    """
    
    with driver.session() as session:
        result = session.run(query, ids=candidate_ids)
        collaborations = list(result)
    
    # Build collaboration score map
    collab_scores = {}
    for c in candidates:
        collab_scores[c['id']] = 0
    
    for collab in collaborations:
        p1, p2 = collab['person1'], collab['person2']
        weight = collab['projects'] + (collab['frequency'] * 0.5)
        collab_scores[p1] = collab_scores.get(p1, 0) + weight
        collab_scores[p2] = collab_scores.get(p2, 0) + weight
    
    # Sort by collaboration score
    scored = []
    for c in candidates:
        score = _calculate_candidate_score(c, skills_required)
        collab_score = collab_scores.get(c['id'], 0)
        scored.append({**c, 'score': score, 'collab_score': collab_score})
    
    scored.sort(key=lambda x: x['collab_score'], reverse=True)
    team = scored[:k]
    
    team_candidates = []
    from .linchpin_detector import get_linchpin_risk_for_employee
    driver_inst = get_driver()
    
    for member in team:
        linchpin_risk = get_linchpin_risk_for_employee(driver_inst, member['id'])
        team_candidates.append(Candidate(
            id=member['id'],
            skills_matched=skills_required,
            score=member['score'],
            availability_hours=member.get('availability_hours', 40),
            conflict_risk=False,
            linchpin_risk=linchpin_risk
        ))
    
    total_score = sum(m['score'] for m in team)
    executive_summary = _generate_executive_summary(team_candidates, 'speed')
    
    return Dossier(
        title="The Speed Squad",
        description="Team members with proven collaboration history for rapid execution.",
        executive_summary=executive_summary,
        team=team_candidates,
        total_score=round(total_score, 2),
        risk_analysis=[
            "✅ Pre-existing working relationships",
            "✅ Reduced onboarding friction",
            "⚠️ May reinforce existing silos"
        ],
        rationale="This team leverages past synergy for fast delivery."
    )


def generate_dossiers(request: Dict[str, Any]) -> List[Dossier]:
    """
    Main entry point: Generate 3 strategic team options.
    
    Args:
        request: TeamRequest dict with:
            - requisitos_hard: {'skills': [...], ...}
            - k: team size
            - week: optional ISO week for availability
            - min_hours: optional minimum hours required
            - mission_profile: optional mission context (Phase 6)
            - force_include: optional list of IDs to force-include (Phase 6)
            - force_exclude: optional list of IDs to force-exclude (Phase 6)
    
    Returns:
        List of 3 Dossier objects
    """
    hard_reqs = request.get('requisitos_hard', {})
    skills_required = hard_reqs.get('skills', [])
    k = request.get('k', 5)
    week = request.get('week')
    min_hours = request.get('min_hours', 20)  # Default: 20 hours/week
    
    # Phase 6: Get mission profile and overrides
    mission_profile = request.get('mission_profile', 'mantenimiento')
    force_include = request.get('force_include', [])
    force_exclude = request.get('force_exclude', [])
    
    # Step 1: Find candidates with required skills
    candidates = find_candidates(skills_required)
    
    if not candidates:
        # No candidates found - return empty dossiers
        return []
    
    # Step 2: Filter by availability (HARD CONSTRAINT)
    candidates = filter_availability(candidates, week, min_hours)
    
    if not candidates:
        # No one available
        return []
    
    # Phase 6: Step 3: Apply manager overrides
    if force_include or force_exclude:
        candidates = apply_overrides(candidates, force_include, force_exclude)
    
    # Phase 6: Step 4: Get mission profile configuration
    from .mission_profiles import get_mission_profile
    profile_config = get_mission_profile(mission_profile)
    
    # Step 5: Generate 3 strategies
    dossiers = []
    
    # Strategy 1: Safe Bet
    safe_bet = _safe_bet_strategy(candidates, skills_required, k)
    # Verify no conflicts
    if filter_conflicts([m.id for m in safe_bet.team]):
        dossiers.append(safe_bet)
    
    # Strategy 2: Growth Team
    growth = _growth_team_strategy(candidates, skills_required, k)
    if filter_conflicts([m.id for m in growth.team]):
        dossiers.append(growth)
    
    # Strategy 3: Speed Squad
    speed = _speed_squad_strategy(candidates, skills_required, k)
    if filter_conflicts([m.id for m in speed.team]):
        dossiers.append(speed)
    
    return dossiers
