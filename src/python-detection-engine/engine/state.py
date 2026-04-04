from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


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

    def summary(self) -> dict[str, int]:
        return {
            "tracked_ips": len(self.by_ip),
            "tracked_hosts": len(self.by_host),
            "tracked_traces": len(self.by_trace_id),
            "tracked_metric_hosts": len(self.metrics_by_host),
        }
