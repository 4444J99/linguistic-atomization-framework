# 02 -- Linguistic Analysis: Implementation Plan

> **Domain:** 02-linguistic-analysis
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Spec reference:** `specs/02-linguistic-analysis/spec.md`

---

## 1. Priority Tiers

| Tier | Scope | Goal |
|------|-------|------|
| P1 | As-built hardening | Test coverage, edge cases, documentation, observability for existing 9-layer engine |
| P2 | ML stub promotion | Replace ML stub with real spaCy/Stanza plugins for token, morphology, syntax, semantics layers |
| P3 | Vision NLP functions | Implement the 84-function RLOS vision layer by layer |
| P4 | Cross-layer & multimodal | Bidirectional feedback, multi-pass analysis, multimodal encoders |

---

## 2. P1 Stories: As-Built Hardening

### S02-01: Baseline 9-Layer Analysis

**What exists:**
- `AnalysisService.analyze()` in `services/analysis.py` computes all 9 baseline layers using regex/string heuristics, runs each through `PluginRegistry`, persists `AnalysisRun` + `LayerOutput` rows.
- Text resolution from `Document.provenance.extracted_text` or `Branch.state_snapshot.current_text`.
- Tested in `test_mvp.py::test_multimodal_linkage` (end-to-end with ingestion) and `test_wave2.py::test_async_job_lifecycle_and_artifacts` (async path).

**What needs hardening:**
1. **Unit tests for each layer's baseline output.** Currently no isolated test validates the shape/values of individual layer outputs. Write parametrized tests that feed known text and assert exact output structure per layer.
2. **Empty text edge case.** The baseline code divides by `max(1, len(words))` which handles empty, but `statistics.mean([0])` could produce unexpected values. Validate edge case behavior for empty/whitespace-only text.
3. **Layer subset selection.** No test covers requesting a partial layer set. Verify that only requested layers appear in output and `LayerOutput` rows.
4. **Large document performance.** Add a benchmark test for a 100KB document to validate NFR-01 (<500ms).

**Files touched:**
- `tests/test_analysis.py` (new)
- `src/nexus_babel/services/analysis.py` (edge case fixes if needed)

### S02-02: Plugin Chain & Provider Provenance

**What exists:**
- `PluginRegistry` with `DeterministicLayerPlugin` and `MLStubLayerPlugin`. Three profile chains. Fallback logic with reason accumulation. `PluginExecution` dataclass.

**What needs hardening:**
1. **Unit tests for profile chain resolution.** Test `_profile_chain()` for all 3 named profiles plus an unknown profile (should default to deterministic).
2. **Fallback behavior test.** Mock a plugin that raises, verify fallback to next plugin and fallback_reason recording.
3. **All-plugins-failed path.** Test the terminal fallback when `ml_only` profile is used and ML is disabled.
4. **Health endpoint coverage.** Verify `health()` returns correct status for enabled/disabled ML.
5. **Runtime measurement accuracy.** Verify `runtime_ms` is > 0 for successful executions.

**Files touched:**
- `tests/test_plugins.py` (new)
- `src/nexus_babel/services/plugins.py` (no changes expected)

### S02-03: Rhetorical Analysis

**What exists:**
- `RhetoricalAnalyzer` with marker sets (6 ethos, 9 pathos, 8 logos), 3 fallacy regex patterns, scoring formula (`count/tokens * 10, cap 1.0`).
- Tested in `test_mvp.py::test_rhetorical_output` (basic shape check).

**What needs hardening:**
1. **Scoring precision tests.** Feed text with known marker counts and verify exact scores.
2. **Fallacy detection tests.** Test each fallacy pattern individually (bandwagon, false dilemma, ad hominem).
3. **Empty text test.** Verify zero-score response for empty/whitespace input.
4. **Edge case: all-marker text.** Text composed entirely of marker words should produce scores near 1.0.
5. **Explainability trace test.** Verify `linked_spans` in analysis pipeline output contain correct marker indices.

**Files touched:**
- `tests/test_rhetoric.py` (new)
- `src/nexus_babel/services/rhetoric.py` (no changes expected)

### S02-04: Execution Modes

**What exists:**
- Sync/async/shadow paths in `routes.py::analyze()`. Async submits a Job. Shadow runs sync + submits async ML job. Feature flags gate async and shadow.
- Tested in `test_wave2.py::test_async_job_lifecycle_and_artifacts` (async path).

