from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricsService:
    counters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    timings: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def inc(self, key: str, value: float = 1.0) -> None:
        self.counters[key] = float(self.counters.get(key, 0.0) + value)

    def observe(self, key: str, value_ms: float) -> None:
        self.timings.setdefault(key, []).append(float(value_ms))

    def snapshot(self) -> dict[str, dict]:
        timing_summary = {}
        for key, values in self.timings.items():
            if not values:
                timing_summary[key] = {"count": 0, "avg_ms": 0.0, "p95_ms": 0.0}
                continue
            ordered = sorted(values)
            index = max(0, int(len(ordered) * 0.95) - 1)
            timing_summary[key] = {
                "count": len(values),
                "avg_ms": round(sum(values) / len(values), 3),
                "p95_ms": round(ordered[index], 3),
            }
        return {"counters": dict(self.counters), "timings": timing_summary}
