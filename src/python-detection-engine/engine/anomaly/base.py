from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from statistics import mean, pstdev

from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent
from engine.state import CorrelationState


@dataclass(slots=True)
class AnomalyDetector:
    model_id: str = "baseline.statistical.v1"
    warmup_samples: int = 20
    zscore_threshold: float = 4.0
    cooldown_seconds: int = 60
    supported_metrics: tuple[str, ...] = (
        "cpu_usage_pct",
        "mem_usage_pct",
        "network_io_kbs",
        "disk_io_kbs",
    )

    def evaluate(
        self, event: NormalizedEvent, state: CorrelationState
    ) -> list[DetectionAlert]:
        if event.event_type != "metric":
            return []
        if not event.host or not event.metric_name or event.metric_value is None:
            return []
        if event.metric_name not in self.supported_metrics:
            return []

        metric_history = state.metrics_by_host.get(event.host, {}).get(event.metric_name, [])
        baseline_values = metric_history[:-1] if metric_history else []
        if len(baseline_values) < self.warmup_samples:
            return []

        baseline_mean = mean(baseline_values)
        baseline_stddev = pstdev(baseline_values)
        if baseline_stddev == 0:
            return []

        zscore = (event.metric_value - baseline_mean) / baseline_stddev
        if zscore < self.zscore_threshold:
            return []

        anomaly_key = f"{event.host}:{event.metric_name}"
        cooldown_until = state.anomaly_cooldowns.get(anomaly_key)
        if cooldown_until is not None and event.timestamp < cooldown_until:
            return []

        state.anomaly_cooldowns[anomaly_key] = event.timestamp + timedelta(
            seconds=self.cooldown_seconds
        )

        return [
            DetectionAlert(
                title="Metric Spike Anomaly",
                description=(
                    f"Metric {event.metric_name} on host {event.host} exceeded the rolling baseline "
                    f"with z-score {zscore:.2f}."
                ),
                severity="medium",
                priority_score=72,
                detection_type="anomaly",
                attack_stage="impact",
                model_id=self.model_id,
                host=event.host,
                trace_id=event.trace_id,
                confidence=min(0.99, 0.6 + (zscore / 10.0)),
                suspected_cause="Observed metric value is significantly above the recent host baseline.",
                evidence=[
                    {"type": "metric_name", "value": event.metric_name},
                    {"type": "metric_value", "value": round(event.metric_value, 2)},
                    {"type": "baseline_mean", "value": round(baseline_mean, 2)},
                    {"type": "zscore", "value": round(zscore, 2)},
                ],
            )
        ]
        return []
