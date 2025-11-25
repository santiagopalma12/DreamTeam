"""
Linchpin Detector - Identify Critical Employees

A "linchpin" is an employee who is critical to the organization due to:
1. High betweenness centrality (connects different parts of the graph)
2. Unique skill coverage (only person with certain skills)

This module helps identify Bus Factor risks.
"""

from typing import List, Dict, Any
from .db import get_driver
import networkx as nx


def calculate_betweenness_centrality(driver) -> Dict[str, float]:
    """
    Calculate betweenness centrality for all employees.
    
    Betweenness centrality measures how often an employee appears
    on the shortest path between other employees in the collaboration graph.
    
    Returns:
        Dict mapping employee_id -> centrality_score (0.0 to 1.0)
    """
    # Build collaboration graph
    query = """
    MATCH (a:Empleado)-[r:HA_COLABORADO_CON]-(b:Empleado)
    WHERE a.id < b.id
    RETURN a.id AS person1, b.id AS person2, 
           coalesce(r.proyectosComunes, 0) AS weight
    """
    
    G = nx.Graph()
    
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            p1 = record['person1']
            p2 = record['person2']
            weight = record['weight']
            G.add_edge(p1, p2, weight=weight)
    
    # Calculate betweenness centrality
    if len(G.nodes()) == 0:
        return {}
    
    centrality = nx.betweenness_centrality(G, weight='weight')
    return centrality


def find_unique_skills(driver) -> Dict[str, List[str]]:
    """
    Find skills that only 1 person has.
    
    Returns:
        Dict mapping employee_id -> list of unique skills
    """
    query = """
    MATCH (e:Empleado)-[:DEMUESTRA_COMPETENCIA]->(s:Skill)
    WITH s.name AS skill, collect(e.id) AS employees
    WHERE size(employees) = 1
    RETURN employees[0] AS employee_id, collect(skill) AS unique_skills
    """
    
    unique_skills_map = {}
    
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            emp_id = record['employee_id']
            skills = record['unique_skills']
            unique_skills_map[emp_id] = skills
    
    return unique_skills_map


def calculate_risk_level(centrality: float, unique_skills: List[str]) -> str:
    """
    Determine risk level based on centrality and unique skills.
    
    Args:
        centrality: Betweenness centrality score (0.0 to 1.0)
        unique_skills: List of unique skills
    
    Returns:
        Risk level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    """
    has_unique_skills = len(unique_skills) > 0
    
    if centrality > 0.7 and has_unique_skills:
        return 'CRITICAL'
    elif centrality > 0.5 or (has_unique_skills and len(unique_skills) >= 2):
        return 'HIGH'
    elif centrality > 0.3 or has_unique_skills:
        return 'MEDIUM'
    else:
        return 'LOW'


def detect_linchpins(driver) -> List[Dict[str, Any]]:
    """
    Identify critical employees (linchpins).
    
    Returns:
        List of dicts with:
        - id: employee ID
        - centrality_score: betweenness centrality (0.0 to 1.0)
        - unique_skills: list of skills only they have
        - risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
        - recommendation: what to do about this risk
    """
    # Calculate centrality
    centrality_map = calculate_betweenness_centrality(driver)
    
    # Find unique skills
    unique_skills_map = find_unique_skills(driver)
    
    # Get all employees
    all_employees = set(centrality_map.keys()) | set(unique_skills_map.keys())
    
    linchpins = []
    
    for emp_id in all_employees:
        centrality = centrality_map.get(emp_id, 0.0)
        unique_skills = unique_skills_map.get(emp_id, [])
        risk_level = calculate_risk_level(centrality, unique_skills)
        
        # Only include if there's some risk
        if risk_level in ['CRITICAL', 'HIGH', 'MEDIUM']:
            recommendation = _get_recommendation(risk_level, unique_skills)
            
            linchpins.append({
                'id': emp_id,
                'centrality_score': round(centrality, 3),
                'unique_skills': unique_skills,
                'risk_level': risk_level,
                'recommendation': recommendation
            })
    
    # Sort by risk level (CRITICAL first)
    risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    linchpins.sort(key=lambda x: (risk_order[x['risk_level']], -x['centrality_score']))
    
    return linchpins


def _get_recommendation(risk_level: str, unique_skills: List[str]) -> str:
    """Generate recommendation based on risk level."""
    if risk_level == 'CRITICAL':
        skills_str = ', '.join(unique_skills[:2])
        return f"🚨 URGENT: Cross-train others on {skills_str}. High Bus Factor risk."
    elif risk_level == 'HIGH':
        return "⚠️ Consider knowledge transfer sessions or pair programming."
    elif risk_level == 'MEDIUM':
        return "📝 Document their expertise and processes."
    else:
        return "✅ Low risk."


def get_linchpin_risk_for_employee(driver, employee_id: str) -> str:
    """
    Get linchpin risk level for a specific employee.
    
    Args:
        driver: Neo4j driver
        employee_id: Employee ID
    
    Returns:
        Risk level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    """
    centrality_map = calculate_betweenness_centrality(driver)
    unique_skills_map = find_unique_skills(driver)
    
    centrality = centrality_map.get(employee_id, 0.0)
    unique_skills = unique_skills_map.get(employee_id, [])
    
    return calculate_risk_level(centrality, unique_skills)
