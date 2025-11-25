"""
Privacy Utilities - GDPR Compliance

Implements privacy-first ingestion where Actor IDs are hashed BEFORE
hitting the graph, making the database safe even if leaked.

Key Features:
- hash_pii(): Deterministic SHA-256 hashing with salt
- normalize_actor_id(): Privacy mode wrapper
- should_hash_actors(): Config check

Usage:
    from app.privacy import normalize_actor_id
    
    # In ingestor
    raw_id = "juan.perez@company.com"
    safe_id = normalize_actor_id(raw_id)
    # If HASH_ACTOR_IDS=true → "emp_a1b2c3d4e5f6g7h8"
    # If HASH_ACTOR_IDS=false → "juan.perez@company.com"
"""

import hashlib
from typing import Optional


def hash_pii(value: str, salt: str) -> str:
    """
    Hash Personally Identifiable Information using SHA-256.
    
    This is the core privacy function. It creates a deterministic hash
    that cannot be reversed without the salt.
    
    Args:
        value: The PII to hash (e.g., 'juan.perez@company.com')
        salt: Secret salt from config (PRIVACY_SALT)
    
    Returns:
        Hashed value with 'emp_' prefix (e.g., 'emp_a1b2c3d4e5f6g7h8')
    
    Examples:
        >>> hash_pii('juan.perez@company.com', 'secret123')
        'emp_a1b2c3d4e5f6g7h8'
        
        >>> hash_pii('juan.perez@company.com', 'secret123')
        'emp_a1b2c3d4e5f6g7h8'  # Same input = same hash (deterministic)
        
        >>> hash_pii('juan.perez@company.com', 'different_salt')
        'emp_x9y8z7w6v5u4t3s2'  # Different salt = different hash
    """
    if not value:
        raise ValueError("Cannot hash empty value")
    
    if not salt or salt == "change_me_in_prod_please":
        raise ValueError("Invalid or default salt. Set PRIVACY_SALT in production.")
    
    # Combine value + salt
    payload = f"{value}{salt}"
    
    # SHA-256 hash
    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    
    # Return first 16 chars with prefix for clarity
    return f"emp_{digest[:16]}"


def should_hash_actors() -> bool:
    """
    Check if privacy mode is enabled.
    
    Reads HASH_ACTOR_IDS from config. If true, all actor IDs
    will be hashed before storage.
    
    Returns:
        True if privacy mode is ON, False otherwise
    """
    try:
        from .config import settings
        return settings.HASH_ACTOR_IDS
    except Exception:
        # Default to False if config fails
        return False


def normalize_actor_id(raw_id: str) -> str:
    """
    Normalize actor ID with privacy mode support.
    
    This is the main function used by ingestors. It automatically
    applies hashing if privacy mode is enabled.
    
    Args:
        raw_id: Raw actor ID from source (e.g., 'juan.perez@company.com')
    
    Returns:
        Normalized ID (hashed if privacy mode ON, plain otherwise)
    
    Examples:
        # With HASH_ACTOR_IDS=true
        >>> normalize_actor_id('juan.perez@company.com')
        'emp_a1b2c3d4e5f6g7h8'
        
        # With HASH_ACTOR_IDS=false
        >>> normalize_actor_id('juan.perez@company.com')
        'juan.perez@company.com'
    """
    if not raw_id:
        return raw_id
    
    if should_hash_actors():
        from .config import settings
        return hash_pii(raw_id, settings.PRIVACY_SALT)
    
    return raw_id


def reverse_lookup(hashed_id: str) -> Optional[str]:
    """
    Reverse lookup for hashed IDs (requires mapping table).
    
    NOTE: This is NOT cryptographic reversal. It requires a separate
    mapping table that stores hash -> plain_id pairs.
    
    Args:
        hashed_id: Hashed employee ID (e.g., 'emp_a1b2c3d4...')
    
    Returns:
        Plain ID if found in mapping, None otherwise
    
    WARNING: This defeats the purpose of hashing. Only use for
    authorized admin access with proper authentication.
    """
    # TODO: Implement mapping table lookup
    # For now, return None (no reverse lookup)
    return None


def validate_privacy_config() -> bool:
    """
    Validate privacy configuration.
    
    Checks:
    - If HASH_ACTOR_IDS=true, PRIVACY_SALT must be changed from default
    - PRIVACY_SALT should be strong (min 16 chars)
    
    Returns:
        True if valid, raises ValueError otherwise
    """
    from .config import settings
    
    if settings.HASH_ACTOR_IDS:
        if settings.PRIVACY_SALT == "change_me_in_prod_please":
            raise ValueError(
                "PRIVACY_SALT must be changed from default when HASH_ACTOR_IDS=true. "
                "Set a strong, random salt in your .env file."
            )
        
        if len(settings.PRIVACY_SALT) < 16:
            raise ValueError(
                "PRIVACY_SALT is too short. Use at least 16 characters for security."
            )
    
    return True
