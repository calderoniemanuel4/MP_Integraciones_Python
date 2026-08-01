#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

export FIRESTORE_EMULATOR_HOST="${FIRESTORE_EMULATOR_HOST-127.0.0.1:8080}"
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT-mp-checkout-pro-test}"

.venv/bin/python -m uvicorn app.main:app --reload
