from __future__ import annotations

import os
import time
import math
from statistics import mean

from fastapi.testclient import TestClient

from nexus_babel.main import app


if __name__ == "__main__":
    api_key = os.environ.get("NEXUS_BOOTSTRAP_OPERATOR_KEY", "nexus-dev-operator-key")  # allow-secret
    headers = {"X-Nexus-API-Key": api_key}
    mean_threshold = float(os.environ.get("NEXUS_LOAD_MEAN_THRESHOLD", "1.5"))
    p95_threshold = float(os.environ.get("NEXUS_LOAD_P95_THRESHOLD", "2.0"))
    durations: list[float] = []
    with TestClient(app) as client:
        docs = client.get("/api/v1/documents", headers=headers).json().get("documents", [])
        if not docs:
            raise SystemExit("No documents found. Run scripts/ingest_corpus.py first.")

        target = docs[0]["id"]
        for _ in range(25):
            start = time.perf_counter()
            resp = client.post("/api/v1/analyze", headers=headers, json={"document_id": target, "mode": "PUBLIC"})
            resp.raise_for_status()
            durations.append(time.perf_counter() - start)

    avg = mean(durations)
    p95_index = max(0, math.ceil(len(durations) * 0.95) - 1)
    p95 = sorted(durations)[p95_index]
    print(f"avg={avg:.4f}s p95={p95:.4f}s thresholds(avg<{mean_threshold}, p95<{p95_threshold})")
    if avg >= mean_threshold or p95 >= p95_threshold:
        raise SystemExit(1)
