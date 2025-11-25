"""
Quick test for Phase 4 Scoring Enhancements

Tests:
1. Impact weighting (High vs Low)
2. Decay factor (recent vs old)
3. Combined effect on scoring
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.scoring import (
    _compute_impact_weight,
    _compute_decay_factor,
    compute_skill_level_from_relation
)

def test_impact_weighting():
    """Test that High impact > Medium > Low"""
    high = _compute_impact_weight('High')
    medium = _compute_impact_weight('Medium')
    low = _compute_impact_weight('Low')
    
    assert high == 1.5, f"Expected High=1.5, got {high}"
    assert medium == 1.0, f"Expected Medium=1.0, got {medium}"
    assert low == 0.5, f"Expected Low=0.5, got {low}"
    print("✅ Impact weighting works correctly")

def test_decay_factor():
    """Test that recent evidence > old evidence"""
    fresh = _compute_decay_factor(30)   # 30 days
    aging = _compute_decay_factor(120)  # 120 days
    stale = _compute_decay_factor(200)  # 200 days
    rotten = _compute_decay_factor(400) # 400 days
    
    assert fresh == 1.0, f"Expected fresh=1.0, got {fresh}"
    assert aging == 0.9, f"Expected aging=0.9, got {aging}"
    assert stale == 0.7, f"Expected stale=0.7, got {stale}"
    assert rotten == 0.5, f"Expected rotten=0.5, got {rotten}"
    print("✅ Decay factor works correctly")

def test_combined_scoring():
    """Test that scoring combines impact + decay correctly"""
    # Scenario 1: Recent High impact evidence
    recent_high = [
        {'date': '2025-01-15', 'impacto': 'High'},
        {'date': '2025-01-10', 'impacto': 'High'},
        {'date': '2025-01-05', 'impacto': 'High'},
    ]
    score1 = compute_skill_level_from_relation(recent_high, '2025-01-15')
    
    # Scenario 2: Old Low impact evidence
    old_low = [
        {'date': '2023-01-15', 'impacto': 'Low'},
        {'date': '2023-01-10', 'impacto': 'Low'},
        {'date': '2023-01-05', 'impacto': 'Low'},
    ]
    score2 = compute_skill_level_from_relation(old_low, '2023-01-15')
    
    print(f"  Recent High impact score: {score1}")
    print(f"  Old Low impact score: {score2}")
    
    assert score1 > score2, f"Expected recent High ({score1}) > old Low ({score2})"
    print("✅ Combined scoring works correctly")

def test_backward_compatibility():
    """Test that old evidence format still works"""
    legacy_evidence = [
        "https://github.com/repo/commit/abc123",
        "https://github.com/repo/commit/def456",
    ]
    score = compute_skill_level_from_relation(legacy_evidence, '2025-01-01')
    assert 1.0 <= score <= 5.0, f"Score {score} out of range"
    print(f"✅ Backward compatibility works (legacy score: {score})")

if __name__ == "__main__":
    print("Testing Phase 4 Scoring Enhancements...\n")
    
    try:
        test_impact_weighting()
        test_decay_factor()
        test_combined_scoring()
        test_backward_compatibility()
        
        print("\n🎉 All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
