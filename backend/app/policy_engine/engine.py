from __future__ import annotations

import threading
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, Optional

import yaml

DEFAULT_WEIGHTS: Dict[str, float] = {
    "base_skill": 1.0,
    "nivel": 0.4,
    "frequency": 0.25,
    "recency": -0.01,
    "validation": 0.5,
}

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "min_frequency": 1.0,
    "max_recency_days": 120.0,
    "min_validated_ratio": 0.3,
}


class PolicyEngineError(RuntimeError):
    """Custom error raised for policy engine failures."""


@dataclass
class RuleBundle:
    weights: Dict[str, float]
    thresholds: Dict[str, float]


class PolicyEngine:
    """Loads YAML rule configuration and evaluates dossiers."""

    def __init__(self, rules_path: Optional[str] = None) -> None:
        self._rules_path = Path(rules_path) if rules_path else Path(__file__).with_name("rules.yaml")
        self._lock = threading.Lock()
        self._rules: Dict[str, Any] = {}
        self._mtime: Optional[float] = None
        self._load_rules(force=True)

    def _load_rules(self, *, force: bool = False) -> None:
        with self._lock:
            if not self._rules_path.exists():
                raise PolicyEngineError(f"Rules file not found: {self._rules_path}")

            current_mtime = self._rules_path.stat().st_mtime
            if not force and self._mtime is not None and current_mtime == self._mtime:
                return

            with self._rules_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}

            if not isinstance(data, dict):
                raise PolicyEngineError("Invalid rules format: expected mapping at top level")

            self._rules = data
            self._mtime = current_mtime

    def _resolve_rules(
        self,
        mission_profile: Optional[str],
        overrides: Optional[Dict[str, Any]] = None,
    ) -> RuleBundle:
        self._load_rules()

        merged: Dict[str, Any] = deepcopy(self._rules.get("default", {}))

        if mission_profile:
            mission_rules = self._rules.get("missions", {}).get(mission_profile)
            if mission_rules:
                merged = self._deep_merge(merged, mission_rules)

        if overrides:
            merged = self._deep_merge(merged, overrides)

        weights = {**DEFAULT_WEIGHTS, **merged.get("weights", {})}
        thresholds = {**DEFAULT_THRESHOLDS, **merged.get("thresholds", {})}

        return RuleBundle(weights=weights, thresholds=thresholds)

    def evaluate(
        self,
        dossier: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        mission_profile = dossier.get("mission_profile")
        rules = self._resolve_rules(mission_profile, overrides)

        skills: Iterable[Dict[str, Any]] = dossier.get("skills", [])
        skill_results = []
        warnings = []

        for skill in skills:
            contributors = skill.get("contributors", [])
            if not contributors:
                skill_results.append(
                    {
                        "skill": skill.get("skill"),
                        "score": 0.0,
                        "contributors": 0,
                        "warnings": ["no_contributors"],
                        "metrics": {},
                    }
                )
                warnings.append({"skill": skill.get("skill"), "issue": "no_contributors"})
                continue

            avg_nivel = mean([c.get("nivel", 0.0) for c in contributors])
            avg_frequency = mean([c.get("frequency", 0.0) for c in contributors])
            recency_options = [c.get("recency_days") for c in contributors if c.get("recency_days") is not None]
            best_recency = min(recency_options) if recency_options else None
            validated_ratio = 0.0
            if contributors:
                validated_count = sum(1 for c in contributors if c.get("validated_by"))
                validated_ratio = validated_count / len(contributors)

            score = rules.weights.get("base_skill", 0.0)
            score += rules.weights.get("nivel", 0.0) * avg_nivel
            score += rules.weights.get("frequency", 0.0) * avg_frequency
            if best_recency is not None:
                score += rules.weights.get("recency", 0.0) * best_recency
            score += rules.weights.get("validation", 0.0) * validated_ratio

            skill_warnings = []
            if avg_frequency < rules.thresholds.get("min_frequency", 0.0):
                skill_warnings.append("low_frequency")
            if (
                best_recency is None
                or best_recency > rules.thresholds.get("max_recency_days", float("inf"))
            ):
                skill_warnings.append("stale_evidence")
            if validated_ratio < rules.thresholds.get("min_validated_ratio", 0.0):
                skill_warnings.append("low_validation")

            if skill_warnings:
                warnings.append({"skill": skill.get("skill"), "issues": skill_warnings})

            skill_results.append(
                {
                    "skill": skill.get("skill"),
                    "score": round(score, 4),
                    "contributors": len(contributors),
                    "warnings": skill_warnings,
                    "metrics": {
                        "avg_nivel": round(avg_nivel, 4),
                        "avg_frequency": round(avg_frequency, 4),
                        "best_recency": best_recency,
                        "validated_ratio": round(validated_ratio, 4),
                    },
                }
            )

        overall_score = round(mean([item["score"] for item in skill_results]) if skill_results else 0.0, 4)

        return {
            "mission_profile": mission_profile,
            "overall_score": overall_score,
            "weights": rules.weights,
            "thresholds": rules.thresholds,
            "skills": skill_results,
            "warnings": warnings,
        }

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = deepcopy(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = PolicyEngine._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result
