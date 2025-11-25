"""
Configuration management for Project Chimera.
Loads environment variables and provides application settings.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass: str = os.getenv("NEO4J_PASS", "password")
    
    # GitHub Configuration
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    
    # Jira Configuration
    jira_base: str = os.getenv("JIRA_BASE", "")
    jira_user: str = os.getenv("JIRA_USER", "")
    jira_token: str = os.getenv("JIRA_TOKEN", "")
    
    # Privacy Configuration
    hash_actor_ids: bool = os.getenv("HASH_ACTOR_IDS", "false").lower() == "true"
    privacy_salt: str = os.getenv("PRIVACY_SALT", "change_me_in_production_please")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
