from __future__ import annotations

from dataclasses import dataclass

from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent
from engine.state import CorrelationState


@dataclass(slots=True)
class RuleMetadata:
    rule_id: str
    title: str
    description: str
    severity: str
    attack_stage: str


@dataclass(slots=True)
class RuleContext:
    state: CorrelationState
    evaluation_enabled: bool


class DetectionRule:
    metadata: RuleMetadata

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        raise NotImplementedError
