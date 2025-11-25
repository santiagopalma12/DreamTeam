"""
Mission Profiles - Phase 6: Policy & Governance

Defines different mission contexts that affect team composition strategy.
Each profile has different optimization weights and preferred strategies.

Available Profiles:
- mantenimiento: Stability and reliability
- innovacion: Experimentation and learning
- entrega_rapida: Speed and proven synergy
"""

from typing import Dict, Any


MISSION_PROFILES = {
    'mantenimiento': {
        'name': 'Maintenance',
        'description': 'Stability and reliability over speed. Prioritizes experienced team members.',
        'weights': {
            'skill_level': 1.5,      # Prioritize high skill levels
            'availability': 1.0,     # Standard availability importance
            'collaboration': 0.5,    # Less important for maintenance
            'linchpin_penalty': 0.3  # Avoid dependencies (moderate)
        },
        'strategy_preference': 'safe_bet',
        'min_skill_threshold': 3.5,  # Prefer experienced members
        'color': '#4CAF50'  # Green for stability
    },
    
    'innovacion': {
        'name': 'Innovation',
        'description': 'Experimentation and learning. Encourages knowledge sharing and growth.',
        'weights': {
            'skill_level': 0.8,      # Mix of levels OK
            'availability': 0.7,     # Flexibility in time
            'collaboration': 1.2,    # Important for knowledge sharing
            'linchpin_penalty': 0.0  # OK to use experts/linchpins
        },
        'strategy_preference': 'growth',
        'min_skill_threshold': 2.5,  # Allow juniors
        'color': '#2196F3'  # Blue for innovation
    },
    
    'entrega_rapida': {
        'name': 'Fast Delivery',
        'description': 'Speed and proven synergy. Leverages existing collaboration patterns.',
        'weights': {
            'skill_level': 1.0,      # Balanced skill requirement
            'availability': 1.5,     # Critical - need full-time focus
            'collaboration': 2.0,    # Very important - past synergy
            'linchpin_penalty': 0.5  # Moderate avoidance
        },
        'strategy_preference': 'speed',
        'min_skill_threshold': 3.0,  # Need competent members
        'color': '#FF9800'  # Orange for urgency
    }
}


def get_mission_profile(profile_name: str) -> Dict[str, Any]:
    """
    Get mission profile configuration.
    
    Args:
        profile_name: One of 'mantenimiento', 'innovacion', 'entrega_rapida'
    
    Returns:
        Profile configuration dict
    
    Examples:
        >>> profile = get_mission_profile('entrega_rapida')
        >>> profile['weights']['availability']
        1.5
    """
    # Default to maintenance if invalid profile
    if profile_name not in MISSION_PROFILES:
        return MISSION_PROFILES['mantenimiento']
    
    return MISSION_PROFILES[profile_name]


def list_mission_profiles() -> list:
    """
    Get list of all available mission profiles.
    
    Returns:
        List of profile summaries (without weights)
    """
    return [
        {
            'id': key,
            'name': profile['name'],
            'description': profile['description'],
            'strategy_preference': profile['strategy_preference'],
            'color': profile['color']
        }
        for key, profile in MISSION_PROFILES.items()
    ]


def validate_mission_profile(profile_name: str) -> bool:
    """
    Check if mission profile name is valid.
    
    Args:
        profile_name: Profile name to validate
    
    Returns:
        True if valid, False otherwise
    """
    return profile_name in MISSION_PROFILES
