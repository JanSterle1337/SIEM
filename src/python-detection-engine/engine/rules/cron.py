from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class ReverseShellCronRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="persistence.reverse_shell_cron",
        title="Reverse Shell Cron Persistence",
        description="Detects cron jobs that resemble reverse shell persistence.",
        severity="critical",
        attack_stage="persistence",
    )

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if event.source_topic != "ocsf-events":
            return []

        message = event.message or ""
        if "cron" not in message.lower():
            return []
        if "/dev/tcp/" not in message:
            return []
        if "bash -i" not in message and "/bin/bash -i" not in message:
            return []

        return [
            DetectionAlert(
                title=self.metadata.title,
                description="Cron job matched a reverse shell persistence pattern.",
                severity=self.metadata.severity,
                priority_score=97,
                detection_type="rule",
                attack_stage=self.metadata.attack_stage,
                rule_id=self.metadata.rule_id,
                host=event.host,
                src_ip=event.src_ip,
                trace_id=event.trace_id,
                confidence=0.98,
                suspected_cause="A scheduled task appears to establish a reverse shell over TCP.",
                evidence=[
                    {"type": "message", "value": message},
                    {"type": "indicator", "value": "/dev/tcp/"},
                ],
            )
        ]
