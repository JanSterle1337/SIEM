from __future__ import annotations

from engine.rules.base import DetectionRule
from engine.rules.api import SuspiciousInternalApiRule
from engine.rules.correlation import DistributedExploitTraceRule
from engine.rules.cron import ReverseShellCronRule
from engine.rules.persistence import BackdoorUserCreationRule
from engine.rules.process import SensitiveProcessExecutionRule
from engine.rules.web import SuspiciousWebPathRule
from engine.rules.web_payload import WebAttackPayloadRule


def build_rule_catalog() -> list[DetectionRule]:
    return [
        SuspiciousWebPathRule(),
        WebAttackPayloadRule(),
        BackdoorUserCreationRule(),
        SensitiveProcessExecutionRule(),
        ReverseShellCronRule(),
        SuspiciousInternalApiRule(),
        DistributedExploitTraceRule(),
    ]
