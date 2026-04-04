from __future__ import annotations

from engine.rules.base import DetectionRule
from engine.rules.web import SuspiciousWebPathRule


def build_rule_catalog() -> list[DetectionRule]:
    return [
        SuspiciousWebPathRule(),
    ]
