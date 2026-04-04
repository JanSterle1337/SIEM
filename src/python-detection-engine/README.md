# Python Threat Detection Engine

This package is the new foundation for the SIEM threat detection engine.

## Planned responsibilities

- Normalize `ocsf-events`, `metrics-raw`, and `ground-truth-events` into one internal event model.
- Run two detection paths:
  - deterministic rule-based detections
  - anomaly detection over metrics and selected log features
- Emit enriched alerts to `siem-alerts`
- Evaluate detections against `ground-truth-events`

## Package layout

- `detection_engine.py`
  - thin entrypoint
- `engine/config.py`
  - environment-driven runtime config
- `engine/schemas/`
  - normalized event and alert contracts
- `engine/rules/`
  - rule interfaces and concrete rules
- `engine/catalog/`
  - rule registration
- `engine/anomaly/`
  - anomaly detection path
- `engine/evaluation/`
  - ground truth matching and metrics
- `engine/state.py`
  - correlation and rolling state
- `engine/pipeline.py`
  - high-level engine wiring

## Immediate next implementation steps

1. Add Kafka consumer/producer loop.
2. Update state on every event.
3. Execute rules and anomaly detectors.
4. Match alerts with ground truth in evaluation mode.
5. Publish alerts using the new alert schema.

## Current status

- Kafka consumer skeleton is wired in.
- Messages are routed by topic and normalized into `NormalizedEvent`.
- Minimal correlation state is updated for IPs, hosts, trace IDs, and metrics.
- Ground truth events are stored by the evaluator in evaluation mode.
- The engine currently prints a short event summary for each processed message.

Rules, anomaly detection, and alert publishing are intentionally not active yet.
