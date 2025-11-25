"""
Neo4j database connection management.
Provides singleton driver instance for database operations.
"""
from neo4j import GraphDatabase
from .config import settings


_driver = None


def get_driver():
    """Get or create Neo4j driver instance (singleton pattern)."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_pass)
        )
    return _driver


def close_driver():
    """Close Neo4j driver connection."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
