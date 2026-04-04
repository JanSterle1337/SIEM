from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class SuspiciousWebPathRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="web.suspicious_path",
        title="Suspicious Web Path Access",
        description="Flags known attack-oriented HTTP paths and parameters.",
        severity="medium",
        attack_stage="exploitation",
    )

    INDICATORS = (
        "/cgi-bin/vulnerable.sh",
        "/api/v1/debug",
        "/.env",
        "/.aws/credentials",
        "../",
        "<script>",
        "OR '1'",
    )

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if event.class_uid != 4002:
            return []

        path = (
            ((event.raw_payload.get("http_request") or {}).get("url") or {}).get("path") or ""
        )
        if not any(indicator in path for indicator in self.INDICATORS):
            return []

        return [
            DetectionAlert(
                title=self.metadata.title,
                description=f"HTTP request matched suspicious path indicator: {path}",
                severity=self.metadata.severity,
                priority_score=70,
                detection_type="rule",
                attack_stage=self.metadata.attack_stage,
                rule_id=self.metadata.rule_id,
                src_ip=event.src_ip,
                host=event.host,
                trace_id=event.trace_id,
                suspected_cause="Direct access to an attack-oriented path or payload.",
                confidence=0.9,
                evidence=[{"type": "path", "value": path, "class_uid": event.class_uid}],
            )
        ]
