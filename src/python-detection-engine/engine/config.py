from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class EngineConfig:
    kafka_brokers: list[str] = field(default_factory=lambda: ["localhost:19092"])
    input_topics: list[str] = field(
        default_factory=lambda: ["ocsf-events", "metrics-raw", "ground-truth-events"]
    )
    alert_topic: str = "siem-alerts"
    consumer_group: str = "python-threat-detection-engine"
    evaluation_enabled: bool = True
    anomaly_enabled: bool = True
    rules_enabled: bool = True

    @classmethod
    def from_env(cls) -> "EngineConfig":
        brokers = os.getenv("KAFKA_BROKERS", "localhost:19092")
        topics = os.getenv(
            "INPUT_TOPICS",
            "ocsf-events,metrics-raw,ground-truth-events",
        )
        return cls(
            kafka_brokers=[item.strip() for item in brokers.split(",") if item.strip()],
            input_topics=[item.strip() for item in topics.split(",") if item.strip()],
            alert_topic=os.getenv("ALERT_TOPIC", "siem-alerts"),
            consumer_group=os.getenv(
                "KAFKA_CONSUMER_GROUP", "python-threat-detection-engine"
            ),
            evaluation_enabled=os.getenv("EVALUATION_ENABLED", "true").lower() == "true",
            anomaly_enabled=os.getenv("ANOMALY_ENABLED", "true").lower() == "true",
            rules_enabled=os.getenv("RULES_ENABLED", "true").lower() == "true",
        )
