from __future__ import annotations

from dataclasses import dataclass

from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent
from engine.state import CorrelationState


@dataclass(slots=True)
class AnomalyDetector:
    model_id: str = "baseline.statistical.v1"

    def evaluate(
        self, event: NormalizedEvent, state: CorrelationState
    ) -> list[DetectionAlert]:
        # Placeholder for rolling-baseline and rare-event logic.
        return []
