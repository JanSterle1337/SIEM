from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


LOCAL_TZ = datetime.now().astimezone().tzinfo


@dataclass(slots=True)
class DetectionAlert:
    title: str
    description: str
    severity: str
    priority_score: int
    detection_type: str
    status: str = "new"
    confidence: float = 0.0
    attack_stage: str | None = None
    rule_id: str | None = None
    model_id: str | None = None
    src_ip: str | None = None
    host: str | None = None
    user: str | None = None
    trace_id: str | None = None
    suspected_cause: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    ground_truth_match: dict[str, Any] | None = None
    alert_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=LOCAL_TZ))

    def to_document(self) -> dict[str, Any]:
        document = asdict(self)
        document["created_at"] = self.created_at.timestamp()
        return document
