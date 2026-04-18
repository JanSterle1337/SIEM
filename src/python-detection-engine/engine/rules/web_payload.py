from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class WebAttackPayloadRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="web.attack_payload",
        title="Web Attack Payload Detected",
        description="Detects explicit SQLi, XSS, and traversal payload markers in HTTP paths.",
        severity="high",
        attack_stage="exploitation",
    )

    PAYLOAD_MARKERS = {
        "sqli": "OR '1'",
        "xss": "<script>",
        "path_traversal": "../",
    }

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if event.source_topic != "ocsf-events":
            return []
        if event.class_uid != 4002:
            return []

        path = (((event.raw_payload.get("http_request") or {}).get("url") or {}).get("path")) or ""
        matched_payload = next(
            (
                payload_type,
                marker,
            )
            for payload_type, marker in self.PAYLOAD_MARKERS.items()
            if marker in path
        ) if any(marker in path for marker in self.PAYLOAD_MARKERS.values()) else None

        if matched_payload is None:
            return []

        payload_type, marker = matched_payload
        return [
            DetectionAlert(
                title=self.metadata.title,
                description=f"HTTP path contained a {payload_type} payload marker: {marker}",
                severity=self.metadata.severity,
                priority_score=86,
                detection_type="rule",
                attack_stage=self.metadata.attack_stage,
                rule_id=self.metadata.rule_id,
                host=event.host,
                src_ip=event.src_ip,
                trace_id=event.trace_id,
                confidence=0.93,
                suspected_cause="A web request carried an explicit exploit payload marker.",
                evidence=[
                    {"type": "payload_type", "value": payload_type},
                    {"type": "path", "value": path},
                ],
            )
        ]
