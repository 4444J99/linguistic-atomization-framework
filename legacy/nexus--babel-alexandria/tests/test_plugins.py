from __future__ import annotations

from nexus_babel.services.plugins import PluginRegistry


def _run(registry: PluginRegistry, *, profile: str | None):
    return registry.run_layer(
        layer="token",
        modality="text",
        text="hello world",
        baseline_output={"token_count": 2},
        baseline_confidence={"token": 0.7},
        plugin_profile=profile,
        context={"mode": "PUBLIC"},
    )


def test_deterministic_profile_uses_deterministic_plugin():
    execution = _run(PluginRegistry(ml_enabled=False), profile=None)
    assert execution.provider_name == "deterministic"
    assert execution.output == {"token_count": 2}
    assert execution.confidence == 0.7


def test_ml_first_falls_back_to_deterministic_when_ml_disabled():
    execution = _run(PluginRegistry(ml_enabled=False), profile="ml_first")
    assert execution.provider_name == "deterministic"
    assert execution.fallback_reason is not None
    assert "plugin_unsupported:ml_stub" in execution.fallback_reason


def test_ml_only_returns_baseline_with_fallback_reason_when_ml_disabled():
    execution = _run(PluginRegistry(ml_enabled=False), profile="ml_only")
    assert execution.provider_name == "deterministic"
    assert execution.runtime_ms == 0
    assert execution.output == {"token_count": 2}
    assert execution.fallback_reason is not None


def test_ml_first_uses_ml_stub_when_enabled():
    execution = _run(PluginRegistry(ml_enabled=True), profile="ml_first")
    assert execution.provider_name == "ml_stub"
    assert execution.output["provider_note"] == "ml_stub_enrichment"
    assert execution.confidence >= 0.79
