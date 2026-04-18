from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class SuspiciousInternalApiRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="api.suspicious_internal_endpoint",
        title="Suspicious Internal API Access",
        description="Detects direct access to sensitive internal API endpoints.",
        severity="high",
        attack_stage="exploitation",
    )

    SENSITIVE_ENDPOINTS = {
        "/v2/internal/config",
    }

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if event.source_topic != "ocsf-events":
            return []
        if event.class_uid != 6003:
            return []

        api_data = event.raw_payload.get("api") or {}
        endpoint = api_data.get("endpoint")
        if endpoint not in self.SENSITIVE_ENDPOINTS:
            return []

        status = ((event.raw_payload.get("http_response") or {}).get("status"))
        if status is not None and int(status) >= 400:
            return []

        return [
            DetectionAlert(
                title=self.metadata.title,
                description=f"Sensitive internal API endpoint was accessed: {endpoint}",
                severity=self.metadata.severity,
                priority_score=84,
                detection_type="rule",
                attack_stage=self.metadata.attack_stage,
                rule_id=self.metadata.rule_id,
                host=event.host,
                src_ip=event.src_ip,
                trace_id=event.trace_id,
                confidence=0.9,
                suspected_cause="An internal configuration endpoint was accessed successfully.",
                evidence=[
                    {"type": "endpoint", "value": endpoint},
                    {"type": "status", "value": status},
                ],
            )
        ]
