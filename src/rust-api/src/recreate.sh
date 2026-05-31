#!/usr/bin/env bash
set -euo pipefail

QW="${QW:-http://localhost:7280}"

declare -A INDEX_CONFIGS=(
  ["metrics-raw"]="metrics-index-config.yaml"
  ["ocsf-events"]="ocsf-index-config.yaml"
  ["raw-logs"]="raw-logs-index-config.yaml"
  ["siem-alerts"]="siem-alerts-config.yaml"
)

for INDEX_ID in "${!INDEX_CONFIGS[@]}"; do
  CONFIG_FILE="${INDEX_CONFIGS[$INDEX_ID]}"

  echo "Deleting index: $INDEX_ID"
  curl -sS -X DELETE "$QW/api/v1/indexes/$INDEX_ID" || true
  echo

  echo "Recreating index: $INDEX_ID from $CONFIG_FILE"
  curl -sS -X POST "$QW/api/v1/indexes" \
    -H "Content-Type: application/yaml" \
    --data-binary "@$CONFIG_FILE"
  echo
done