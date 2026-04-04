from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


@dataclass(slots=True)
class GroundTruthEvaluator:
    truth_events: deque[NormalizedEvent] = field(default_factory=deque)
    matched_alert_ids: set[str] = field(default_factory=set)

    def ingest_ground_truth(self, event: NormalizedEvent) -> None:
        self.truth_events.append(event)

    def annotate_alert(self, alert: DetectionAlert) -> DetectionAlert:
        # Placeholder for time-window matching between alerts and labeled attacks.
        return alert
