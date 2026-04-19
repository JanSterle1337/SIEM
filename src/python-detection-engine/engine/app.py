from __future__ import annotations

from engine.catalog.rule_catalog import build_rule_catalog
from engine.config import EngineConfig
from engine.consumers import build_consumer, build_producer
from engine.pipeline import DetectionPipeline


def main() -> None:
    config = EngineConfig.from_env()
    producer = build_producer(config)
    pipeline = DetectionPipeline(
        config=config,
        rules=build_rule_catalog(),
        alert_producer=producer,
    )
    pipeline.describe_startup()

    consumer = build_consumer(config)
    print("  Consumer loop: enabled")
    print(f"  Alert publishing: enabled ({config.alert_topic})")

    try:
        for message in consumer:
            topic = message.topic
            raw_message = message.value
            pipeline.process_message(topic, raw_message)
    except KeyboardInterrupt:
        if config.evaluation_enabled:
            pipeline.print_evaluation_summary()
        print("SIEM Threat Detection Engine stopped.")
    finally:
        producer.flush()
        producer.close()
