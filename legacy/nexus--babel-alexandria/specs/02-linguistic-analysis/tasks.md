# 02 -- Linguistic Analysis: Tasks

> **Domain:** 02-linguistic-analysis
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Plan reference:** `specs/02-linguistic-analysis/plan.md`

---

## Legend

- `[P]` = Can be parallelized with other `[P]` tasks in the same story
- `[S]` = Sequential; depends on prior task completion
- `[Story X]` = Story dependency (must complete before this task starts)

---

## P1: As-Built Hardening

### S02-01: Baseline 9-Layer Analysis

- [ ] **T01-01** [P] Create `tests/test_analysis.py` with test fixture that creates an `AnalysisService` instance backed by an isolated SQLite database and a sample `Document` with known `extracted_text` in provenance.
  - File: `tests/test_analysis.py`
  - AC: Fixture yields `(client, analysis_service, session, doc_id, auth_headers)`.

- [ ] **T01-02** [P] Write parametrized unit test `test_baseline_layer_outputs` that runs `AnalysisService.analyze()` on a fixed 200-word English text and asserts exact output schema for each of the 9 layers.
  - File: `tests/test_analysis.py`
  - AC: For each layer, assert all expected keys present, correct types (int, float, list, dict), and confidence matches the defined baseline (token=0.72, morphology=0.68, ... semiotic=0.63). <!-- allow-secret -->

- [ ] **T01-03** [P] Write test `test_empty_text_analysis` that analyzes a document with empty `extracted_text` and verifies no crash, all layers return valid (potentially zero) outputs.
  - File: `tests/test_analysis.py`
  - AC: `token_count=0`, `unique_tokens=0`, `sentence_count=0`, all scores/counts are 0 or valid defaults. No exceptions raised.

- [ ] **T01-04** [P] Write test `test_layer_subset_selection` that requests only `["token", "rhetoric"]` layers and verifies only those 2 layers appear in `AnalysisRun.layers`, `results`, `confidence`, and only 2 `LayerOutput` rows are created.
  - File: `tests/test_analysis.py`
  - AC: `len(run.layers) == 2`, `set(run.results.keys()) == {"token", "rhetoric"}`, DB query for LayerOutput returns exactly 2 rows.

- [ ] **T01-05** [P] Write test `test_branch_text_resolution` that creates a `Branch` with known `state_snapshot.current_text`, runs analysis by `branch_id`, and verifies the text was resolved correctly.
  - File: `tests/test_analysis.py`
  - AC: Token count matches expected count from the branch text, not from any document.

- [ ] **T01-06** [S] Write test `test_analysis_missing_source` that calls `analyze()` with neither `document_id` nor `branch_id` and verifies `ValueError` is raised with expected message.
  - File: `tests/test_analysis.py`
  - AC: `pytest.raises(ValueError, match="Either document_id or branch_id")`.

- [ ] **T01-07** [P] Write benchmark test `test_analysis_performance_100kb` that generates a ~100KB text document, runs sync analysis (all 9 layers, deterministic), and asserts completion under 500ms.
  - File: `tests/test_analysis.py`
  - AC: `assert elapsed_ms < 500`. Mark with `@pytest.mark.slow`.

### S02-02: Plugin Chain & Provider Provenance

- [ ] **T02-01** [P] Create `tests/test_plugins.py` with isolated `PluginRegistry` tests (no DB needed).
  - File: `tests/test_plugins.py`
  - AC: File created with imports and base fixtures.

- [ ] **T02-02** [P] Write test `test_profile_chain_resolution` that verifies `_profile_chain()` returns correct chains for `"deterministic"`, `"ml_first"`, `"ml_only"`, `None`, `"unknown_profile"`, and `"  ML_FIRST  "` (whitespace/case).
  - File: `tests/test_plugins.py`
  - AC: Assert exact chain lists. `None` and `"unknown_profile"` both resolve to `["deterministic"]`. `"  ML_FIRST  "` resolves to `["ml_stub", "deterministic"]`.

- [ ] **T02-03** [P] Write test `test_deterministic_passthrough` that runs `DeterministicLayerPlugin.run()` with known baseline_output and verifies output is unchanged and confidence matches baseline.
  - File: `tests/test_plugins.py`
  - AC: `output == baseline_output`, `confidence == baseline_confidence["token"]`.

