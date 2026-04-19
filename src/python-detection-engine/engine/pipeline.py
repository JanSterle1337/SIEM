from __future__ import annotations

import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Any

from engine.anomaly.base import AnomalyDetector
from engine.config import EngineConfig
from engine.consumers import KafkaTopicBindings
from engine.evaluation.ground_truth import GroundTruthEvaluator
from engine.rules.base import DetectionRule, RuleContext
from engine.schemas.alerts import DetectionAlert
from engine.schemas.events import NormalizedEvent
from engine.state import CorrelationState


@dataclass(slots=True)
class DetectionPipeline:
    config: EngineConfig
    rules: list[DetectionRule]
    alert_producer: Any | None = None
    state: CorrelationState = field(default_factory=CorrelationState)
    anomaly_detector: AnomalyDetector = field(default_factory=AnomalyDetector)
    evaluator: GroundTruthEvaluator = field(default_factory=GroundTruthEvaluator)
    topic_bindings: KafkaTopicBindings = field(init=False)

    def __post_init__(self) -> None:
        self.topic_bindings = KafkaTopicBindings.from_config(self.config)

    def describe_startup(self) -> None:
        rule_count = len(self.rules) if self.config.rules_enabled else 0
        print("SIEM Threat Detection Engine")
        print(f"  Brokers: {', '.join(self.config.kafka_brokers)}")
        print(f"  Input topics: {', '.join(self.config.input_topics)}")
        print(f"  Alert topic: {self.config.alert_topic}")
        print(f"  Rules enabled: {self.config.rules_enabled} ({rule_count} loaded)")
        print(f"  Anomaly enabled: {self.config.anomaly_enabled}")
        print(f"  Evaluation enabled: {self.config.evaluation_enabled}")

    def process_message(self, topic: str, raw_message: str) -> NormalizedEvent | None:
        payload = self._decode_payload(raw_message)
        if payload is None:
            print(f"[decode-error] topic={topic} message={raw_message[:160]}")
            return None

        event = NormalizedEvent.from_topic_payload(topic, payload)
        self.state.remember(event)

        if event.event_type == "ground_truth" and self.config.evaluation_enabled:
            self.evaluator.ingest_ground_truth(event)

        #print(self._format_event_summary(event))
        self._evaluate_rules(event)
        self._evaluate_anomalies(event)
        return event

    @staticmethod
    def _decode_payload(raw_message: str) -> dict | None:
        try:
            payload = json.loads(raw_message)
        except JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _format_event_summary(self, event: NormalizedEvent) -> str:
        timestamp = event.timestamp.isoformat()
        class_uid = event.class_uid if event.class_uid is not None else "-"
        host = event.host or "-"
        src_ip = event.src_ip or "-"
        trace_id = event.trace_id or "-"
        metric = (
            f"{event.metric_name}={event.metric_value}"
            if event.metric_name and event.metric_value is not None
            else "-"
        )
        truth = event.ground_truth_intent or "-"
        return (
            "[event] "
            f"time={timestamp} "
            f"topic={event.source_topic} "
            f"type={event.event_type} "
            f"class_uid={class_uid} "
            f"host={host} "
            f"src_ip={src_ip} "
            f"trace_id={trace_id} "
            f"metric={metric} "
            f"truth={truth}"
        )

    def _evaluate_rules(self, event: NormalizedEvent) -> None:
        if not self.config.rules_enabled:
            return

        context = RuleContext(
            state=self.state,
            evaluation_enabled=self.config.evaluation_enabled,
        )

        for rule in self.rules:
            alerts = rule.evaluate(event, context)
            for alert in alerts:
                if self.config.evaluation_enabled:
                    alert = self.evaluator.annotate_alert(alert)
                print(self._format_alert_summary(alert))
                self._publish_alert(alert)

    def _evaluate_anomalies(self, event: NormalizedEvent) -> None:
        if not self.config.anomaly_enabled:
            return

        alerts = self.anomaly_detector.evaluate(event, self.state)
        for alert in alerts:
            if self.config.evaluation_enabled:
                alert = self.evaluator.annotate_alert(alert)
            print(self._format_alert_summary(alert))
            self._publish_alert(alert)

    def _publish_alert(self, alert: DetectionAlert) -> None:
        if self.alert_producer is None:
            return
        self.alert_producer.send(
            self.topic_bindings.alerts_topic,
            alert.to_document(),
        )

    def print_evaluation_summary(self) -> None:
        summary = self.evaluator.build_summary()
        print("[evaluation] "
              f"ground_truth_events={summary['ground_truth_events']} "
              f"matched_ground_truth_events={summary['matched_ground_truth_events']} "
              f"matched_alerts={summary['matched_alerts']} "
              f"true_positives={summary['true_positives']} "
              f"false_positives={summary['false_positives']} "
              f"false_negatives={summary['false_negatives']} "
              f"precision={summary['precision']} "
              f"recall={summary['recall']} "
              f"f1_score={summary['f1_score']}")

    @staticmethod
    def _format_alert_summary(alert: DetectionAlert) -> str:
        host = alert.host or "-"
        src_ip = alert.src_ip or "-"
        trace_id = alert.trace_id or "-"
        rule_id = alert.rule_id or "-"
        cause = alert.suspected_cause or "-"
        evidence = DetectionPipeline._format_alert_evidence(alert)
        gt_match = "matched" if alert.ground_truth_match else "unmatched"
        return (
            "[alert] "
            f"severity={alert.severity} "
            f"priority={alert.priority_score} "
            f"confidence={alert.confidence:.2f} "
            f"detection_type={alert.detection_type} "
            f"rule_id={rule_id} "
            f"title={alert.title} "
            f"host={host} "
            f"src_ip={src_ip} "
            f"trace_id={trace_id} "
            f"ground_truth={gt_match} "
            f"cause={cause} "
            f"evidence={evidence}"
        )

    @staticmethod
    def _format_alert_evidence(alert: DetectionAlert) -> str:
        if not alert.evidence:
            return "-"

        first_item = alert.evidence[0]
        evidence_type = first_item.get("type", "unknown")
        evidence_value = first_item.get("value", "-")
        return f"{evidence_type}:{evidence_value}"
