from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.now(tz=UTC)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    return datetime.now(tz=UTC)


@dataclass(slots=True)
class NormalizedEvent:
    source_topic: str
    event_type: str
    timestamp: datetime
    raw_payload: dict[str, Any] = field(default_factory=dict)
    class_uid: int | None = None
    class_name: str | None = None
    category: str | None = None
    trace_id: str | None = None
    host: str | None = None
    src_ip: str | None = None
    dst_ip: str | None = None
    user: str | None = None
    message: str | None = None
    severity_id: int | None = None
    status: str | None = None
    metric_name: str | None = None
    metric_value: float | None = None
    metric_tags: dict[str, Any] = field(default_factory=dict)
    ground_truth_intent: str | None = None
    ground_truth_outcome: str | None = None

    @classmethod
    def from_topic_payload(
        cls, topic: str, payload: dict[str, Any]
    ) -> "NormalizedEvent":
        if topic == "ocsf-events":
            return cls.from_ocsf_event(payload, topic)
        if topic == "metrics-raw":
            return cls.from_metric_event(payload, topic)
        if topic == "ground-truth-events":
            return cls.from_ground_truth_event(payload, topic)
        return cls(
            source_topic=topic,
            event_type="unknown",
            timestamp=_parse_datetime(payload.get("time") or payload.get("timestamp")),
            raw_payload=payload,
            message=payload.get("message"),
        )

    @classmethod
    def from_ocsf_event(
        cls, payload: dict[str, Any], topic: str = "ocsf-events"
    ) -> "NormalizedEvent":
        src_endpoint = payload.get("src_endpoint") or {}
        dst_endpoint = payload.get("dst_endpoint") or {}
        user = payload.get("user") or {}
        device = payload.get("device") or {}
        return cls(
            source_topic=topic,
            event_type="ocsf",
            timestamp=_parse_datetime(payload.get("time") or payload.get("timestamp")),
            raw_payload=payload,
            class_uid=payload.get("class_uid"),
            class_name=payload.get("class_name"),
            category=payload.get("category_name"),
            trace_id=payload.get("trace_id"),
            host=device.get("hostname"),
            src_ip=src_endpoint.get("ip"),
            dst_ip=dst_endpoint.get("ip"),
            user=user.get("name"),
            message=payload.get("message"),
            severity_id=payload.get("severity_id"),
            status=payload.get("status"),
        )

    @classmethod
    def from_metric_event(
        cls, payload: dict[str, Any], topic: str = "metrics-raw"
    ) -> "NormalizedEvent":
        return cls(
            source_topic=topic,
            event_type="metric",
            timestamp=_parse_datetime(payload.get("timestamp")),
            raw_payload=payload,
            host=payload.get("host"),
            metric_name=payload.get("metric_name"),
            metric_value=payload.get("value"),
            metric_tags=payload.get("tags") or {},
            message=payload.get("metric_name"),
        )

    @classmethod
    def from_ground_truth_event(
        cls, payload: dict[str, Any], topic: str = "ground-truth-events"
    ) -> "NormalizedEvent":
        return cls(
            source_topic=topic,
            event_type="ground_truth",
            timestamp=_parse_datetime(payload.get("timestamp")),
            raw_payload=payload,
            class_uid=payload.get("class_uid"),
            category=payload.get("category"),
            trace_id=payload.get("trace_id"),
            message=payload.get("raw_log"),
            ground_truth_intent=payload.get("intent"),
            ground_truth_outcome=payload.get("outcome"),
        )