- [ ] **T02-04** [P] Write test `test_ml_stub_enrichment` that runs `MLStubLayerPlugin.run()` with `enabled=True` and verifies output has `provider_note` key and confidence is `baseline + 0.1` (capped at 0.95).
  - File: `tests/test_plugins.py`
  - AC: `"provider_note" in output`, `confidence == min(0.95, baseline_conf + 0.1)`.

- [ ] **T02-05** [P] Write test `test_ml_stub_disabled` that verifies `MLStubLayerPlugin(enabled=False)` returns `healthcheck()=False`, `supports()=False`.
  - File: `tests/test_plugins.py`
  - AC: Both methods return False. `.run()` raises `RuntimeError`.

- [ ] **T02-06** [P] Write test `test_fallback_on_plugin_failure` that creates a custom mock plugin raising `RuntimeError`, puts it first in chain with deterministic second, and verifies fallback to deterministic with correct `fallback_reason`.
  - File: `tests/test_plugins.py`
  - AC: `execution.provider_name == "deterministic"`, `"mock_plugin:RuntimeError" in execution.fallback_reason`.

- [ ] **T02-07** [P] Write test `test_all_plugins_failed` that uses `ml_only` profile with ML disabled and verifies terminal fallback with `fallback_reason` containing `"all_plugins_failed"` or `"plugin_unsupported"`.
  - File: `tests/test_plugins.py`
  - AC: `execution.confidence == baseline_confidence.get(layer, 0.0)`, `execution.provider_name == "deterministic"`, fallback_reason is non-None.

- [ ] **T02-08** [P] Write test `test_runtime_measurement` that runs a plugin and verifies `runtime_ms >= 0` (integer).
  - File: `tests/test_plugins.py`
  - AC: `isinstance(execution.runtime_ms, int)`, `execution.runtime_ms >= 0`.

- [ ] **T02-09** [P] Write test `test_plugin_health` that verifies `registry.health()` returns `{"deterministic": True, "ml_stub": False}` when ML is disabled, and `{"deterministic": True, "ml_stub": True}` when ML is enabled.
  - File: `tests/test_plugins.py`
  - AC: Exact dict match for both configurations.

### S02-03: Rhetorical Analysis

- [ ] **T03-01** [P] Create `tests/test_rhetoric.py` with `RhetoricalAnalyzer` unit tests.
  - File: `tests/test_rhetoric.py`
  - AC: File created with imports and `RhetoricalAnalyzer()` fixture.

- [ ] **T03-02** [P] Write test `test_ethos_scoring_precision` with text containing exactly 2 ethos markers in 20 tokens. Expected: `ethos_score = round(min(1.0, 2/20 * 10), 4) = 1.0`.
  - File: `tests/test_rhetoric.py`
  - AC: Assert exact `ethos_score` value. Test with 1 marker in 100 tokens for sub-1.0 score: `round(min(1.0, 1/100 * 10), 4) = 0.1`.

- [ ] **T03-03** [P] Write test `test_pathos_scoring` with text containing pathos markers "fear" and "love" among neutral words.
  - File: `tests/test_rhetoric.py`
  - AC: `pathos_score > 0`, `"pathos" in strategies`.

- [ ] **T03-04** [P] Write test `test_logos_scoring` with text containing logos markers "therefore" and "because".
  - File: `tests/test_rhetoric.py`
  - AC: `logos_score > 0`, `"logos" in strategies`.

- [ ] **T03-05** [P] Write parametrized test `test_fallacy_detection` for each of the 3 fallacy patterns:
  - Bandwagon: "Everyone knows this is true" -> `["bandwagon"]`
  - False dilemma: "Either you agree or you are wrong" -> `["false dilemma"]`
  - Ad hominem: "You are stupid for thinking that" -> `["ad hominem"]`
  - File: `tests/test_rhetoric.py`
  - AC: Each input text produces exactly the expected fallacy in the `fallacies` list.

- [ ] **T03-06** [P] Write test `test_rhetoric_empty_text` verifying zero scores, empty strategies/fallacies, token_count=0 for `""` and `"   "`.
  - File: `tests/test_rhetoric.py`
  - AC: All scores 0.0, strategies=[], fallacies=[], explainability.token_count=0.

