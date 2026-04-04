from __future__ import annotations

from engine.rules.base import DetectionRule, RuleContext, RuleMetadata
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


class DistributedExploitTraceRule(DetectionRule):
    metadata = RuleMetadata(
        rule_id="correlation.distributed_exploit_trace",
        title="Correlated Distributed Exploit Trace",
        description="Reserves a dedicated rule for multi-event trace_id correlation.",
        severity="high",
        attack_stage="exfiltration",
    )

    def evaluate(
        self, event: NormalizedEvent, context: RuleContext
    ) -> list[DetectionAlert]:
        if not event.trace_id:
            return []
        return []
