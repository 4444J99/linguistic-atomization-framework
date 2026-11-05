#!/usr/bin/env bash
set -euo pipefail
uvicorn nexus_babel.main:app --host 0.0.0.0 --port 8000 --reload