- [ ] **T03-07** [P] Write test `test_strategy_ranking` with text containing more pathos markers than logos markers and no ethos markers.
  - File: `tests/test_rhetoric.py`
  - AC: `strategies[0] == "pathos"`, `strategies[1] == "logos"`, `"ethos" not in strategies`.

- [ ] **T03-08** [P] Write integration test `test_rhetorical_endpoint_with_document_id` via TestClient that creates a document, then calls `/api/v1/rhetorical_analysis` with `document_id` instead of `text`.
  - File: `tests/test_rhetoric.py`
  - AC: Response 200, scores are non-negative floats, strategies is a list.

### S02-04: Execution Modes

- [ ] **T04-01** [P] [Story S02-01] Write test `test_sync_mode_returns_full_results` that posts to `/api/v1/analyze` with `execution_mode="sync"` and verifies `status="completed"`, `analysis_run_id` is not null, `layers` dict is populated.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 200`, all fields non-null/non-empty as expected.

- [ ] **T04-02** [P] [Story S02-01] Write test `test_async_mode_returns_job_id` that posts with `execution_mode="async"` and verifies `analysis_run_id=None`, `job_id` is not null, `status="queued"`.
  - File: `tests/test_analysis.py`
  - AC: Job exists in DB with `job_type="analyze"`.

- [ ] **T04-03** [P] Write test `test_async_mode_disabled_returns_400` with settings override `async_jobs_enabled=False`.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 400`, detail mentions "disabled".

- [ ] **T04-04** [P] Write test `test_shadow_mode_creates_both` with settings override `shadow_execution_enabled=True` and `async_jobs_enabled=True`. Post with `execution_mode="shadow"`.
  - File: `tests/test_analysis.py`
  - AC: `analysis_run_id` is not null (sync result), `job_id` is not null (shadow job), `status="shadow_queued"`. Shadow job payload has `plugin_profile="ml_first"`.

- [ ] **T04-05** [P] Write test `test_shadow_mode_disabled_no_job` with `shadow_execution_enabled=False`. Post with `execution_mode="shadow"`.
  - File: `tests/test_analysis.py`
  - AC: `analysis_run_id` is not null, `job_id` is null, `status="completed"`.

### S02-05: Analysis Run Retrieval

- [ ] **T05-01** [S] [Story S02-01] Write test `test_get_run_detail` that creates a sync analysis, then GETs the run by ID and verifies full `AnalysisRunResponse` shape including `layer_outputs` array.
  - File: `tests/test_analysis.py`
  - AC: Response has `analysis_run_id`, `mode`, `execution_mode`, `layer_outputs` with correct count.

- [ ] **T05-02** [P] Write test `test_get_run_not_found` that GETs a nonexistent run ID and verifies 404.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 404`.

- [ ] **T05-03** [P] Write test `test_list_runs_pagination` that creates 3 analysis runs, then lists with `limit=2` and verifies only 2 returned, ordered by `created_at DESC`.
  - File: `tests/test_analysis.py`
  - AC: `len(resp.json()["runs"]) == 2`, first run is the most recent.

- [ ] **T05-04** [P] Write test `test_layer_output_provenance_fields` that verifies each `layer_output` in a run detail response contains `layer_name`, `output`, `confidence`, `provider_name`, `provider_version`, `runtime_ms`, `fallback_reason`.
  - File: `tests/test_analysis.py`
  - AC: All 7 fields present in each layer output. `provider_name == "deterministic"`, `provider_version == "v2.0"`.

### S02-06: Conflict & Mode Enforcement

- [ ] **T06-01** [P] Write test `test_analyze_non_ingested_document_409` that creates a Document with `ingested=False`, `conflict_flag=False` and verifies 409 on analyze.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 409`, detail mentions "conflicted or non-ingestable".

- [ ] **T06-02** [P] Write test `test_analyze_raw_mode_system_disabled` with settings `raw_mode_enabled=False`. Post with `mode="RAW"` using researcher key.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 403`, detail mentions role/mode.

- [ ] **T06-03** [P] Write test `test_analyze_raw_mode_key_disabled` with system `raw_mode_enabled=True` but per-key `raw_mode_enabled=False`. Post with `mode="RAW"`.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 403`.