**What needs hardening:**
1. **Shadow mode test.** Test with `shadow_execution_enabled=True` and verify both sync result and async job creation.
2. **Shadow disabled test.** Test with `shadow_execution_enabled=False` and verify no async job is created.
3. **Async disabled test.** Verify 400 response when `async_jobs_enabled=False` and `execution_mode="async"`.
4. **Shadow default profile test.** Verify shadow job defaults to `"ml_first"` when original request has no explicit plugin_profile.

**Files touched:**
- `tests/test_analysis.py` (extend)
- `src/nexus_babel/config.py` (no changes expected)

### S02-05: Analysis Run Retrieval

**What exists:**
- `GET /analysis/runs/{id}` and `GET /analysis/runs` endpoints. `AnalysisService.get_run()` joins `LayerOutput` records.

**What needs hardening:**
1. **Retrieval shape test.** Verify response includes all expected fields from `AnalysisRunResponse`.
2. **Not-found test.** Verify 404 for nonexistent run ID.
3. **Pagination test.** Verify `limit` parameter works correctly.
4. **Layer output ordering.** Verify layer_outputs match the order of requested layers.

**Files touched:**
- `tests/test_analysis.py` (extend)

### S02-06: Conflict & Mode Enforcement

**What exists:**
- Conflict/ingestion check in routes.py. Mode enforcement via `_enforce_mode()`.
- Tested in `test_mvp.py::test_conflict_hygiene_and_analyze_409`.

**What needs hardening:**
1. **Non-ingested document test.** Verify 409 when document exists but `ingested=False` and `conflict_flag=False`.
2. **RAW mode with disabled system flag.** Verify 403 when system `raw_mode_enabled=False`.
3. **RAW mode with disabled per-key flag.** Verify 403 when per-key `raw_mode_enabled=False`.

**Files touched:**
- `tests/test_analysis.py` (extend)

---

## 3. P2 Stories: ML Plugin Promotion

### S02-07: ML Plugin Integration

**Goal:** Replace the `MLStubLayerPlugin` with real NLP plugins that use spaCy (or Stanza) for token, morphology, syntax, and semantics layers.

**Approach:**
1. Define a `SpacyLayerPlugin` that wraps a loaded spaCy model (`en_core_web_sm` or `en_core_web_md`).
2. Implement `supports()` to return True for layers: token, morphology, syntax, semantics, pragmatics.
3. Implement `run()` per layer:
   - **token:** Return proper tokenization with POS tags. <!-- allow-secret -->
   - **morphology:** Return lemmas, morphological features, word lengths.
   - **syntax:** Return dependency parse, sentence segmentation, clause detection.
   - **semantics:** Return NER entities (spaCy types), similarity scores.
4. Register `SpacyLayerPlugin` in `PluginRegistry` under `"spacy"` name.
5. Add new profile: `"spacy_first"` -> `[spacy, deterministic]`.
6. Add spaCy as an optional dependency in `pyproject.toml` under `[project.optional-dependencies.nlp]`.
7. The ML stub remains for layers not covered by spaCy (discourse, sociolinguistics, rhetoric, semiotic).

**Confidence targets (with spaCy):**
- token: 0.85+ <!-- allow-secret -->
- morphology: 0.80+
- syntax: 0.82+
- semantics: 0.78+

**Files to create/modify:**
- `src/nexus_babel/services/plugins_spacy.py` (new)
- `src/nexus_babel/services/plugins.py` (register new plugin)
- `pyproject.toml` (add `nlp` extra)
- `tests/test_plugins_spacy.py` (new)

**Risks:**
- spaCy model download (~30MB for `sm`, ~90MB for `md`) adds CI complexity.
- spaCy is not async-native; may need thread pool for async execution mode.
- Memory impact: ~200MB per loaded model. Must not break 16GB RAM constraint.

---

## 4. P3 Stories: Vision NLP Functions

### S02-08: Phonology Layer

**Functions:** PHON_001 speech_to_text (Whisper), PHON_002 extract_prosody (F0/intensity).

**Approach:**
1. Create `WhisperPhonologyPlugin` wrapping OpenAI Whisper (or `faster-whisper`).
2. PHON_001: Transcribe audio documents. Output: `{transcription, language, segments}`.
3. PHON_002: Extract prosody from audio using `parselmouth` (Praat wrapper). Output: `{pitch_contour, intensity_contour, speaking_rate}`.
4. Register as layer `"phonology"` (new 10th layer) or sub-layer of token.
5. Only activates for `modality="audio"`.

**Dependencies:** `openai-whisper` or `faster-whisper`, `parselmouth`, `soundfile`.

### S02-09: Advanced Morphology

**Functions:** MORPH_002 lemmatize, MORPH_003 morphological_parse, MORPH_008 detect_alliteration, MORPH_009 detect_assonance.

