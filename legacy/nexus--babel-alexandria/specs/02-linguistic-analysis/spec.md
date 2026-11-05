# 02 -- Linguistic Analysis: Specification

> **Domain:** 02-linguistic-analysis
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Source of truth:** `src/nexus_babel/services/analysis.py`, `src/nexus_babel/services/rhetoric.py`, `src/nexus_babel/services/plugins.py`

---

## 1. Overview

The Linguistic Analysis domain provides the 9-layer analysis engine at the heart of Nexus Babel Alexandria. It ingests text from a `Document` or `Branch`, computes baseline heuristic outputs across all nine linguistic layers, runs each layer through a plugin chain with fallback logic, records per-layer provenance (provider, confidence, runtime), and persists the full analysis as an `AnalysisRun` with associated `LayerOutput` records.

The system also provides a standalone rhetorical analysis endpoint with Aristotelian ethos/pathos/logos scoring, fallacy detection, and explainability traces.

The current implementation covers deterministic heuristic analysis. The vision (84 NLP functions from the RLOS design document) extends each layer with ML-backed providers, multimodal processing, cross-layer feedback, and production-grade NLP models (spaCy, Stanza, HuggingFace Transformers).

---

## 2. Architectural Context

### 2.1 Data Flow

```
POST /api/v1/analyze
  |
  v
routes.py: validate auth, enforce mode, check conflict_flag
  |
  v
AnalysisService.analyze()
  |-- resolve text from Document.provenance.extracted_text or Branch.state_snapshot.current_text
  |-- _build_baseline_outputs(text, source_metadata)
  |   |-- tokenize_words(), split_sentences(), split_paragraphs()
  |   |-- RhetoricalAnalyzer.analyze(text) for rhetoric layer
  |   |-- produce 9 baseline output dicts + 9 baseline confidence floats
  |
  |-- for each requested layer:
  |     PluginRegistry.run_layer(layer, modality, text, baseline_output, baseline_confidence, plugin_profile, context)
  |       |-- resolve profile chain: "deterministic" | "ml_first" | "ml_only"
  |       |-- iterate chain, try each plugin: supports() -> run() -> PluginExecution
  |       |-- fallback to next plugin on failure; ultimate fallback = baseline
  |     record LayerOutput(layer_name, output, confidence, provider_name, provider_version, runtime_ms, fallback_reason)
  |
  |-- persist AnalysisRun + all LayerOutput rows
  v
AnalyzeResponse { analysis_run_id, mode, layers, confidence_bundle, hypergraph_ids, plugin_provenance, job_id, status }
```

### 2.2 Key Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `AnalysisService` | `services/analysis.py` | Orchestrates full 9-layer analysis, persists runs |
| `RhetoricalAnalyzer` | `services/rhetoric.py` | Marker-based ethos/pathos/logos scoring + fallacy detection |
| `PluginRegistry` | `services/plugins.py` | Plugin chain management, profile resolution, fallback |
| `DeterministicLayerPlugin` | `services/plugins.py` | Passthrough baseline at baseline confidence |
| `MLStubLayerPlugin` | `services/plugins.py` | Stub ML enrichment (+0.1 confidence), feature-flagged |
| `AnalysisRun` | `models.py` | ORM: run metadata, layers, confidence, results |
| `LayerOutput` | `models.py` | ORM: per-layer output with provider provenance |
| `AnalyzeRequest` / `AnalyzeResponse` | `schemas.py` | Pydantic request/response contracts |
| `RhetoricalAnalysisRequest` / `RhetoricalAnalysisResponse` | `schemas.py` | Standalone rhetoric endpoint contracts |

### 2.3 Execution Modes

| Mode | Behavior |
|------|----------|
| `sync` | Run analysis inline, return full results immediately |
| `async` | Submit as `Job` (type=`"analyze"`), return `job_id` with `status="queued"` |
| `shadow` | Run sync deterministic, also submit async ML job; return sync results with `status="shadow_queued"` |

