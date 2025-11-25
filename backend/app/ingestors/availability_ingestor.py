import csv
import os
from ..db import get_driver
# from neo4j import GraphDatabase

# def get_driver():
#     return GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4jpasswd"))

def ingest_availability(csv_path):
    if not os.path.exists(csv_path):
        print(f"Availability CSV not found at {csv_path}")
        return

    driver = get_driver()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Ingesting {len(rows)} availability slots...")
    
    # Phase 3: Normalize employee IDs with privacy support
    from ..uid_normalizer import normalize_uid
    for row in rows:
        row['employee_id'] = normalize_uid('csv', row['employee_id'])
    
    query = """
    UNWIND $rows AS row
    MERGE (e:Empleado {id: row.employee_id})
    MERGE (a:Availability {week: row.week, employee_id: row.employee_id})
    SET a.hours = toInteger(row.hours)
    MERGE (e)-[:HAS_AVAILABILITY]->(a)
    """
    
    with driver.session() as s:
        try:
            s.run(query, rows=rows)
            print("Availability ingested successfully.")
        except Exception as e:
            print(f"Error ingesting availability: {e}")