- [ ] **T06-04** [P] Write test `test_analyze_viewer_role_forbidden` that uses viewer key to POST analyze.
  - File: `tests/test_analysis.py`
  - AC: `resp.status_code == 403`, detail mentions "viewer" role.

---

## P2: ML Plugin Promotion

### S02-07: ML Plugin Integration

- [ ] **T07-01** [P] Add `nlp` optional dependency group to `pyproject.toml`: `spacy>=3.7`, `en-core-web-sm` (via spaCy download or pip URL).
  - File: `pyproject.toml`
  - AC: `pip install -e ".[nlp]"` succeeds, `import spacy; spacy.load("en_core_web_sm")` works.

- [ ] **T07-02** [S] [Story T07-01] Create `src/nexus_babel/services/plugins_spacy.py` with `SpacyLayerPlugin` class implementing the `LayerPlugin` protocol.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Class has `name="spacy"`, `version="v1.0"`, `modalities={"text", "pdf"}`. `healthcheck()` returns True if model loaded. `supports()` returns True for layers: token, morphology, syntax, semantics.

- [ ] **T07-03** [S] [Story T07-02] Implement `SpacyLayerPlugin.run()` for `layer="token"`: return `{token_count, unique_tokens, top_tokens, pos_distribution}` using spaCy tokenization.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Output includes POS distribution. Confidence >= 0.85.

- [ ] **T07-04** [S] [Story T07-02] Implement `SpacyLayerPlugin.run()` for `layer="morphology"`: return `{avg_word_length, long_word_ratio, suffix_signals, lemmas, morphological_features}` using spaCy.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Output includes lemmatized tokens. Confidence >= 0.80.

- [ ] **T07-05** [S] [Story T07-02] Implement `SpacyLayerPlugin.run()` for `layer="syntax"`: return `{sentence_count, avg_sentence_length, clause_markers, dependency_tree, pos_tags}` using spaCy dependency parser.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: `dependency_tree` is a list of `{token, dep, head, pos}` dicts. Confidence >= 0.82.

- [ ] **T07-06** [S] [Story T07-02] Implement `SpacyLayerPlugin.run()` for `layer="semantics"`: return `{named_entities, event_candidates, semantic_density}` using spaCy NER.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: `named_entities` includes entity type labels (PER, ORG, LOC, etc.). Confidence >= 0.78.

- [ ] **T07-07** [S] [Story T07-06] Register `SpacyLayerPlugin` in `PluginRegistry.__init__()` and add `"spacy_first"` profile chain: `[spacy, deterministic]`.
  - File: `src/nexus_babel/services/plugins.py`
  - AC: `registry._profile_chain("spacy_first") == ["spacy", "deterministic"]`. Plugin only registered when spacy is importable.

- [ ] **T07-08** [P] Add `NEXUS_SPACY_MODEL` setting (default `"en_core_web_sm"`) and `NEXUS_NLP_EXTRA_ENABLED` flag (default `False`) to config.
  - File: `src/nexus_babel/config.py`
  - AC: Settings loaded from env. When `nlp_extra_enabled=False`, spaCy plugin is not registered.

- [ ] **T07-09** [S] [Story T07-07] Create `tests/test_plugins_spacy.py` with tests for each of the 4 supported layers, guarded by `@pytest.mark.skipif(not HAS_SPACY, ...)`.
  - File: `tests/test_plugins_spacy.py`
  - AC: All 4 layer tests pass when spaCy is installed. Tests are skipped cleanly when spaCy is absent.

---

## P3: Vision NLP Functions

### S02-08: Phonology Layer

- [ ] **T08-01** [P] Research and select Whisper integration approach: `openai-whisper` vs `faster-whisper` vs HuggingFace `transformers` pipeline. Document decision in `docs/adr/`.
  - AC: ADR written with performance/memory/license comparison.

- [ ] **T08-02** [S] [Story T08-01] Create `src/nexus_babel/services/plugins_phonology.py` with `WhisperPhonologyPlugin` implementing PHON_001 (speech_to_text).
  - File: `src/nexus_babel/services/plugins_phonology.py`
  - AC: For audio modality, returns `{transcription, language, segments, word_timestamps}`.