Shadow execution requires `NEXUS_SHADOW_EXECUTION_ENABLED=true` in settings. Async requires `NEXUS_ASYNC_JOBS_ENABLED=true`.

### 2.4 Governance Integration

- The `/api/v1/analyze` route enforces mode access via `_enforce_mode()` -- RAW mode requires both system-level and per-key `raw_mode_enabled` flags.
- Conflicted documents (`conflict_flag=True`) or non-ingested documents return HTTP 409.
- The rhetoric layer within the analysis pipeline does not itself perform governance filtering; governance is handled separately via `/api/v1/governance/evaluate`.

---

## 3. The Nine Layers

### 3.1 Token Layer

**As-built baseline (`analysis.py:_build_baseline_outputs`):**

| Field | Computation | Type |
|-------|-------------|------|
| `token_count` | `len(tokenize_words(text))` | int |
| `unique_tokens` | `len(set(lower_words))` | int |
| `top_tokens` | `Counter(lower_words).most_common(20)` | list[str] |

**Baseline confidence:** 0.72

**Vision functions (MORPH_001 tokenize):** Language-specific, emoji-aware tokenization using SentencePiece/BPE. Current implementation uses regex `[\w'-]+`.

### 3.2 Morphology Layer

| Field | Computation | Type |
|-------|-------------|------|
| `avg_word_length` | `mean(len(w) for w in words)` | float |
| `long_word_ratio` | count of words >= 8 chars / total words | float |
| `suffix_signals` | `Counter(w[-3:])` top 10 | list[tuple] |

**Baseline confidence:** 0.68

**Vision functions:** MORPH_002 lemmatize, MORPH_003 morphological_parse, MORPH_004 compound_decomposition, MORPH_005 stem_extraction, MORPH_006 inflection_generation, MORPH_007 emoji_normalize, MORPH_008 detect_alliteration, MORPH_009 detect_assonance, MORPH_010 grapheme_safety_check.

### 3.3 Syntax Layer

| Field | Computation | Type |
|-------|-------------|------|
| `sentence_count` | `len(split_sentences(text))` | int |
| `avg_sentence_length` | mean tokens per sentence | float |
| `clause_markers` | counts of `,`, `;`, `:` | dict |

**Baseline confidence:** 0.66

**Vision functions:** SYNT_001 dependency_parse (UD), SYNT_002 pos_tag (UPOS), SYNT_003 constituency_parse, SYNT_004 extract_phrases, SYNT_005 detect_parallelism, SYNT_006 detect_chiasmus, SYNT_007 extract_clauses, SYNT_008 argument_structure, SYNT_009 grammaticality_check, SYNT_010 extract_modifiers, SYNT_011 coordination_resolution, SYNT_012 long_distance_dependency.

### 3.4 Semantics Layer

| Field | Computation | Type |
|-------|-------------|------|
| `named_entities` | Capitalized words hashed to `entity_id` + `label`, top 10 | list[dict] |
| `event_candidates` | Words ending in `-ed`/`-ing`, hashed to `event_id` + `trigger`, max 10 | list[dict] |
| `semantic_density` | unique tokens / total tokens | float |

**Baseline confidence:** 0.64

**Vision functions:** SEM_001 NER (18 types, F1>90%), SEM_002 SRL, SEM_003 sentiment, SEM_004 similarity, SEM_005 intent, SEM_006 WSD, SEM_007 metaphor, SEM_008 frame_semantic, SEM_009 temporal_relations, SEM_010 causal_relations, SEM_011 emotion, SEM_012 semantic_graph (AMR), SEM_013 entity_linking, SEM_014 multimodal_grounding.

### 3.5 Pragmatics Layer

| Field | Computation | Type |
|-------|-------------|------|
| `question_count` | `text.count("?")` | int |
| `exclamation_count` | `text.count("!")` | int |
| `hedge_count` | count of "maybe", "perhaps", "likely", "possibly" | int |
| `speech_act_hint` | "directive" if "should" in words, else "assertive" | str |

