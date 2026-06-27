#!/usr/bin/env bash
set -euo pipefail
curl -sS -X POST "${BASE_URL:-http://localhost:8000}/checkout/preference" \
  -H "Content-Type: application/json" \
  -d '{"product_code":"test-product","quantity":1}'

