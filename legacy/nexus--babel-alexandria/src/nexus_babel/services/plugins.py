from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class PluginExecution:
    output: dict[str, Any]
    confidence: float
    provider_name: str
    provider_version: str
    runtime_ms: int
    fallback_reason: str | None = None


class LayerPlugin(Protocol):
    name: str
    version: str
    modalities: set[str]

    def healthcheck(self) -> bool: ...

    def supports(self, layer: str, modality: str) -> bool: ...

    def run(
        self,
        layer: str,
        modality: str,
        text: str,
        baseline_output: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]: ...


class DeterministicLayerPlugin:
    name = "deterministic"
    version = "v2.0"
    modalities = {"text", "pdf", "image", "audio", "binary"}

    def healthcheck(self) -> bool:
        return True

    def supports(self, layer: str, modality: str) -> bool:
        return modality in self.modalities

    def run(
        self,
        layer: str,
        modality: str,
        text: str,
        baseline_output: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        confidence = float(context.get("baseline_confidence", {}).get(layer, 0.65))
        return baseline_output, confidence


class MLStubLayerPlugin:
    name = "ml_stub"
    version = "v0.1"
    modalities = {"text", "pdf", "image", "audio"}

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def healthcheck(self) -> bool:
        return self.enabled

    def supports(self, layer: str, modality: str) -> bool:
        return self.enabled and modality in self.modalities

    def run(
        self,
        layer: str,
        modality: str,
        text: str,
        baseline_output: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        if not self.enabled:
            raise RuntimeError("ML plugin disabled by feature flag")
        enriched = {
            **baseline_output,
            "provider_note": "ml_stub_enrichment",
        }
        baseline_conf = float(context.get("baseline_confidence", {}).get(layer, 0.65))
        return enriched, min(0.95, baseline_conf + 0.1)


class PluginRegistry:
    def __init__(self, ml_enabled: bool = False):
        self.plugins: dict[str, LayerPlugin] = {
            "deterministic": DeterministicLayerPlugin(),
            "ml_stub": MLStubLayerPlugin(enabled=ml_enabled),
        }

    def health(self) -> dict[str, bool]:
        return {name: plugin.healthcheck() for name, plugin in self.plugins.items()}

    def _profile_chain(self, plugin_profile: str | None) -> list[str]:
        profile = (plugin_profile or "deterministic").strip().lower()
        if profile == "ml_first":
            return ["ml_stub", "deterministic"]
        if profile == "ml_only":
            return ["ml_stub"]
        return ["deterministic"]

    def run_layer(
        self,
        *,
        layer: str,
        modality: str,
        text: str,
        baseline_output: dict[str, Any],
        baseline_confidence: dict[str, float],
        plugin_profile: str | None,
        context: dict[str, Any] | None = None,
    ) -> PluginExecution:
        ctx = dict(context or {})
        ctx["baseline_confidence"] = baseline_confidence
        chain = self._profile_chain(plugin_profile)
        fallback_reasons: list[str] = []

        for plugin_name in chain:
            plugin = self.plugins.get(plugin_name)
            if not plugin:
                fallback_reasons.append(f"plugin_not_found:{plugin_name}")
                continue
            if not plugin.supports(layer, modality):
                fallback_reasons.append(f"plugin_unsupported:{plugin_name}")
                continue
            start = time.perf_counter()
            try:
                output, confidence = plugin.run(layer, modality, text, baseline_output, ctx)
                runtime_ms = int((time.perf_counter() - start) * 1000)
                return PluginExecution(
                    output=output,
                    confidence=float(confidence),
                    provider_name=plugin.name,
                    provider_version=plugin.version,
                    runtime_ms=runtime_ms,
                    fallback_reason=";".join(fallback_reasons) if fallback_reasons else None,
                )
            except Exception as exc:  # pragma: no cover - defensive plugin boundary
                fallback_reasons.append(f"{plugin_name}:{exc}")
                continue

        return PluginExecution(
            output=baseline_output,
            confidence=float(baseline_confidence.get(layer, 0.0)),
            provider_name="deterministic",
            provider_version="v2.0",
            runtime_ms=0,
            fallback_reason=";".join(fallback_reasons) if fallback_reasons else "all_plugins_failed",
        )
