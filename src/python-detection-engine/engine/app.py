from __future__ import annotations

from engine.catalog.rule_catalog import build_rule_catalog
from engine.config import EngineConfig
from engine.pipeline import DetectionPipeline


def main() -> None:
    config = EngineConfig.from_env()
    pipeline = DetectionPipeline(
        config=config,
        rules=build_rule_catalog(),
    )
    pipeline.describe_startup()