**Approach:**
1. Extend `SpacyLayerPlugin` (from S02-07) with lemmatization and morphological features.
2. Implement alliteration detector: scan consecutive words for shared initial consonant clusters.
3. Implement assonance detector: scan words for repeated vowel patterns.
4. Output additions: `{lemmas, morphological_features, alliteration_spans, assonance_spans}`.

### S02-10: Advanced Syntax

**Functions:** SYNT_001 dependency_parse, SYNT_002 pos_tag, SYNT_005 detect_parallelism, SYNT_006 detect_chiasmus.

**Approach:**
1. Dependency parse and POS tagging via spaCy (already planned in S02-07).
2. Parallelism detector: compare POS tag sequences across sibling clauses for structural similarity.
3. Chiasmus detector: detect A-B-B-A patterns in POS/lexical sequences (F1 target ~0.78).
4. Output additions: `{dependency_tree, pos_tags, parallel_structures, chiasmus_candidates}`.

### S02-11: Advanced Semantics

**Functions:** SEM_001 NER, SEM_002 SRL, SEM_003 sentiment, SEM_007 metaphor_detection, SEM_012 AMR parsing.

**Approach:**
1. NER: Replace capitalized-word heuristic with spaCy NER (or HuggingFace NER model for 18 fine-grained types).
2. SRL: Use AllenNLP SRL model or a HuggingFace SRL pipeline.
3. Sentiment: Use `cardiffnlp/twitter-roberta-base-sentiment` or similar.
4. Metaphor: Train/use a binary metaphor classifier (literal vs. figurative).
5. AMR: Use `amrlib` for AMR parsing (Smatch target >84%).

**Dependencies:** `transformers`, `amrlib`, `allennlp` (optional).

### S02-12: Advanced Pragmatics

**Functions:** PRAG_001 speech_act_classification, PRAG_002 coreference, PRAG_005 irony/sarcasm.

**Approach:**
1. Speech act classifier: Fine-tune a small model on speech act corpus (5 categories: assertive, directive, commissive, expressive, declarative).
2. Coreference: Use `neuralcoref` or HuggingFace coreference model.
3. Irony/sarcasm: Use multimodal features (text + punctuation + emoji patterns).

### S02-13: Advanced Discourse

**Functions:** DISC_001 rst_parsing, DISC_005 argumentation_mining.

**Approach:**
1. RST parser: Use `rst-workbench` or train on GUM corpus. Graph-based (not tree-only).
2. Argumentation mining: Identify premise-claim-rebuttal structure using a sequence labeling model.

### S02-14: Advanced Sociolinguistics

**Functions:** SOCIO_002 register_classification, SOCIO_006 formality_scoring.

**Approach:**
1. Register classifier: Feature-based (lexical complexity, sentence length, contraction ratio, passive voice ratio) + optional ML model.
2. Formality scorer: Expand current heuristic with syntactic features (passive voice, nominal style, hedging).

### S02-15: Advanced Rhetoric

**Functions:** RHET_002 figure_detection, RHET_003 expanded fallacy_detection, RHET_004 propaganda.

**Approach:**
1. Rhetorical figure detection: Pattern-based for 25+ figures (anaphora, epistrophe, antithesis, hyperbole, litotes, etc.).
2. Fallacy detection: Expand from 3 to 10+ types. Use SemEval propaganda detection dataset.
3. Propaganda technique detection: Fine-tune on PTC corpus (18 techniques).

### S02-16: Semiotic Engine

**Functions:** Peircean triadic engine, icon/index/symbol classification.

**Approach:**
1. Build semiotic knowledge graph with denotation/connotation edges.
2. Icon classification via visual similarity (CLIP embeddings).
3. Index classification via causal reasoning (knowledge graph traversal).
4. Symbol classification via cultural symbol lexicon + sociolinguistic context.

---

## 5. P4 Stories: Cross-Layer & Multimodal

### S02-17: Cross-Layer Feedback

**Goal:** Enable bidirectional information flow between layers.

**Approach:**
1. Define a `LayerContext` that accumulates outputs from all layers run so far.
2. Pass `LayerContext` to each subsequent layer as additional input.
3. Implement optional second pass: after all layers run once, re-run layers that have cross-layer dependencies.
4. Add `max_iterations` config (default 1 = no feedback, 2 = one feedback pass).
5. Track convergence: compare layer outputs between iterations, stop when delta < threshold.

### S02-18: Multimodal Analysis

**Goal:** Process non-text modalities through appropriate layer subsets.

