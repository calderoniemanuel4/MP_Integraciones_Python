#!/usr/bin/env bash
set -euo pipefail
curl -i -X POST "${BASE_URL:-http://localhost:8000}/webhooks/mercadopago?data.id=123" \
  -H "Content-Type: application/json" \
  -d '{"id":"evt-test","type":"payment","action":"payment.updated","data":{"id":"123"}}'

