from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class BackdoorUserCreationRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="persistence.backdoor_user",
        title="Suspicious Backdoor Account Creation",
        description="Detects suspicious account creation tied to persistence patterns.",
        severity="high",
        attack_stage="persistence",
    )

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if event.class_uid != 3001:
            return []
        if "backdoor_user" not in (event.message or ""):
            return []

        return [
            DetectionAlert(
                title=self.metadata.title,
                description="A suspicious account named backdoor_user was created.",
                severity=self.metadata.severity,
                priority_score=88,
                detection_type="rule",
                attack_stage=self.metadata.attack_stage,
                rule_id=self.metadata.rule_id,
                host=event.host,
                user="backdoor_user",
                confidence=0.95,
                suspected_cause="Persistence attempt through account creation.",
                evidence=[{"type": "message", "value": event.message}],
            )
        ]
