from __future__ import annotations

from engine.catalog.rule_catalog import build_rule_catalog
from engine.config import EngineConfig
from engine.consumers import build_consumer
from engine.pipeline import DetectionPipeline


def main() -> None:
    config = EngineConfig.from_env()
    pipeline = DetectionPipeline(
        config=config,
        rules=build_rule_catalog(),
    )
    pipeline.describe_startup()

    consumer = build_consumer(config)
    print("  Consumer loop: enabled")

    for message in consumer:
        topic = message.topic
        raw_message = message.value
        pipeline.process_message(topic, raw_message)
