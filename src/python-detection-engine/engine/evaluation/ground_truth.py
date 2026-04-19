from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta

from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent


@dataclass(slots=True)
class GroundTruthEvaluator:
    match_window_seconds: int = 60
    truth_events: deque[NormalizedEvent] = field(default_factory=deque)
    pending_alerts: dict[str, DetectionAlert] = field(default_factory=dict)
    matched_alert_ids: set[str] = field(default_factory=set)
    matched_truth_event_ids: set[str] = field(default_factory=set)

    def ingest_ground_truth(self, event: NormalizedEvent) -> None:
        self.truth_events.append(event)
        self._try_match_pending_alerts()

    def annotate_alert(self, alert: DetectionAlert) -> DetectionAlert:
        matched_truth = self._find_match(alert)
        if matched_truth is None:
            self.pending_alerts[alert.alert_id] = alert
            return alert

        self._mark_match(alert, matched_truth)
        return alert

    def build_summary(self) -> dict[str, float | int]:
        total_truth = len(self.truth_events)
        true_positives = len(self.matched_alert_ids)
        false_positives = len(self.pending_alerts)
        false_negatives = total_truth - len(self.matched_truth_event_ids)

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1_score = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "ground_truth_events": total_truth,
            "matched_ground_truth_events": len(self.matched_truth_event_ids),
            "matched_alerts": len(self.matched_alert_ids),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
        }

    def _find_match(self, alert: DetectionAlert) -> NormalizedEvent | None:
        window = timedelta(seconds=self.match_window_seconds)
        stage = alert.attack_stage

        for truth_event in self.truth_events:
            truth_id = self._truth_event_id(truth_event)
            if truth_id in self.matched_truth_event_ids:
                continue

            time_delta = abs(truth_event.timestamp - alert.created_at)
            if time_delta > window:
                continue
            if alert.trace_id and truth_event.trace_id and alert.trace_id != truth_event.trace_id:
                continue
            if alert.host and truth_event.host and alert.host != truth_event.host:
                continue
            if alert.src_ip and truth_event.src_ip and alert.src_ip != truth_event.src_ip:
                continue
            if stage and truth_event.ground_truth_intent and not self._stage_matches_truth(stage, truth_event.ground_truth_intent):
                continue
            return truth_event

        return None

    def _try_match_pending_alerts(self) -> None:
        for alert_id, alert in list(self.pending_alerts.items()):
            matched_truth = self._find_match(alert)
            if matched_truth is None:
                continue
            self._mark_match(alert, matched_truth)
            self.pending_alerts.pop(alert_id, None)

    def _mark_match(self, alert: DetectionAlert, truth_event: NormalizedEvent) -> None:
        truth_id = self._truth_event_id(truth_event)
        self.matched_alert_ids.add(alert.alert_id)
        self.matched_truth_event_ids.add(truth_id)
        self.pending_alerts.pop(alert.alert_id, None)
        alert.ground_truth_match = {
            "timestamp": truth_event.timestamp.isoformat(),
            "intent": truth_event.ground_truth_intent,
            "category": truth_event.category,
            "trace_id": truth_event.trace_id,
            "host": truth_event.host,
            "src_ip": truth_event.src_ip,
        }

    @staticmethod
    def _stage_matches_truth(alert_stage: str, truth_intent: str) -> bool:
        normalized_alert = alert_stage.lower()
        normalized_truth = truth_intent.lower()
        aliases = {
            "impact": {"impact", "exfiltration", "execution", "persistence", "exploitation"},
            "execution": {"execution"},
            "exfiltration": {"exfiltration"},
            "persistence": {"persistence"},
            "exploitation": {"exploitation", "recon"},
        }
        return normalized_truth in aliases.get(normalized_alert, {normalized_alert})

    @staticmethod
    def _truth_event_id(event: NormalizedEvent) -> str:
        return "|".join(
            [
                event.timestamp.isoformat(),
                event.trace_id or "-",
                event.category or "-",
                event.ground_truth_intent or "-",
                event.message or "-",
            ]
        )