- [ ] **T08-03** [S] [Story T08-02] Implement PHON_002 extract_prosody using `parselmouth` (Praat wrapper).
  - File: `src/nexus_babel/services/plugins_phonology.py`
  - AC: Returns `{pitch_contour, intensity_contour, speaking_rate, pause_positions}`.

- [ ] **T08-04** [S] Write tests for phonology plugin with a small test WAV file.
  - File: `tests/test_plugins_phonology.py`
  - AC: Transcription test passes. Mark with `@pytest.mark.slow` and `@pytest.mark.nlp`.

### S02-09: Advanced Morphology

- [ ] **T09-01** [P] [Story S02-07] Extend `SpacyLayerPlugin` morphology output with full lemma list and morphological feature dicts per token.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Output includes `{lemmas: [{token, lemma, morph_features}], ...}`.

- [ ] **T09-02** [P] Implement `detect_alliteration()` function: scan consecutive words for shared initial consonant clusters, return spans.
  - File: `src/nexus_babel/services/analysis_literary.py` (new)
  - AC: `detect_alliteration("Peter Piper picked a peck")` returns alliteration spans.

- [ ] **T09-03** [P] Implement `detect_assonance()` function: scan words for repeated internal vowel patterns.
  - File: `src/nexus_babel/services/analysis_literary.py`
  - AC: `detect_assonance("The rain in Spain stays mainly in the plain")` detects "ai" pattern.

- [ ] **T09-04** [S] Integrate literary analysis functions into morphology layer plugin output.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Morphology output includes `alliteration_spans` and `assonance_spans`.

### S02-10: Advanced Syntax

- [ ] **T10-01** [P] [Story S02-07] Ensure spaCy syntax layer outputs full dependency tree with UD relations.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Output `dependency_tree` uses Universal Dependencies relation labels.

- [ ] **T10-02** [P] Implement `detect_parallelism()`: compare POS tag sequences across sibling clauses for structural repetition.
  - File: `src/nexus_babel/services/analysis_literary.py`
  - AC: Detects parallel structures like "I came, I saw, I conquered".

- [ ] **T10-03** [P] Implement `detect_chiasmus()`: detect A-B-B-A patterns in POS or lexical sequences.
  - File: `src/nexus_babel/services/analysis_literary.py`
  - AC: Detects "Ask not what your country can do for you, ask what you can do for your country".

- [ ] **T10-04** [S] Integrate parallelism and chiasmus detection into syntax layer plugin output.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: Syntax output includes `parallel_structures` and `chiasmus_candidates`.

### S02-11: Advanced Semantics

- [ ] **T11-01** [P] [Story S02-07] Replace capitalized-word NER heuristic with spaCy NER in semantics layer. Map spaCy entity types to 18 fine-grained types.
  - File: `src/nexus_babel/services/plugins_spacy.py`
  - AC: `named_entities` use typed labels (PERSON, ORG, GPE, DATE, etc.) instead of heuristic `entity_id` hashes.

- [ ] **T11-02** [P] Research SRL integration options: AllenNLP vs HuggingFace SRL pipeline. Document decision.
  - AC: Decision documented with performance/accuracy/dependency tradeoffs.

- [ ] **T11-03** [S] [Story T11-02] Implement SEM_002 SRL as a plugin extension to the semantics layer.
  - File: `src/nexus_babel/services/plugins_srl.py` (new) or extend spaCy plugin
  - AC: Returns `{predicates: [{predicate, arguments: [{role, text, span}]}]}`.

- [ ] **T11-04** [P] Implement SEM_003 sentiment analysis using a HuggingFace sentiment model.
  - File: `src/nexus_babel/services/plugins_sentiment.py` (new)
  - AC: Returns `{polarity, positive_score, negative_score, neutral_score, vad_scores}`.

- [ ] **T11-05** [P] Research AMR parsing integration (`amrlib`). Evaluate Smatch scores and memory footprint.
  - AC: Decision documented. Must fit within 16GB constraint.

### S02-12: Advanced Pragmatics

- [ ] **T12-01** [P] Implement PRAG_001 speech_act_classifier: rule-based first pass (question marks, imperatives, hedges, first-person commitments) mapping to 5 categories.
  - File: `src/nexus_babel/services/analysis_pragmatics.py` (new)
  - AC: Classifies sentences into assertive, directive, commissive, expressive, declarative.