**Baseline confidence:** 0.62

**Vision functions:** PRAG_001 speech_act_classification (5 categories), PRAG_002 coreference_resolution, PRAG_003 implicature_detection, PRAG_004 presupposition_identification, PRAG_005 irony_sarcasm_detection, PRAG_006 politeness_analysis, PRAG_007 hedging_detection, PRAG_008 deictic_resolution, PRAG_009 ellipsis_resolution, PRAG_010 question_type_classification, PRAG_011 dialogue_act_tagging.

### 3.6 Discourse Layer

| Field | Computation | Type |
|-------|-------------|------|
| `paragraph_count` | `len(split_paragraphs(text))` | int |
| `connective_count` | count of "however", "therefore", "because", "although" | int |
| `pdf_hints` | page_count, heading_candidates, citation_markers from source_metadata segments | dict |

**Baseline confidence:** 0.61

**Vision functions:** DISC_001 rst_parsing (F1>70%), DISC_002 topic_segmentation, DISC_003 topic_tracking, DISC_004 coherence_evaluation, DISC_005 argumentation_mining, DISC_006 rhetorical_relation_classification (25+ relations), DISC_007 discourse_deixis_resolution, DISC_008 information_structure, DISC_009 discourse_marker_analysis.

### 3.7 Sociolinguistics Layer

| Field | Computation | Type |
|-------|-------------|------|
| `contraction_count` | count of `n't`, `'re`, `'ll`, `'ve` | int |
| `formality_score` | `1.0 - (exclamation_count / sentence_count)` | float |
| `register_hint` | "informal" if `!` count > 2, else "neutral" | str |

**Baseline confidence:** 0.59

**Vision functions:** SOCIO_001 dialect_identification, SOCIO_002 register_classification, SOCIO_003 style_analysis (authorship), SOCIO_004 code_switching_detection, SOCIO_005 politeness_strategy_detection, SOCIO_006 formality_scoring, SOCIO_007 gender_language_analysis, SOCIO_008 cultural_context_retrieval.

### 3.8 Rhetoric Layer

| Field | Computation | Type |
|-------|-------------|------|
| `ethos_score` | marker_count/token_count * 10, capped at 1.0 | float |
| `pathos_score` | marker_count/token_count * 10, capped at 1.0 | float |
| `logos_score` | marker_count/token_count * 10, capped at 1.0 | float |
| `strategies` | ranked non-zero appeal names | list[str] |
| `fallacies` | regex matches for bandwagon, false dilemma, ad hominem | list[str] |
| `explainability` | token_count, marker_counts, linked_spans | dict |

**Markers:**
- Ethos: according, study, evidence, expert, source, citation
- Pathos: fear, love, grief, rage, hope, joy, pain, sacred, mythic
- Logos: therefore, because, hence, thus, if, then, proof, logic

**Fallacy patterns:**
- Bandwagon: `\beveryone knows\b`
- False dilemma: `\beither\b.+\bor\b`
- Ad hominem: `\byou are (stupid|ignorant|worthless)\b`

**Baseline confidence:** 0.74

