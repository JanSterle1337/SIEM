from __future__ import annotations

from engine.rules.base import DetectionRule
from engine.rules.correlation import DistributedExploitTraceRule
from engine.rules.persistence import BackdoorUserCreationRule
from engine.rules.web import SuspiciousWebPathRule


def build_rule_catalog() -> list[DetectionRule]:
    return [
        SuspiciousWebPathRule(),
        BackdoorUserCreationRule(),
        DistributedExploitTraceRule(),
    ]
