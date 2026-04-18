from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class DistributedExploitTraceRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="correlation.distributed_exploit_trace",
        title="Correlated Distributed Exploit Activity",
        description="Detects a trace_id that spans suspicious web access, internal API access, and sensitive process activity.",
        severity="high",
        attack_stage="exfiltration",
    )

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if not event.trace_id:
            return []

        trace_events = context.state.by_trace_id.get(event.trace_id)
        if not trace_events:
            return []

        matched_http = next(
            (
                item
                for item in trace_events
                if item.get("class_uid") == 4002
                and item.get("http_path") in {"/api/v1/debug", "/cgi-bin/vulnerable.sh"}
            ),
            None,
        )
        matched_api = next(
            (
                item
                for item in trace_events
                if item.get("class_uid") == 6003
                and item.get("api_endpoint") == "/v2/internal/config"
            ),
            None,
        )
        matched_process = next(
            (
                item
                for item in trace_events
                if item.get("message") and "cat /etc/shadow" in item.get("message", "")
            ),
            None,
        )

        if not (matched_http and matched_api and matched_process):
            return []

        alert_key = f"{self.metadata.rule_id}:{event.trace_id}"
        if not context.state.mark_alert_fired(alert_key):
            return []

        return [
            DetectionAlert(
                title=self.metadata.title,
                description=(
                    "A single trace_id touched a suspicious web path, an internal API endpoint, and a sensitive process command."
                ),
                severity=self.metadata.severity,
                priority_score=92,
                detection_type="rule",
                attack_stage=self.metadata.attack_stage,
                rule_id=self.metadata.rule_id,
                src_ip=event.src_ip,
                host=event.host,
                trace_id=event.trace_id,
                confidence=0.96,
                suspected_cause="Coordinated exploit activity spanning web, API, and host process layers.",
                evidence=[
                    {"type": "trace_id", "value": event.trace_id},
                    {"type": "http_path", "value": matched_http.get("http_path")},
                    {"type": "api_endpoint", "value": matched_api.get("api_endpoint")},
                    {"type": "process", "value": matched_process.get("message")},
                ],
            )
        ]
