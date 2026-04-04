from __future__ import annotations

from dataclasses import dataclass, field

from engine.anomaly.base import AnomalyDetector
from engine.config import EngineConfig
from engine.evaluation.ground_truth import GroundTruthEvaluator
from engine.rules.base import DetectionRule
from engine.state import CorrelationState


@dataclass(slots=True)
class DetectionPipeline:
    config: EngineConfig
    rules: list[DetectionRule]
    state: CorrelationState = field(default_factory=CorrelationState)
    anomaly_detector: AnomalyDetector = field(default_factory=AnomalyDetector)
    evaluator: GroundTruthEvaluator = field(default_factory=GroundTruthEvaluator)

    def describe_startup(self) -> None:
        rule_count = len(self.rules) if self.config.rules_enabled else 0
        print("SIEM Threat Detection Engine")
        print(f"  Brokers: {', '.join(self.config.kafka_brokers)}")
        print(f"  Input topics: {', '.join(self.config.input_topics)}")
        print(f"  Alert topic: {self.config.alert_topic}")
        print(f"  Rules enabled: {self.config.rules_enabled} ({rule_count} loaded)")
        print(f"  Anomaly enabled: {self.config.anomaly_enabled}")
        print(f"  Evaluation enabled: {self.config.evaluation_enabled}")
