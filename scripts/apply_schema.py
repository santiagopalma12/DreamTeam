import sys
import os

# Add backend to path so we can import app.config
# Assuming scripts/ is at root level and backend/ is at root level
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

try:
    from neo4j import GraphDatabase
    # from app.config import settings
    class Settings:
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASS = "neo4jpasswd"
    settings = Settings()
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"Import Error: {e}")
    sys.exit(1)

def apply_schema():
    uri = settings.NEO4J_URI
    auth = (settings.NEO4J_USER, settings.NEO4J_PASS)
    
    print(f"Connecting to {uri}...")
    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
        print("Connected.")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        return

    schema_path = os.path.join(os.path.dirname(__file__), '../backend/neo4j/schema.cypher')
    if not os.path.exists(schema_path):
        print(f"Schema file not found at {schema_path}")
        return

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_cypher = f.read()
        
    # Split by semicolon to get individual statements, filtering empty ones
    # Note: This is a simple splitter. It might fail if semicolons are inside strings, 
    # but for our schema file it is sufficient.
    statements = [s.strip() for s in schema_cypher.split(';') if s.strip() and not s.strip().startswith('//')]
    
    with driver.session() as session:
        for stmt in statements:
            # Remove comments if any remain (simple check)
            lines = [l for l in stmt.split('\n') if not l.strip().startswith('//')]
            clean_stmt = '\n'.join(lines)
            if not clean_stmt.strip():
                continue
                
            print(f"Executing: {clean_stmt[:60].replace('\n', ' ')}...")
            try:
                session.run(clean_stmt)
            except Exception as e:
                print(f"Error executing statement: {e}")
                
    print("Schema applied successfully.")
    driver.close()

if __name__ == "__main__":
    apply_schema()