**Approach:**
1. Audio: Route through phonology plugin (Whisper transcription), then text analysis on transcription.
2. Image: Route through semiotic/iconographic plugins, extract text via OCR, then text analysis on extracted text.
3. Video: Frame sampling + ViT + temporal transformer for visual features, Whisper for audio track.
4. Shared embedding space: CLIP-style contrastive learning for cross-modal alignment.

---

## 6. Dependency Graph

```
S02-01 (baseline tests) ───┐
S02-02 (plugin tests)  ────┤
S02-03 (rhetoric tests) ───┤──> P1 complete
S02-04 (exec mode tests) ──┤
S02-05 (retrieval tests) ──┤
S02-06 (enforcement tests) ┘
                            |
                            v
S02-07 (spaCy plugin) ─────> P2 complete
                            |
                            v
S02-08 (phonology) ────────┐
S02-09 (adv morphology) ───┤ (depends on S02-07 for spaCy base)
S02-10 (adv syntax) ───────┤
S02-11 (adv semantics) ────┤──> P3 complete
S02-12 (adv pragmatics) ───┤
S02-13 (adv discourse) ────┤
S02-14 (adv socioling) ────┤
S02-15 (adv rhetoric) ─────┤
S02-16 (semiotic engine) ──┘
                            |
                            v
S02-17 (cross-layer) ──────┐
S02-18 (multimodal) ───────┘──> P4 complete
```

P1 stories are independent of each other and can be parallelized.
P3 stories S02-09 through S02-14 depend on S02-07 (spaCy plugin) for the base NLP pipeline.
P3 stories S02-08, S02-15, S02-16 can proceed independently.
P4 stories depend on all P3 work.

---

## 7. Testing Strategy

### Unit Tests (per story)

| Story | Test File | Scope |
|-------|-----------|-------|
| S02-01 | `tests/test_analysis.py` | Per-layer output shape, empty text, layer subsets, confidence values |
| S02-02 | `tests/test_plugins.py` | Profile chains, fallback, all-fail, health, runtime |
| S02-03 | `tests/test_rhetoric.py` | Scoring precision, each fallacy, empty text, explainability |
| S02-04 | `tests/test_analysis.py` | Shadow mode, async disabled, shadow disabled |
| S02-05 | `tests/test_analysis.py` | Retrieval shape, 404, pagination |
| S02-06 | `tests/test_analysis.py` | Conflict, non-ingested, RAW mode enforcement |
| S02-07 | `tests/test_plugins_spacy.py` | spaCy plugin per-layer output, confidence, fallback |

### Integration Tests

- Existing `test_mvp.py` covers the full ingest-analyze-retrieve pipeline.
- Existing `test_wave2.py` covers async job lifecycle with analysis.
- New integration tests should cover shadow execution end-to-end.

### Performance Tests

- `tests/test_perf_analysis.py` (new): Benchmark 100KB document analysis under 500ms (NFR-01).
- Mark with `@pytest.mark.slow` to exclude from CI fast path.

---

## 8. Migration Notes

### Database

No new migrations required for P1 or P2. The `AnalysisRun` and `LayerOutput` tables are already created in `20260218_0001_initial` and `20260218_0002_wave2_alpha`.

### Configuration

P2 will add:
- `NEXUS_SPACY_MODEL` setting (default: `en_core_web_sm`).
- `NEXUS_NLP_EXTRA_ENABLED` feature flag for optional NLP dependencies.

### Backward Compatibility

- All P2/P3 changes are additive. Existing `deterministic` profile behavior is unchanged.
- New plugins are registered under new names; existing profile chains are unmodified.
- Layer output schemas are extended (new fields added), never breaking (no fields removed).

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| spaCy model memory (~200MB) on 16GB machine | OOM in CI or dev | Use `en_core_web_sm` (30MB), lazy-load model, test with `@pytest.mark.nlp` gate |
| ML inference latency breaking <500ms NFR | Slow sync analysis | Run ML layers only in async/shadow mode; deterministic remains fast path |
| Whisper model size (1.5GB for medium) | Disk/memory pressure | Use `tiny` or `base` model for dev; `medium` only in production |
| 84 functions overwhelming scope | Feature creep | Strict priority tiers; P3 functions implemented only as plugins, never modifying core |
| Tokenizer inconsistency (rhetoric vs. text_utils) | Subtle count mismatches | Consolidate to single tokenizer in P1 (low priority, document as known issue) |
| Shadow execution creating orphaned async jobs | Job queue pollution | Add TTL/cleanup for shadow jobs; track shadow_parent_run_id |