- [ ] **T12-02** [P] Research coreference resolution: `neuralcoref` (deprecated), HuggingFace coreference, or spaCy experimental coref.
  - AC: Decision documented with accuracy/stability/dependency tradeoffs.

- [ ] **T12-03** [P] Implement PRAG_005 irony/sarcasm detection: heuristic approach using punctuation patterns, emoji signals, and contradiction indicators.
  - File: `src/nexus_babel/services/analysis_pragmatics.py`
  - AC: Detects simple irony signals (e.g., "Oh great, another meeting" with sarcasm markers).

### S02-13: Advanced Discourse

- [ ] **T13-01** [P] Research RST parsing options: `rst-workbench`, `rstfinder`, or custom model on GUM corpus.
  - AC: Decision documented with F1 targets (span >80%, nuclearity >75%, relation >70%).

- [ ] **T13-02** [S] [Story T13-01] Implement DISC_001 rst_parsing as a discourse layer plugin.
  - File: `src/nexus_babel/services/plugins_discourse.py` (new)
  - AC: Returns `{rst_tree, relations: [{type, nucleus, satellite, span}]}`.

- [ ] **T13-03** [P] Implement DISC_005 argumentation_mining: identify premise, claim, and rebuttal segments using a sequence labeling approach.
  - File: `src/nexus_babel/services/plugins_discourse.py`
  - AC: Returns `{arguments: [{type: "premise"|"claim"|"rebuttal", text, span}]}`.

### S02-14: Advanced Sociolinguistics

- [ ] **T14-01** [P] Implement SOCIO_002 register_classification: feature-based classifier using lexical complexity, sentence length distribution, contraction ratio, passive voice ratio.
  - File: `src/nexus_babel/services/analysis_socioling.py` (new)
  - AC: Classifies text as formal/informal/technical/literary/conversational with confidence.

- [ ] **T14-02** [P] Implement SOCIO_006 enhanced formality_scoring: expand current `1 - (!count / sentence_count)` heuristic with lexical, syntactic, and stylistic features.
  - File: `src/nexus_babel/services/analysis_socioling.py`
  - AC: Formality score uses 5+ features. Tests show improved discrimination between formal and informal texts.

### S02-15: Advanced Rhetoric

- [ ] **T15-01** [P] Expand fallacy patterns in `RhetoricalAnalyzer` from 3 to 10+ types. Add: straw man, appeal to authority, red herring, slippery slope, circular reasoning, hasty generalization, tu quoque.
  - File: `src/nexus_babel/services/rhetoric.py`
  - AC: `FALLACY_PATTERNS` dict has 10+ entries. All new patterns have unit tests.

- [ ] **T15-02** [P] Implement RHET_002 rhetorical_figure_detection: pattern-based detection for anaphora, epistrophe, antithesis, hyperbole, litotes, alliteration (cross-ref with MORPH_008), metaphor indicators.
  - File: `src/nexus_babel/services/rhetoric_figures.py` (new)
  - AC: Detects at least 10 rhetorical figures. Returns `{figures: [{type, text, span, confidence}]}`.

- [ ] **T15-03** [P] Implement RHET_005 persuasive_strategy_identification based on Cialdini's 6 principles: reciprocity, commitment, social proof, authority, liking, scarcity.
  - File: `src/nexus_babel/services/rhetoric_persuasion.py` (new)
  - AC: Returns `{strategies: [{principle, markers, confidence}]}`.

- [ ] **T15-04** [S] Integrate expanded rhetoric functions into the rhetoric layer plugin output.
  - File: `src/nexus_babel/services/analysis.py` or plugin
  - AC: Rhetoric layer output includes `figures`, `expanded_fallacies`, `persuasive_strategies` alongside existing scores.

### S02-16: Semiotic Engine

- [ ] **T16-01** [P] Design semiotic knowledge graph schema: nodes (signs), edges (representamen->object, object->interpretant), properties (denotation_weight, connotation_weight, culture_tag).
  - AC: Schema documented. Compatible with hypergraph storage.

- [ ] **T16-02** [S] [Story T16-01] Implement icon/index/symbol classifier for the semiotic layer.
  - File: `src/nexus_babel/services/semiotic_engine.py` (new)
  - AC: Given a character/emoji, classifies as icon (visual similarity), index (causal/contiguous), or symbol (conventional). Uses static lookup tables initially.

