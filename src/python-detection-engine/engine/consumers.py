from __future__ import annotations

from dataclasses import dataclass

from engine.config import EngineConfig


@dataclass(slots=True)
class KafkaTopicBindings:
    ocsf_topic: str = "ocsf-events"
    metrics_topic: str = "metrics-raw"
    ground_truth_topic: str = "ground-truth-events"
    alerts_topic: str = "siem-alerts"

    @classmethod
    def from_config(cls, config: EngineConfig) -> "KafkaTopicBindings":
        topics = {topic: topic for topic in config.input_topics}
        return cls(
            ocsf_topic=topics.get("ocsf-events", "ocsf-events"),
            metrics_topic=topics.get("metrics-raw", "metrics-raw"),
            ground_truth_topic=topics.get("ground-truth-events", "ground-truth-events"),
            alerts_topic=config.alert_topic,
        )