**Vision functions:** RHET_001 rhetorical_appeal_classification (F1 0.75-0.85), RHET_002 rhetorical_figure_detection (25+ figures), RHET_003 fallacy_detection (10+ types, F1 0.70-0.84), RHET_004 propaganda_technique_detection (18 techniques), RHET_005 persuasive_strategy_identification (Cialdini's 6 principles), RHET_006 argument_quality_assessment.

### 3.9 Semiotic Layer

| Field | Computation | Type |
|-------|-------------|------|
| `emoji_count` | characters with `ord(ch) > 10000` | int |
| `glyph_count` | characters in set `{delta, AE, Omega, trigram, triangle, Lambda, @}` | int |
| `symbol_density` | non-alnum non-space chars / total chars | float |

**Baseline confidence:** 0.63

**Vision functions:** ICONO_001 emoji_sense_disambiguation, ICONO_002 emoji_sentiment_analysis, ICONO_003 hieroglyph_processing, ICONO_004 typography_analysis, ICONO_005 meme_template_recognition, ICONO_006 visual_metaphor_detection. The Peircean triadic engine (representamen/object/interpretant, icon/index/symbol classification, semiotic chains) is described in the vision document.

---

## 4. Plugin Architecture

### 4.1 Plugin Protocol

```python
class LayerPlugin(Protocol):
    name: str
    version: str
    modalities: set[str]

    def healthcheck(self) -> bool: ...
    def supports(self, layer: str, modality: str) -> bool: ...
    def run(self, layer: str, modality: str, text: str,
            baseline_output: dict, context: dict) -> tuple[dict, float]: ...
```

### 4.2 Built-in Plugins

| Plugin | Version | Modalities | Behavior |
|--------|---------|------------|----------|
| `DeterministicLayerPlugin` | v2.0 | text, pdf, image, audio, binary | Passthrough: returns `baseline_output` at `baseline_confidence[layer]` |
| `MLStubLayerPlugin` | v0.1 | text, pdf, image, audio | Adds `provider_note: "ml_stub_enrichment"` to output, adds 0.1 to confidence (capped at 0.95). Requires `plugin_ml_enabled=True` in settings. |

### 4.3 Profile Chains

| Profile | Chain | Use Case |
|---------|-------|----------|
| `"deterministic"` (default) | `[deterministic]` | Fast, reproducible baseline |
| `"ml_first"` | `[ml_stub, deterministic]` | ML preferred with deterministic fallback |
| `"ml_only"` | `[ml_stub]` | ML-only (fails if ML disabled) |

### 4.4 PluginExecution Record

```python
@dataclass
class PluginExecution:
    output: dict[str, Any]
    confidence: float
    provider_name: str
    provider_version: str
    runtime_ms: int
    fallback_reason: str | None = None
```

Each execution records the winning provider, its version, wall-clock runtime in milliseconds, and any fallback reasons accumulated during chain traversal. This data is persisted per-layer in the `LayerOutput` table and surfaced via `plugin_provenance` in the API response.

### 4.5 Failure Handling

When a plugin fails (raises an exception), the registry logs `"{plugin_name}:{exc}"` as a fallback reason and continues to the next plugin in the chain. If all plugins fail, the registry returns a synthetic `PluginExecution` with `baseline_output`, `confidence=0.0` (from `baseline_confidence.get(layer, 0.0)`), `provider_name="deterministic"`, and `fallback_reason="all_plugins_failed"`.

---

## 5. API Contract

### 5.1 POST /api/v1/analyze

**Auth:** operator (minimum role)
**Request:** `AnalyzeRequest`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `document_id` | str or null | null | Target document (mutually exclusive with branch_id) |
| `branch_id` | str or null | null | Target branch |
| `layers` | list[str] | [] (all 9) | Subset of layers to run |
| `mode` | "PUBLIC" or "RAW" | "PUBLIC" | Governance mode |
| `execution_mode` | "sync" / "async" / "shadow" | "sync" | How to execute |
| `plugin_profile` | str or null | null | Plugin chain profile |

**Response:** `AnalyzeResponse`

| Field | Type | Description |
|-------|------|-------------|
| `analysis_run_id` | str or null | Run ID (null for async) |
| `mode` | str | Effective mode |
| `layers` | dict[str, Any] | Layer name -> output dict |
| `confidence_bundle` | dict[str, float] | Layer name -> confidence |
| `hypergraph_ids` | dict | Graph projection IDs |
| `plugin_provenance` | dict | Per-layer provider info |
| `job_id` | str or null | Job ID (async/shadow) |
| `status` | str | "completed", "queued", "shadow_queued" |

**Error codes:**
- 400: Missing document_id and branch_id; document not found
- 401: Missing or invalid API key
- 403: Insufficient role or mode not allowed
- 409: Document is conflicted or not ingested

### 5.2 GET /api/v1/analysis/runs/{run_id}

**Auth:** viewer
**Response:** `AnalysisRunResponse` including `layer_outputs` array with full per-layer provenance.

### 5.3 GET /api/v1/analysis/runs

**Auth:** viewer
**Query:** `limit` (1-1000, default 100)
**Response:** Summary list of runs (id, document_id, branch_id, mode, execution_mode, plugin_profile, created_at).

### 5.4 POST /api/v1/rhetorical_analysis

**Auth:** operator
**Request:** `RhetoricalAnalysisRequest`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | str or null | null | Direct text input |
| `document_id` | str or null | null | Resolve text from document |
| `audience_profile` | dict | {} | Audience context (unused in current impl) |

**Response:** `RhetoricalAnalysisResponse`

| Field | Type | Description |
|-------|------|-------------|
| `ethos_score` | float | 0.0-1.0 |
| `pathos_score` | float | 0.0-1.0 |
| `logos_score` | float | 0.0-1.0 |
| `strategies` | list[str] | Ranked non-zero appeal names |
| `fallacies` | list[str] | Detected fallacy types |
| `explainability` | dict | token_count, marker_counts |

---

## 6. Data Model

### 6.1 AnalysisRun

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID str | Primary key |
| `document_id` | FK -> documents.id | Nullable |
| `branch_id` | FK -> branches.id | Nullable |
| `mode` | str(16) | "PUBLIC" or "RAW" |
| `execution_mode` | str(16) | "sync", "async", "shadow" |
| `plugin_profile` | str(64) | Nullable; e.g. "deterministic", "ml_first" |
| `job_id` | FK -> jobs.id | Nullable; links to async Job |
| `layers` | JSON list | Layer names that were run |
| `confidence` | JSON dict | Layer -> confidence float |
| `results` | JSON dict | Layer -> output dict |
| `run_metadata` | JSON dict | plugin_provenance, source_modality, plugin_health |
| `created_at` | datetime(tz) | Timestamp |

### 6.2 LayerOutput

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID str | Primary key |
| `analysis_run_id` | FK -> analysis_runs.id | Parent run |
| `layer_name` | str(64) | e.g. "token", "rhetoric" |
| `output` | JSON dict | Full layer output |
| `confidence` | float | Provider confidence |
| `provider_name` | str(64) | e.g. "deterministic", "ml_stub" |
| `provider_version` | str(32) | e.g. "v2.0" |
| `runtime_ms` | int | Wall-clock execution time |
| `fallback_reason` | str(256) | Nullable; accumulated fallback reasons |
| `created_at` | datetime(tz) | Timestamp |

---

## 7. Functional Requirements

### Story S02-01: Baseline 9-Layer Analysis (P1 -- as-built)

- **FR-01** (MUST): The system MUST resolve text from either `Document.provenance.extracted_text` (by `document_id`) or `Branch.state_snapshot.current_text` (by `branch_id`). Exactly one MUST be provided.
- **FR-02** (MUST): When no `layers` list is provided, the system MUST analyze all 9 layers: token, morphology, syntax, semantics, pragmatics, discourse, sociolinguistics, rhetoric, semiotic.
- **FR-03** (MUST): Each layer MUST produce a structured output dict as defined in Section 3 and a baseline confidence value.
- **FR-04** (MUST): The analysis MUST be persisted as an `AnalysisRun` row with associated `LayerOutput` rows (one per requested layer).
- **FR-05** (MUST): Each `LayerOutput` MUST record `provider_name`, `provider_version`, `runtime_ms`, and `fallback_reason`.
- **FR-06** (SHOULD): The token layer SHOULD return the top-20 most common lowercased tokens.
- **FR-07** (SHOULD): The semantics layer SHOULD cap named_entities and event_candidates at 10 entries each.
- **FR-08** (MAY): Layers MAY be requested individually or in any subset.

### Story S02-02: Plugin Chain & Provider Provenance (P1 -- as-built)

- **FR-09** (MUST): The `PluginRegistry` MUST support at minimum the `DeterministicLayerPlugin`.
- **FR-10** (MUST): Plugin profile chains MUST be resolved as: `"deterministic"` -> `[deterministic]`, `"ml_first"` -> `[ml_stub, deterministic]`, `"ml_only"` -> `[ml_stub]`.
- **FR-11** (MUST): If a plugin's `supports()` returns false or `run()` raises an exception, the registry MUST fall through to the next plugin in the chain and record a fallback reason.
- **FR-12** (MUST): If all plugins fail, the registry MUST return baseline output with confidence from `baseline_confidence.get(layer, 0.0)` and `fallback_reason="all_plugins_failed"`.
- **FR-13** (MUST): `PluginExecution` MUST track wall-clock `runtime_ms` via `time.perf_counter()`.
- **FR-14** (SHOULD): The `MLStubLayerPlugin` SHOULD add 0.1 to baseline confidence (capped at 0.95) and enrich output with `provider_note`.
- **FR-15** (SHOULD): The `PluginRegistry.health()` SHOULD return a dict of plugin name -> healthcheck boolean.
- **FR-16** (MAY): Custom plugin profiles MAY be added in future versions.

### Story S02-03: Rhetorical Analysis (P1 -- as-built)

- **FR-17** (MUST): `RhetoricalAnalyzer.analyze()` MUST compute ethos/pathos/logos scores as `marker_count / token_count * 10`, each capped at 1.0.
- **FR-18** (MUST): The analyzer MUST detect fallacies using the 3 defined regex patterns (bandwagon, false dilemma, ad hominem).
- **FR-19** (MUST): The response MUST include `strategies` (ranked non-zero appeals) and `explainability` (token_count, marker_counts).
- **FR-20** (MUST): The standalone `/api/v1/rhetorical_analysis` endpoint MUST resolve text from either `text` field or `document_id`.
- **FR-21** (SHOULD): For empty text (no tokens), the analyzer SHOULD return all-zero scores with empty strategies/fallacies.
- **FR-22** (MAY): The `audience_profile` field MAY be used in future versions for audience-adaptive scoring.

### Story S02-04: Execution Modes (P1 -- as-built)

- **FR-23** (MUST): `sync` mode MUST execute analysis inline and return full results.
- **FR-24** (MUST): `async` mode MUST submit a `Job` with `job_type="analyze"` and return `job_id` with `status="queued"`.
- **FR-25** (MUST): `async` mode MUST be gated by `NEXUS_ASYNC_JOBS_ENABLED` setting.
- **FR-26** (MUST): `shadow` mode MUST execute sync analysis AND submit an async ML job when `NEXUS_SHADOW_EXECUTION_ENABLED=true`.
- **FR-27** (MUST): Shadow mode MUST default the async job's `plugin_profile` to `"ml_first"` when the original request has no explicit profile.
- **FR-28** (SHOULD): Shadow results SHOULD return `status="shadow_queued"` with both `analysis_run_id` and `job_id`.

### Story S02-05: Analysis Run Retrieval (P1 -- as-built)

- **FR-29** (MUST): `GET /api/v1/analysis/runs/{run_id}` MUST return the full run detail including all `layer_outputs`.
- **FR-30** (MUST): `GET /api/v1/analysis/runs` MUST return a paginated list ordered by `created_at DESC`.
- **FR-31** (MUST): Each `layer_output` entry MUST include `layer_name`, `output`, `confidence`, `provider_name`, `provider_version`, `runtime_ms`, `fallback_reason`.

### Story S02-06: Conflict & Mode Enforcement (P1 -- as-built)

- **FR-32** (MUST): Analysis MUST be blocked with HTTP 409 if the target document has `conflict_flag=True` or `ingested=False`.
- **FR-33** (MUST): RAW mode access MUST require both system-level `raw_mode_enabled` and per-key `raw_mode_enabled` flags.
- **FR-34** (MUST): Insufficient role or mode access MUST return HTTP 403.

### Story S02-07: ML Plugin Integration (P2 -- partially built)

- **FR-35** (MUST): The `MLStubLayerPlugin` MUST be gated by `NEXUS_PLUGIN_ML_ENABLED` setting.
- **FR-36** (SHOULD): ML plugins SHOULD produce enriched outputs that are a superset of baseline outputs.
- **FR-37** (SHOULD): When ML is disabled, `healthcheck()` SHOULD return `False` and `supports()` SHOULD return `False`.
- **FR-38** (MAY): Future ML plugins MAY integrate spaCy, Stanza, or HuggingFace Transformers.

### Story S02-08: Phonology Layer (P3 -- vision)

- **FR-39** (SHOULD): The system SHOULD implement PHON_001 speech_to_text using Whisper-based transcription for audio modality.
- **FR-40** (SHOULD): The system SHOULD implement PHON_002 extract_prosody (F0, intensity, duration, rhythm).
- **FR-41** (MAY): The system MAY implement PHON_003-008 (intonation, stress, tone, alignment, VAD, diarization).

### Story S02-09: Advanced Morphology (P3 -- vision)

- **FR-42** (SHOULD): The system SHOULD implement MORPH_002 lemmatize and MORPH_003 morphological_parse.
- **FR-43** (SHOULD): The system SHOULD implement MORPH_008 detect_alliteration and MORPH_009 detect_assonance for literary analysis.
- **FR-44** (MAY): The system MAY implement MORPH_004 compound_decomposition, MORPH_005 stem_extraction, MORPH_006 inflection_generation, MORPH_007 emoji_normalize, MORPH_010 grapheme_safety_check.

### Story S02-10: Advanced Syntax (P3 -- vision)

- **FR-45** (SHOULD): The system SHOULD implement SYNT_001 dependency_parse (Universal Dependencies) and SYNT_002 pos_tag (UPOS).
- **FR-46** (SHOULD): The system SHOULD implement SYNT_005 detect_parallelism and SYNT_006 detect_chiasmus for rhetorical figure detection.
- **FR-47** (MAY): The system MAY implement SYNT_003-004, SYNT_007-012.

### Story S02-11: Advanced Semantics (P3 -- vision)

- **FR-48** (MUST): The system MUST replace capitalized-word NER heuristic with proper NER (SEM_001, 18 fine-grained types, F1>90%).
- **FR-49** (SHOULD): The system SHOULD implement SEM_002 SRL, SEM_003 sentiment (polarity + VAD), SEM_007 metaphor_detection.
- **FR-50** (SHOULD): The system SHOULD implement SEM_012 semantic_graph_construction (AMR parsing, Smatch>84%).
- **FR-51** (MAY): The system MAY implement SEM_004-006, SEM_008-011, SEM_013-014.

### Story S02-12: Advanced Pragmatics (P3 -- vision)

- **FR-52** (SHOULD): The system SHOULD implement PRAG_001 speech_act_classification (5 categories) replacing the current single-heuristic "should"->"directive".
- **FR-53** (SHOULD): The system SHOULD implement PRAG_002 coreference_resolution and PRAG_005 irony_sarcasm_detection.
- **FR-54** (MAY): The system MAY implement PRAG_003-004, PRAG_006-011.

### Story S02-13: Advanced Discourse (P3 -- vision)

- **FR-55** (SHOULD): The system SHOULD implement DISC_001 rst_parsing (enhanced RST with graph structure, F1>70%).
- **FR-56** (SHOULD): The system SHOULD implement DISC_005 argumentation_mining (premise-claim-rebuttal).
- **FR-57** (MAY): The system MAY implement DISC_002-004, DISC_006-009.

### Story S02-14: Advanced Sociolinguistics (P3 -- vision)

- **FR-58** (SHOULD): The system SHOULD implement SOCIO_002 register_classification (formal/informal/technical/literary) and SOCIO_006 formality_scoring.
- **FR-59** (MAY): The system MAY implement SOCIO_001, SOCIO_003-005, SOCIO_007-008.

### Story S02-15: Advanced Rhetoric (P3 -- vision)

- **FR-60** (SHOULD): The system SHOULD implement RHET_002 rhetorical_figure_detection (25+ figures).
- **FR-61** (SHOULD): The system SHOULD expand RHET_003 fallacy_detection to 10+ fallacy types (F1 0.70-0.84).
- **FR-62** (SHOULD): The system SHOULD implement RHET_004 propaganda_technique_detection (18 techniques).
- **FR-63** (MAY): The system MAY implement RHET_005 persuasive_strategy_identification and RHET_006 argument_quality_assessment.

### Story S02-16: Semiotic Engine (P3 -- vision)

- **FR-64** (SHOULD): The system SHOULD implement the Peircean triadic engine (representamen, object, interpretant classification).
- **FR-65** (SHOULD): The system SHOULD implement icon/index/symbol classification using CLIP embeddings and cultural symbol lexicon.
- **FR-66** (MAY): The system MAY implement semiotic chains (unlimited semiosis), denotation/connotation analysis, and the full ICONO_001-006 functions.

### Story S02-17: Cross-Layer Feedback (P4 -- vision)

- **FR-67** (SHOULD): The analysis engine SHOULD support bidirectional information flow between layers (upward, downward, lateral, recursive) through the unified hypergraph.
- **FR-68** (MAY): Layers MAY subscribe to outputs of other layers for iterative refinement.
- **FR-69** (MAY): The system MAY implement a feedback convergence loop with configurable max iterations.

### Story S02-18: Multimodal Analysis (P4 -- vision)

- **FR-70** (SHOULD): The analysis engine SHOULD process audio modality documents through the phonology layer.
- **FR-71** (SHOULD): The analysis engine SHOULD process image modality documents through the semiotic and iconographic layers.
- **FR-72** (MAY): The system MAY support video and gesture modalities via cross-modal attention (Multimodal Bottleneck Transformers).

---

## 8. Non-Functional Requirements

- **NFR-01** (MUST): Sync analysis of a single document (all 9 layers, deterministic profile) MUST complete in under 500ms for documents under 100KB.
- **NFR-02** (MUST): All `PluginExecution` records MUST include accurate `runtime_ms` measurements.
- **NFR-03** (SHOULD): The plugin chain SHOULD gracefully degrade -- a failing plugin SHOULD NOT crash the analysis run.
- **NFR-04** (SHOULD): The system SHOULD log plugin failures with sufficient context for debugging.
- **NFR-05** (MAY): Analysis results MAY be cached for identical (document_id, layers, mode, plugin_profile) tuples.

---

## 9. Constraints & Assumptions

- The current baseline relies entirely on regex and string operations. No NLP library dependencies yet.
- `RhetoricalAnalyzer` tokenizes independently from `tokenize_words()` (uses `re.findall(r"[\w'-]+", text.lower())` vs. the `WORD_PATTERN` regex in `text_utils.py`). These are functionally equivalent but represent separate code paths.
- The `MLStubLayerPlugin` is a placeholder. It does not perform real ML inference -- it adds a fixed 0.1 confidence boost and a `provider_note` annotation.
- Shadow execution creates a second analysis run via the async job queue. The two runs are not explicitly linked beyond the shared `document_id`/`branch_id`.
- The rhetoric layer in the analysis pipeline calls `RhetoricalAnalyzer.analyze()` inline. The standalone `/api/v1/rhetorical_analysis` endpoint calls the same analyzer but bypasses the plugin chain.
- The `audience_profile` field in `RhetoricalAnalysisRequest` is accepted but not used in the current implementation.