- [ ] **T16-03** [S] [Story T16-02] Implement denotation/connotation analysis for emojis and common symbols using a curated lexicon.
  - File: `src/nexus_babel/services/semiotic_engine.py`
  - AC: Returns `{denotation, connotations: [{meaning, weight, culture}]}` for top-100 emojis.

- [ ] **T16-04** [S] Integrate semiotic engine into the semiotic layer plugin output.
  - File: `src/nexus_babel/services/analysis.py` or plugin
  - AC: Semiotic layer output includes `sign_classifications` and `connotation_analysis` alongside existing counts.

---

## P4: Cross-Layer & Multimodal

### S02-17: Cross-Layer Feedback

- [ ] **T17-01** [P] Design `LayerContext` dataclass that accumulates layer outputs during analysis and is passed as additional context to subsequent layers.
  - File: `src/nexus_babel/services/analysis.py`
  - AC: Design documented. `LayerContext` stores `{layer_name: output}` dict, accessible by any layer plugin.

- [ ] **T17-02** [S] [Story T17-01] Modify `AnalysisService.analyze()` to build `LayerContext` incrementally and pass it to `PluginRegistry.run_layer()` via the `context` dict.
  - File: `src/nexus_babel/services/analysis.py`
  - AC: Each layer receives prior layers' outputs in `context["layer_context"]`. Backward compatible (plugins can ignore it).

- [ ] **T17-03** [S] [Story T17-02] Implement optional multi-pass analysis: after first pass, re-run layers that declare cross-layer dependencies. Add `max_iterations` to `AnalyzeRequest` (default 1).
  - File: `src/nexus_babel/services/analysis.py`, `src/nexus_babel/schemas.py`
  - AC: With `max_iterations=2`, layers that read from `layer_context` produce refined outputs. Convergence tracked.

- [ ] **T17-04** [S] Write tests for single-pass (backward compatible) and multi-pass analysis.
  - File: `tests/test_analysis.py`
  - AC: Single-pass results unchanged. Multi-pass produces equal or improved confidence.

### S02-18: Multimodal Analysis

- [ ] **T18-01** [P] Implement audio-to-text routing: when `modality="audio"`, run Whisper transcription first, then text analysis on transcription.
  - File: `src/nexus_babel/services/analysis.py`
  - AC: Audio documents produce text-layer analysis results from transcribed text.

- [ ] **T18-02** [P] Implement image-to-text routing: when `modality="image"`, extract text via OCR (Tesseract or PaddleOCR), then text analysis.
  - File: `src/nexus_babel/services/analysis.py`
  - AC: Image documents with text content produce text-layer analysis results.

- [ ] **T18-03** [S] Add modality-specific layer selection: audio documents auto-include phonology layer, image documents auto-include semiotic/iconographic layers.
  - File: `src/nexus_babel/services/analysis.py`
  - AC: Layer selection is modality-aware. Text-only layers are skipped for non-text modalities when no transcription is available.

- [ ] **T18-04** [S] Write multimodal analysis integration tests using test fixtures for audio and image documents.
  - File: `tests/test_analysis_multimodal.py` (new)
  - AC: Audio document analysis includes transcription. Image document analysis includes OCR text.

---

## Summary

| Priority | Stories | Tasks | Status |
|----------|---------|-------|--------|
| P1 | S02-01 through S02-06 | 30 tasks | Not started |
| P2 | S02-07 | 9 tasks | Not started |
| P3 | S02-08 through S02-16 | 22 tasks | Not started |
| P4 | S02-17, S02-18 | 8 tasks | Not started |
| **Total** | **18 stories** | **69 tasks** | |

### Parallel Execution Groups (P1)

All P1 stories are independent. Within each story, tasks marked `[P]` can be parallelized:

- **Batch 1 (all [P] tasks across S02-01 through S02-06):** T01-01 through T01-05, T01-07, T02-01 through T02-09, T03-01 through T03-08, T04-01 through T04-05, T05-02 through T05-04, T06-01 through T06-04
- **Batch 2 (sequential tasks):** T01-06, T05-01
- **Batch 3 (P2 sequential chain):** T07-01 -> T07-02 -> T07-03 through T07-07 -> T07-09
