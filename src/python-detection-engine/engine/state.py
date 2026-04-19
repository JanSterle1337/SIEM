from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from engine.schemas.events import NormalizedEvent


@dataclass(slots=True)
class CorrelationState:
    by_ip: dict[str, deque[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    by_host: dict[str, deque[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    by_trace_id: dict[str, deque[dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    metrics_by_host: dict[str, dict[str, list[float]]] = field(
        default_factory=lambda: defaultdict(dict)
    )
    fired_alert_keys: set[str] = field(default_factory=set)
    anomaly_cooldowns: dict[str, datetime] = field(default_factory=dict)

    def summary(self) -> dict[str, int]:
        return {
            "tracked_ips": len(self.by_ip),
            "tracked_hosts": len(self.by_host),
            "tracked_traces": len(self.by_trace_id),
            "tracked_metric_hosts": len(self.metrics_by_host),
        }

    def remember(self, event: NormalizedEvent, max_items: int = 50) -> None:
        event_snapshot = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "class_uid": event.class_uid,
            "host": event.host,
            "src_ip": event.src_ip,
            "trace_id": event.trace_id,
            "message": event.message,
            "http_path": (
                (((event.raw_payload.get("http_request") or {}).get("url") or {}).get("path"))
                if event.raw_payload
                else None
            ),
            "api_endpoint": (
                ((event.raw_payload.get("api") or {}).get("endpoint"))
                if event.raw_payload
                else None
            ),
        }

        if event.src_ip:
            self.by_ip[event.src_ip].append(event_snapshot)
            self._trim(self.by_ip[event.src_ip], max_items)

        if event.host:
            self.by_host[event.host].append(event_snapshot)
            self._trim(self.by_host[event.host], max_items)

        if event.trace_id:
            self.by_trace_id[event.trace_id].append(event_snapshot)
            self._trim(self.by_trace_id[event.trace_id], max_items)

        if event.event_type == "metric" and event.host and event.metric_name:
            host_metrics = self.metrics_by_host[event.host]
            values = host_metrics.setdefault(event.metric_name, [])
            if event.metric_value is not None:
                values.append(event.metric_value)
            if len(values) > max_items:
                del values[:-max_items]

    @staticmethod
    def _trim(items: deque[dict[str, Any]], max_items: int) -> None:
        while len(items) > max_items:
            items.popleft()

    def mark_alert_fired(self, key: str) -> bool:
        if key in self.fired_alert_keys:
            return False
        self.fired_alert_keys.add(key)
        return True
