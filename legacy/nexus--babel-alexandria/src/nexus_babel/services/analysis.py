from __future__ import annotations

import hashlib
import statistics
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import AnalysisRun, Branch, Document, LayerOutput
from nexus_babel.services.plugins import PluginRegistry
from nexus_babel.services.rhetoric import RhetoricalAnalyzer
from nexus_babel.services.text_utils import split_paragraphs, split_sentences, tokenize_words


class AnalysisService:
    def __init__(self, rhetorical_analyzer: RhetoricalAnalyzer, plugin_registry: PluginRegistry):
        self.rhetorical_analyzer = rhetorical_analyzer
        self.plugin_registry = plugin_registry

    def analyze(
        self,
        session: Session,
        document_id: str | None,
        branch_id: str | None,
        layers: list[str],
        mode: str,
        *,
        execution_mode: str = "sync",
        plugin_profile: str | None = None,
        job_id: str | None = None,
    ) -> tuple[AnalysisRun, dict[str, Any]]:
        text = ""
        modality = "text"
        hypergraph_ids: dict[str, Any] = {}
        source_metadata: dict[str, Any] = {}

        if document_id:
            doc = session.scalar(select(Document).where(Document.id == document_id))
            if not doc:
                raise ValueError(f"document_id {document_id} not found")
            text = str((doc.provenance or {}).get("extracted_text", ""))
            modality = doc.modality
            source_metadata = dict(doc.provenance or {})
            hypergraph_ids = (doc.provenance or {}).get("hypergraph", {})
        elif branch_id:
            branch = session.scalar(select(Branch).where(Branch.id == branch_id))
            if not branch:
                raise ValueError(f"branch_id {branch_id} not found")
            text = str((branch.state_snapshot or {}).get("current_text", ""))
            hypergraph_ids = {"branch_id": branch.id}
            source_metadata = dict(branch.state_snapshot or {})
        else:
            raise ValueError("Either document_id or branch_id must be provided")

        requested = layers or [
            "token",
            "morphology",
            "syntax",
            "semantics",
            "pragmatics",
            "discourse",
            "sociolinguistics",
            "rhetoric",
            "semiotic",
        ]

        baseline_outputs, baseline_confidence = self._build_baseline_outputs(text, source_metadata)

        selected_outputs: dict[str, Any] = {}
        confidence_bundle: dict[str, float] = {}
        plugin_provenance: dict[str, Any] = {}
        layer_rows: list[LayerOutput] = []

        for layer in requested:
            baseline_output = baseline_outputs.get(layer, {})
            executed = self.plugin_registry.run_layer(
                layer=layer,
                modality=modality,
                text=text,
                baseline_output=baseline_output,
                baseline_confidence=baseline_confidence,
                plugin_profile=plugin_profile,
                context={"mode": mode.upper()},
            )
            selected_outputs[layer] = executed.output
            confidence_bundle[layer] = round(float(executed.confidence), 4)
            plugin_provenance[layer] = {
                "provider_name": executed.provider_name,
                "provider_version": executed.provider_version,
                "runtime_ms": executed.runtime_ms,
                "fallback_reason": executed.fallback_reason,
            }
            layer_rows.append(
                LayerOutput(
                    layer_name=layer,
                    output=executed.output,
                    confidence=float(executed.confidence),
                    provider_name=executed.provider_name,
                    provider_version=executed.provider_version,
                    runtime_ms=executed.runtime_ms,
                    fallback_reason=executed.fallback_reason,
                )
            )

        run = AnalysisRun(
            document_id=document_id,
            branch_id=branch_id,
            mode=mode.upper(),
            execution_mode=execution_mode,
            plugin_profile=plugin_profile,
            job_id=job_id,
            layers=requested,
            confidence=confidence_bundle,
            results=selected_outputs,
            run_metadata={
                "plugin_provenance": plugin_provenance,
                "source_modality": modality,
                "plugin_health": self.plugin_registry.health(),
            },
        )
        session.add(run)
        session.flush()

        for row in layer_rows:
            row.analysis_run_id = run.id
            session.add(row)

        return run, {
            "mode": mode.upper(),
            "layers": selected_outputs,
            "confidence_bundle": confidence_bundle,
            "hypergraph_ids": hypergraph_ids,
            "plugin_provenance": plugin_provenance,
        }

    def get_run(self, session: Session, run_id: str) -> dict[str, Any]:
        run = session.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
        if not run:
            raise ValueError(f"analysis run {run_id} not found")
        outputs = session.scalars(select(LayerOutput).where(LayerOutput.analysis_run_id == run.id)).all()
        return {
            "analysis_run_id": run.id,
            "document_id": run.document_id,
            "branch_id": run.branch_id,
            "mode": run.mode,
            "execution_mode": run.execution_mode,
            "plugin_profile": run.plugin_profile,
            "layers": run.layers,
            "confidence_bundle": run.confidence,
            "results": run.results,
            "run_metadata": run.run_metadata,
            "layer_outputs": [
                {
                    "layer_name": row.layer_name,
                    "output": row.output,
                    "confidence": row.confidence,
                    "provider_name": row.provider_name,
                    "provider_version": row.provider_version,
                    "runtime_ms": row.runtime_ms,
                    "fallback_reason": row.fallback_reason,
                }
                for row in outputs
            ],
        }

    def _build_baseline_outputs(self, text: str, source_metadata: dict[str, Any]) -> tuple[dict[str, Any], dict[str, float]]:
        words = tokenize_words(text)
        sentences = split_sentences(text)
        paragraphs = split_paragraphs(text)
        lower_words = [w.lower() for w in words]
        word_lengths = [len(w) for w in words] or [0]

        entity_candidates = [w for w in words if len(w) > 1 and w[0].isupper()]
        top_entities = [token for token, _ in Counter(entity_candidates).most_common(10)]
        entity_records = [
            {
                "entity_id": hashlib.sha1(entity.encode("utf-8")).hexdigest()[:12],
                "label": entity,
            }
            for entity in top_entities
        ]
        event_candidates = [
            {
                "event_id": hashlib.sha1(token.encode("utf-8")).hexdigest()[:12],
                "trigger": token,
            }
            for token in lower_words
            if token.endswith("ed") or token.endswith("ing")
        ][:10]

        rhetorical = self.rhetorical_analyzer.analyze(text)
        rhetorical_traces = rhetorical.get("explainability", {}).copy()
        rhetorical_traces["linked_spans"] = [
            {"marker": marker, "index": text.lower().find(marker)}
            for marker in ["therefore", "because", "everyone knows", "according"]
            if marker in text.lower()
        ]

        segments = source_metadata.get("segments", {}) if isinstance(source_metadata, dict) else {}
        pdf_hints = {
            "page_count": segments.get("page_count"),
            "heading_candidates": segments.get("heading_candidates", []),
            "citation_markers": segments.get("citation_markers", []),
        }

        outputs: dict[str, Any] = {
            "token": {
                "token_count": len(words),
                "unique_tokens": len(set(lower_words)),
                "top_tokens": [token for token, _ in Counter(lower_words).most_common(20)],
            },
            "morphology": {
                "avg_word_length": round(statistics.mean(word_lengths), 3),
                "long_word_ratio": round(sum(1 for w in words if len(w) >= 8) / max(1, len(words)), 3),
                "suffix_signals": Counter(w[-3:].lower() for w in words if len(w) >= 3).most_common(10),
            },
            "syntax": {
                "sentence_count": len(sentences),
                "avg_sentence_length": round(sum(len(tokenize_words(s)) for s in sentences) / max(1, len(sentences)), 3),
                "clause_markers": {
                    "commas": text.count(","),
                    "semicolons": text.count(";"),
                    "colons": text.count(":"),
                },
            },
            "semantics": {
                "named_entities": entity_records,
                "event_candidates": event_candidates,
                "semantic_density": round(len(set(lower_words)) / max(1, len(words)), 3),
            },
            "pragmatics": {
                "question_count": text.count("?"),
                "exclamation_count": text.count("!"),
                "hedge_count": sum(text.lower().count(h) for h in ["maybe", "perhaps", "likely", "possibly"]),
                "speech_act_hint": "directive" if "should" in lower_words else "assertive",
            },
            "discourse": {
                "paragraph_count": len(paragraphs),
                "connective_count": sum(text.lower().count(c) for c in ["however", "therefore", "because", "although"]),
                "pdf_hints": pdf_hints,
            },
            "sociolinguistics": {
                "contraction_count": sum(text.count(c) for c in ["n't", "'re", "'ll", "'ve"]),
                "formality_score": round(1.0 - (text.count("!") / max(1, len(sentences))), 3),
                "register_hint": "informal" if text.count("!") > 2 else "neutral",
            },
            "rhetoric": {
                **rhetorical,
                "explainability": rhetorical_traces,
            },
            "semiotic": {
                "emoji_count": sum(1 for ch in text if ord(ch) > 10000),
                "glyph_count": sum(1 for ch in text if ch in {"∆", "Æ", "Ω", "☲", "⟁", "Λ", "@"}),
                "symbol_density": round(sum(1 for ch in text if not ch.isalnum() and not ch.isspace()) / max(1, len(text)), 4),
            },
        }
        confidence = {
            "token": 0.72,
            "morphology": 0.68,
            "syntax": 0.66,
            "semantics": 0.64,
            "pragmatics": 0.62,
            "discourse": 0.61,
            "sociolinguistics": 0.59,
            "rhetoric": 0.74,
            "semiotic": 0.63,
        }
        return outputs, confidence
