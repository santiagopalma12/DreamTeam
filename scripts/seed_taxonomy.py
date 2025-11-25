import sys
import os
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

try:
    from neo4j import GraphDatabase
    # from app.config import settings
    class Settings:
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASS = "neo4jpasswd"
    settings = Settings()
except ImportError:
    print("Import Error: Dependencies not found.")
    sys.exit(1)

def seed_taxonomy():
    uri = settings.NEO4J_URI
    auth = (settings.NEO4J_USER, settings.NEO4J_PASS)
    
    print(f"Connecting to {uri}...")
    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    csv_path = os.path.join(os.path.dirname(__file__), '../backend/neo4j/taxonomy.csv')
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    query = """
    UNWIND $rows AS row
    MERGE (s:Skill {name: row.skill})
    SET s.family = row.family
    WITH s, row
    WHERE row.alias IS NOT NULL AND row.alias <> ''
    MERGE (a:Alias {name: row.alias})
    MERGE (s)-[:HAS_ALIAS]->(a)
    """
    
    with driver.session() as session:
        print(f"Seeding {len(rows)} skills...")
        try:
            session.run(query, rows=rows)
            print("Taxonomy seeded successfully.")
        except Exception as e:
            print(f"Error seeding taxonomy: {e}")
        
    driver.close()

if __name__ == "__main__":
    seed_taxonomy()
