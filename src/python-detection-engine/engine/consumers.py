from __future__ import annotations

from dataclasses import dataclass

from kafka import KafkaConsumer

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


def build_consumer(config: EngineConfig) -> KafkaConsumer:
    return KafkaConsumer(
        *config.input_topics,
        bootstrap_servers=config.kafka_brokers,
        group_id=config.consumer_group,
        value_deserializer=lambda message: message.decode("utf-8"),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
