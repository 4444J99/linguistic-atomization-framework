[![ORGAN-I: Theoria](https://img.shields.io/badge/ORGAN--I-Theoria-311b92?style=flat-square)](https://github.com/organvm-i-theoria)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Status: MVP Scaffold](https://img.shields.io/badge/status-mvp%20scaffold-green?style=flat-square)]()
[![Specification: 50K words](https://img.shields.io/badge/specification-50%2C000%20words-informational?style=flat-square)]()

# Nexus Babel Alexandria

**ARC4N Living Digital Canon — A Breathing Organism for Language Evolution**

> *A living modular library that atomizes classic and modern literary works down to their molecular level — glyph-seeds, syllables, words, sentences, paragraphs — enabling creative recombination, temporal evolution, and scholarly exploration across a spiral of expansion, compression, and rebirth.*

## Vision

ARC4N is not a static archive. It is a **synthetic linguistic organism** capable of recording, simulating, accelerating, and inventing the full evolutionary arc of language — from primordial glyph to cosmic song. Every letter is an active generative glyph-seed carrying phonemic, historic, and thematic metadata. Every document can drift naturally through centuries of linguistic change, mutate synthetically at accelerated rates, or remix with other texts to birth entirely new compositions.

The NLP engine underneath (Theoria Linguae Machina) provides 9-layer rhetorical-linguistic analysis through a bidirectional hypergraph architecture grounded in category theory, Peircean semiotics, and Aristotelian rhetoric. The original RLOS design documents are preserved in `docs/corpus/`.

## Canon-Building Capabilities

- **5-Level Atomization**: Glyph-seeds (with phoneme, historic forms, visual mutations, thematic tags) → syllabic clusters → words → sentences → paragraphs
- **Temporal Evolution**: Natural drift (historic linguistic shifts), synthetic mutation, phase shifts (expansion/peak/compression/rebirth), glyph fusion
- **Seed Text Provisioning**: Canonical works (Homer, Dante, Whitman, Joyce, Shelley) provisioned from Project Gutenberg
- **Remix Engine**: Interleave, thematic blend, temporal layer, and glyph collide strategies across documents
- **Branch Timelines**: Deterministic, replayable evolution forks with seeded RNG
- **9-Layer Analysis**: Token, morphology, syntax, semantics, pragmatics, discourse, sociolinguistics, rhetoric, semiotic
- **Dual-Mode Governance**: PUBLIC (content filtering) / RAW (research access with flagging)
- **Hypergraph Projection**: Neo4j + local cache with integrity verification

## Implementation Status

- Full REST API under `/api/v1/*` with 28 operations across ingest, analysis, jobs, governance, branches, remix, and corpus seed management
- UI shells: `/app/corpus`, `/app/hypergraph`, `/app/timeline`, `/app/governance`
- Postgres-compatible SQLAlchemy schema + Neo4j projection adapter
- Async job queue with retry/backoff, canonicalization, multimodal ingestion
- Test coverage: ingestion, governance, hypergraph integrity, branch determinism, evolution, remix, ARC4N atomization

### MVP Implemented vs Planned (Snapshot)

| Area | MVP Implemented (Current Repo) | Planned / Roadmap (RLOS) |
|---|---|---|
| API surface | `28` `/api/v1` operations for ingest, analysis, jobs, governance, branches, remix, corpus seeds | Expanded orchestration and deeper analysis APIs aligned to long-horizon RLOS roadmap |
| Analysis engine | Deterministic heuristic layer outputs with plugin fallback architecture (`deterministic`, `ml_stub`) | Full ML-backed multi-layer RLOS implementations and richer plugin providers |
| Governance | PUBLIC/RAW mode policy evaluation with audit logging and decision traces | Expanded policy governance, stronger auth, and broader compliance controls |
| Evolution & Remix | Deterministic branch evolution + remix artifact persistence/lineage hooks | Deeper generative engines, richer lineage projections, and advanced composition semantics |
| Ops & DX | FastAPI app, worker, Alembic migrations, contract/integration tests, operator runbook | Broader CI quality gates, production deployment hardening, and roadmap-driven subsystem expansion |

This repository is an active MVP implementation with a preserved theoretical corpus. The long-form RLOS roadmap in `docs/roadmap.md` remains aspirational and should not be interpreted as already implemented.

### Quickstart

1. Install dependencies:
   - `python3 -m pip install -e .[dev,postgres]`
2. Start infrastructure (optional but recommended for Postgres/Neo4j):
   - `docker compose up -d`
3. Configure environment:
   - `cp .env.example .env`
4. Run API:
   - `uvicorn nexus_babel.main:app --reload`
5. Run worker:
   - `python -m nexus_babel.worker`
6. Run ingestion against current corpus:
   - `python scripts/ingest_corpus.py`
7. Run tests:
   - `pytest -q`
8. Regenerate normalized OpenAPI contract snapshot after intentional API changes:
   - `make openapi-snapshot` (or `.venv/bin/python scripts/generate_openapi_contract_snapshot.py`)
9. Regenerate and verify certainty artifacts after changes that affect repo structure, route inventory, docs, or roadmap references:
   - `make certainty`
   - `make certainty-check`
10. Run a local verification bundle (optional, recommended before PRs):
   - `make verify`

### Security Model (MVP)

- All `/api/v1/*` routes require `X-Nexus-API-Key`.
- Roles:
  - `viewer`: read-only endpoints.
  - `operator`: ingest/analyze/governance in `PUBLIC`.
  - `researcher` and `admin`: all `operator` actions plus `RAW` mode.
- `RAW` mode can be globally disabled with `NEXUS_RAW_MODE_ENABLED=false`.

### Known Limitations

- API-key auth is the MVP control plane; OAuth/JWT is not included in this slice.
- Multimodal OCR/prosody paths are metadata-first and intentionally shallow.
- Files containing Git conflict markers are treated as non-ingestable until resolved.

### Durability Guarantees (MVP)

- Document atom totals are stored in SQL (`atom_count`, `graph_projected_atom_count`, `graph_projection_status`).
- Hypergraph integrity endpoints are derived from durable counters and can optionally verify Neo4j counts.
- Canonicalization is recomputed deterministically from the authoritative corpus snapshot on each ingest job.

---

## Table of Contents

- [Theoretical Purpose](#theoretical-purpose)
- [Philosophical Framework](#philosophical-framework)
- [The Nine-Layer Plexus Architecture](#the-nine-layer-plexus-architecture)
- [Formal Foundations](#formal-foundations)
- [The 84 Core Functions](#the-84-core-functions)
- [Semiotic Engine](#semiotic-engine)
- [Rhetorical Strategy Engine](#rhetorical-strategy-engine)
- [Multimodal Architecture](#multimodal-architecture)
- [Meta-Learning and Evolution](#meta-learning-and-evolution)
- [Dual-Mode Governance](#dual-mode-governance)
- [Technical Architecture](#technical-architecture)
- [Cross-Organ Position](#cross-organ-position)
- [Repository Contents](#repository-contents)
- [Related Work](#related-work)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Theoretical Purpose

Nexus Babel Alexandria began as a pure design-document repository and still preserves that corpus. It now also includes an MVP implementation of the ingestion, analysis, evolution, governance, and UI shell surfaces described by the original specification.

The document proposes **RLOS (Rhetorical-Linguistic Operating System)**, a nine-layer "plexus architecture" for computational linguistics. Where conventional NLP pipelines process language as a linear sequence of transformations — tokenize, parse, classify, output — RLOS models language as a **bidirectional hypergraph** in which every layer communicates with every other layer simultaneously. A morphological insight can reshape a pragmatic interpretation; a sociolinguistic register shift can rewrite a syntactic parse. The architecture treats language the way language actually behaves: as a living, self-referential system where meaning emerges from the interplay of all levels at once.

The name encodes three epistemic commitments. **Nexus**: connection, the hypergraph substrate that refuses to decompose language into isolated components. **Babel**: multiplicity, the insistence that any serious language system must work for Yoruba and Welsh and Tagalog with the same architectural commitment it gives to English. **Alexandria**: preservation, the ambition to build a knowledge architecture capacious enough to hold the full complexity of human linguistic expression without reducing it to feature vectors.

This is ORGAN-I (Theoria) work in its most concentrated form. The document synthesizes traditions that rarely share a page — Friedrich Kittler's media archaeology alongside Abstract Meaning Representation, Aristotle's rhetorical triangle alongside DisCoCat categorical semantics, Peirce's triadic semiotics alongside PyTorch tensor operations — and proposes a unified computational framework that respects all of them. Whether or not this system is ever built exactly as specified, the synthesis itself maps intellectual territory that the NLP community has left largely unexplored.

The central theoretical claim is that **language is irreducibly multi-layered, bidirectional, and rhetorical**. Any system that processes language through a linear pipeline — however sophisticated its transformer architecture — has already committed an ontological error by assuming that phonology precedes morphology precedes syntax precedes semantics. RLOS refuses that assumption. The plexus architecture is not merely an engineering choice but a philosophical position about the nature of linguistic cognition.

---

## Philosophical Framework

### The Problem of Linearity in Computational Linguistics

The dominant paradigm in NLP treats language processing as a pipeline: raw input enters at one end, passes through successive transformation stages, and exits as structured output at the other. This model, inherited from the Chomskyan tradition of generative grammar (where deep structure maps to surface structure through ordered transformations), persists in modern architectures even when the underlying theory has moved on.

The pipeline assumption is not merely an engineering convenience — it is an epistemological commitment. It asserts that linguistic knowledge decomposes cleanly into sequential layers, that information flows in one direction, and that each layer's output is sufficient input for the next. Every NLP practitioner knows this is false. Pragmatic context reshapes syntactic interpretation. Prosodic contour disambiguates lexical meaning. Sociolinguistic register determines morphological choice. The pipeline handles these cross-layer interactions as special cases, exceptions, post-hoc corrections. The plexus handles them as the fundamental mechanism of linguistic cognition.

### Four Theoretical Pillars

The RLOS specification draws its formal architecture from four traditions, each contributing irreplaceable structural commitments:

**Category Theory and DisCoCat Semantics.** The mathematical backbone is Distributional Compositional Categorical (DisCoCat) semantics, which uses category theory to model how word meanings compose into sentence meanings. In the RLOS architecture, each plexus layer is a category, morphisms between layers are functors, and the hypergraph connections are natural transformations. This gives the system a rigorous algebraic structure for reasoning about cross-layer interactions — not as ad hoc connections but as mathematically principled mappings. The use of Frobenius algebras for relative clauses and quantum density matrices for polysemy extends the framework into domains that standard distributional semantics cannot reach.

**Peircean Semiotics.** Charles Sanders Peirce's triadic sign theory (sign-object-interpretant) provides the framework for how RLOS models meaning across modalities. Where Saussurean semiotics offers a dyadic model (signifier-signified) that maps cleanly onto text, Peirce's triadic model handles the multimodal reality of language: an icon (visual resemblance), an index (causal connection), and a symbol (conventional association) all participate in meaning-making simultaneously. The concept of unlimited semiosis — where every interpretant becomes the sign vehicle for a subsequent interpretation — maps directly onto the recursive structure of the hypergraph, where every node's meaning is perpetually conditioned by its connections.

**Aristotelian Rhetoric.** The rhetorical tradition contributes the ethos-pathos-logos-kairos framework as a first-class analytical dimension. The system does not merely classify text by sentiment (a semantic task) but models the rhetorical strategies at work: how a speaker constructs credibility (ethos), appeals to emotion (pathos), constructs logical arguments (logos), and responds to situational context (kairos). This is most visible in the Pragmatic and Discourse layers, where rhetorical function shapes the interpretation of speech acts and argumentation structures. The inclusion of kairos — the right thing at the right time — as a computational concern is, as far as this document is aware, unprecedented in NLP.

**Media Archaeology (Kittler).** Friedrich Kittler's insight that media systems are not transparent tools but infrastructural conditions for what can be said, known, and argued informs the Meta-Interface layer and the entire governance architecture. RLOS does not present itself as a neutral analysis tool. The specification explicitly acknowledges that the system's architecture constitutes an epistemological framework — that the choice of what to foreground in a visualization is a political act, that the decision to model rhetoric computationally is itself a rhetorical move. This self-reflexivity, unusual in a technical specification, is characteristic of ORGAN-I's commitment to theory that knows itself as theory.

### The Synthesis as Contribution

These four traditions have been developed in near-total isolation from each other. Category theorists working on DisCoCat rarely cite Kittler. Rhetoricians working on persuasion analysis rarely formalize their models in algebraic terms. Semioticians working on multimodal meaning rarely engage with the concrete engineering constraints of transformer architectures. The specification's primary intellectual contribution is demonstrating that these traditions are not merely compatible but mutually necessary: category theory provides the algebraic structure, semiotics provides the theory of signs, rhetoric provides the theory of purpose, and media archaeology provides the critical self-awareness that prevents the system from mistaking its own abstractions for neutral descriptions of reality.

---

## The Nine-Layer Plexus Architecture

The core architectural innovation is the **plexus**: nine layers arranged not as a pipeline but as a fully connected hypergraph where information flows bidirectionally between all layers through synchronous hyperedge replacement grammars.

| Layer | Domain | Core Concern |
|-------|--------|-------------|
| **1. ICONOGRAPHIC / INTERFACE** | Multimodal intake and output | Image, audio, video, text ingestion; cross-modal alignment via CLIP/Whisper |
| **2. PHONOLOGICAL** | Speech and prosody | Phoneme processing, intonation contours, prosodic structure, speech-text alignment |
| **3. MORPHOLOGICAL** | Tokenization and lexicon | Morpheme decomposition, compound analysis, neologism detection, multilingual stemming |
| **4. SYNTACTIC** | Grammar and structure | Dependency parsing, constituency trees, grammatical relation extraction |
| **5. SEMANTIC** | Meaning and intent | Entity recognition, sentiment analysis, semantic role labeling, intent classification |
| **6. PRAGMATIC** | Context and implicature | Speech act detection, presupposition resolution, Gricean maxim modeling, indirect speech |
| **7. DISCOURSE** | Coherence and argumentation | RST relations, discourse connectives, argumentation mining, narrative structure |
| **8. SOCIOLINGUISTIC** | Register, dialect, and culture | Style detection, code-switching, dialect identification, cultural context modeling |
| **9. META-INTERFACE** | User interaction | Visualization, explanation generation, interactive exploration, feedback loops |

The key departure from standard architectures: **there are no back-edges because there is no forward direction.** Every layer connects to every other layer through the hypergraph. A phonological pattern (sarcastic intonation) directly informs pragmatic interpretation without passing through syntax and semantics as intermediaries. A sociolinguistic register shift (formal to colloquial) directly modifies morphological tokenization strategies. The plexus treats these cross-layer interactions not as edge cases to be patched but as the fundamental mechanism of linguistic cognition.

The mathematical substrate for this full connectivity is a **labeled property hypergraph** — a graph structure in which edges can connect arbitrary numbers of nodes (not just pairs), each edge and node carries typed properties, and the graph supports efficient traversal in any direction. The specification details a custom `.rl` format (JSON-LD based) for serializing these hypergraphs, with each node carrying layer-specific embeddings in 768-1024 dimensional vector spaces.

---

## Formal Foundations

### Category Theory Framework

The DisCoCat framework treats grammar as a free rigid monoidal category **G** and semantics as the category **FVect** of finite-dimensional vector spaces. A strong monoidal functor **F: G -> S** maps grammatical derivations to semantic computations, ensuring that compositional sentence meaning arises from word-level meanings in an algebraically principled way.

The specification extends this standard framework in two directions:

- **Frobenius algebras** model relative clauses and other recursive structures, providing a categorical account of how embedded clauses interact with their matrix sentences.
- **Quantum density matrices** model lexical polysemy, treating a word's meaning not as a single vector but as a mixed state that collapses to a particular sense under contextual measurement.

### Synchronous Hyperedge Replacement Grammars

The computational formalism for inter-layer communication is drawn from Synchronous Hyperedge Replacement Grammars (SHRGs), which generalize synchronous context-free grammars to hypergraphs. Where SCFGs model the relationship between two string languages (useful for machine translation), SHRGs model the relationship between two graph languages — which is exactly what RLOS needs to formalize the bidirectional mappings between plexus layers.

Parsing complexity is bounded at O(n^(k+1) * 3^(d(k+1))) for treewidth k. The specification notes that 98% of AMR semantic graphs have treewidth 2 or less, making SHRG parsing tractable for realistic linguistic inputs. The use of S-Graph grammars (with Merge, Rename, and Forget operations) provides a 6722x speedup over the standard HRG toolkit Bolinas, bringing the formalism from theoretical elegance into practical viability.

### Abstract Meaning Representation Extensions

The specification extends standard AMR in three directions critical for the plexus architecture:

- **Multimodal AMR**: Nodes for visual and audio entities, cross-modal edges linking textual references to perceptual grounding.
- **Rhetorical AMR**: Discourse relations encoded as graph edges, connecting the semantic layer to the discourse and pragmatic layers.
- **Temporal/Modal AMR**: Uniform Meaning Representation (UMR) extensions for temporal relations and modality, enabling the system to reason about tense, aspect, and counterfactual meaning.

Performance target: Smatch F1 greater than 85% with an explainable SHRG backbone — meaning the system can not only produce correct semantic graphs but also provide human-readable derivation traces for its analyses.

---

## The 84 Core Functions

The design document specifies **84 core functions** across all nine layers, each with defined inputs, outputs, dependencies, and target accuracy metrics. These are not API endpoints — they are functional specifications for capabilities the system would need to exhibit.

The functions span eight functional categories:

- **Phonology (8 functions)**: Speech-to-text via Whisper, prosodic extraction (F0, intensity, duration, rhythm), intonation classification, stress detection, tone classification for tonal languages, phonetic alignment via Montreal Forced Aligner, voice activity detection, and speaker diarization.

- **Morphology (10 functions)**: Language-specific tokenization (with dedicated modules for Chinese/jieba, Japanese/MeCab, Arabic/CAMeL), lemmatization, morpheme segmentation (critical for agglutinative languages like Turkish and Finnish), compound decomposition, stemming, inflection generation, emoji normalization, alliteration detection, assonance detection, and grapheme safety checking (homoglyph detection for security).

- **Syntax (12 functions)**: Universal Dependencies parsing, POS tagging (UPOS universal tagset), constituency parsing, phrase extraction, rhetorical parallelism detection, chiasmus detection (A-B-B-A patterns, F1 ~0.78), clause segmentation, argument structure analysis, grammaticality scoring, modifier extraction, coordination resolution, and long-distance dependency tracking (filler-gap/wh-movement).

- **Semantics (14 functions)**: Named entity recognition (18 fine-grained types, F1 >90%), semantic role labeling (PropBank/FrameNet, F1 ~87%), sentiment analysis (polarity + VAD scores, F1 >92%), semantic similarity (Sentence-BERT), intent classification (20+ types, F1 >85%), word sense disambiguation (WordNet synsets, F1 ~80%), metaphor detection (F1 ~75-80%), frame semantic parsing, temporal and causal relation extraction, emotion classification (8 emotions, F1 ~65-75%), AMR parsing (Smatch ~84%), entity linking (Wikipedia/Wikidata), and multimodal grounding.

- **Pragmatics (11 functions)**: Speech act classification (Searle's 5 categories), coreference resolution, Gricean implicature detection, presupposition identification, irony/sarcasm detection (multimodal: text + prosody + emoji), politeness analysis (Brown and Levinson framework), hedging detection, deictic resolution (including gestural deixis), ellipsis recovery, question type classification, and dialogue act tagging.

- **Discourse (9 functions)**: Enhanced RST parsing with graph structure (F1 >70% relation labeling), topic segmentation, topic tracking, coherence evaluation, argumentation mining (premise-claim-rebuttal), rhetorical relation classification (25+ relations), discourse deixis resolution, information structure (given-new, topic-focus), and discourse marker analysis.

- **Sociolinguistics (8 functions)**: Dialect identification, register classification (formal/informal/technical/literary), style analysis (authorship attribution), code-switching detection, politeness strategy detection (positive/negative face), formality scoring, sociolinguistic gender marker analysis (with ethics constraints), and cultural context retrieval via the World Knowledge and Reasoning Module.

- **Iconography and Rhetoric (12 functions)**: Emoji sense disambiguation (EmojiNet), emoji sentiment analysis (VAD scores), hieroglyph processing (Egyptian/Mayan/Chinese pictographs), typography analysis (font semantics, CAPS, emphasis), meme template recognition, visual metaphor detection, rhetorical appeal classification (ethos/pathos/logos, F1 ~0.75-0.85), rhetorical figure detection (25+ figures), fallacy detection (10+ types, F1 ~0.70-0.84), propaganda technique detection (18 techniques), persuasive strategy identification (Cialdini's 6 principles), and argument quality assessment.

Each function specification includes target accuracy ranges (typically 85-95% F1 for well-resourced languages), computational complexity estimates, and dependency chains to other functions.

---

## Semiotic Engine

The Peircean Semiotic Engine implements Peirce's triadic sign model as a computational system:

- **Representamen**: The sign vehicle — emoji bytes, sound waves, pixel arrays, typographic marks.
- **Object**: The referent concept — what the sign points to.
- **Interpretant**: The context-dependent meaning effect — what the sign produces in its receiver.

The engine classifies signs along the icon-index-symbol axis. Icons are detected through visual similarity metrics and CLIP embeddings. Indexes are traced through causal reasoning via the World Knowledge and Reasoning Module. Symbols are resolved through a cultural symbol lexicon integrated with the sociolinguistic context layer.

A critical feature is the modeling of **semiotic chains** — where one sign's interpretant becomes the representamen of the next sign, producing the "unlimited semiosis" that Peirce described and that Umberto Eco made central to his theory of interpretation. The specification illustrates this with the example of a red rose: denotation (Rosa genus flower) branches into culturally weighted connotations (love at 0.9 in Western cultures, England at 0.6 in British contexts, pain/thorns at 0.4 in warning contexts), with the pragmatic and sociolinguistic modules providing the contextual weights that select the appropriate connotative chain.

The emoji semantics subsystem demonstrates the engine's practical application. The skull emoji carries a denotative meaning (death, danger) and a context-dependent connotative meaning ("I'm dying of laughter" in internet slang). The engine disambiguates through co-occurrence analysis, contextual BERT embeddings, and semantic shift detection via longitudinal analysis — detecting when a sign's dominant interpretant has shifted across a community over time.

---

## Rhetorical Strategy Engine

The Rhetorical Strategy Engine (RSE) implements Aristotle's rhetorical triad as a computational framework with measurable performance targets:

**Ethos Detection (F1 ~0.75-0.80)**: Identifies credibility construction through source citations, expertise markers, trust signals, and their opposites (ad hominem attacks, credibility undermining). The engine distinguishes between ethos-building and ethos-attacking moves.

**Pathos Detection (F1 ~0.80-0.85)**: The highest-performing component, reflecting the relative salience of emotional language in persuasive text. Draws on emotion lexicons (NRC, VAD), intensity adjectives, vivid imagery, and metaphor. The specification notes that approximately 31% of persuasive text clauses contain pathos-bearing elements.

**Logos Detection**: Integrates argumentation mining, logical connective analysis, and evidence marker detection with the fallacy detection subsystem (F1 ~0.70-0.84). RST integration provides the argumentative structure that logos analysis requires.

**Kairos Assessment**: Models situational appropriateness — not just what is said but whether it is the right thing at the right time. This is the most experimental component, drawing on audience modeling and contextual state tracking.

The engine implements Enhanced Rhetorical Structure Theory (eRST), which extends traditional tree-based RST to a graph-based model handling concurrent relations. The system identifies 25+ discourse relations (Elaboration, Evidence, Contrast, Concession, Motivation, Antithesis, among others) with signal-based detection using explicit markers ("although," "because," "however").

The computational persuasion subsystem models audiences as probabilistic state machines with belief states (Bayesian networks), emotional states (VAD coordinates), cognitive states (elaboration likelihood), social identities (values, ideology), and credibility perceptions (trust ratings). Strategy selection optimizes P(Goal_State | Strategy, Current_State) subject to ethical constraints: in PUBLIC mode, all manipulative strategies (fallacies, deception, dark patterns) are prohibited, while non-rational persuasion (emotion, ethos) is permitted only when accompanied by rational persuasion (facts, evidence, logic).

---

## Multimodal Architecture

The multimodal integration architecture uses **Multimodal Bottleneck Transformers** with cross-attention mechanisms to avoid the quadratic scaling that naive fusion would require. Modality-specific encoders produce embeddings in a shared 512-768 dimensional space:

- **Text**: SentencePiece/BPE tokenization to 768-1024d embeddings
- **Image**: Vision Transformer (ViT) with 14x14 or 16x16 patches
- **Audio**: Whisper/Wav2Vec2 spectrogram encoding
- **Video**: Frame sampling + ViT + temporal transformer
- **Gesture**: OpenPose/MediaPipe keypoints with sequence modeling

The shared embedding space is trained via CLIP-style contrastive learning on 400M+ image-text pairs. Cross-modal alignment uses the formula CrossAttention(Q, K, V) = softmax(QK^T / sqrt(d_k))V, where queries come from one modality and keys/values from another.

The specification draws on Kress and van Leeuwen's theory of **modal affordances** — the recognition that different modalities contribute different kinds of meaning (writing conveys precise propositional content, images convey spatial relationships, gesture conveys deictic reference, music conveys emotional evocation). Integration modes are classified as redundancy (reinforcement), complementarity (unique information from each modality), or contradiction (a critical signal for irony and sarcasm detection). The FRESCO framework provides three semiotic levels for visual analysis: plastic (colors, lines, shapes), figurative (entities, objects), and enunciation (point of view, framing).

---

## Meta-Learning and Evolution

The system's adaptability architecture uses **Model-Agnostic Meta-Learning (MAML)** with an outer loop that learns optimal parameter initialization across a distribution of 1000+ tasks, and an inner loop that adapts to new tasks in 3-10 gradient steps. First-Order MAML (omitting the Hessian) provides a 33% speedup with minimal performance loss.

Low-resource language adaptation combines five strategies: multilingual pre-trained language models (mGPT, BLOOM), in-context learning with 5-10 target-language examples, query alignment for cross-lingual transfer, parameter-efficient fine-tuning (LoRA with rank 4-16, adapter bottlenecks of 64-256), and data augmentation through back-translation and synthetic templates. The target is performance within 10% of high-resource languages.

Continual learning integrates six methods to prevent catastrophic forgetting: episodic memory replay (1-2% of data), EWC-style parameter regularization, knowledge distillation on anchor points, sharpness-aware minimization for flat minima, task-specific adapters with gating, and prototypical networks for class-incremental learning. The backward transfer target is less than 5% accuracy drop on Task 1 after learning Task 10.

---

## Dual-Mode Governance

The specification addresses the dual-use nature of powerful language technology through a **RAW/PUBLIC mode architecture**:

| Dimension | PUBLIC Mode | RAW Mode |
|-----------|-------------|----------|
| **Access** | Open to general public | Vetted researchers and institutions |
| **Content Filters** | Strong multi-layered (NSFW, hate speech, misinformation, violence, self-harm) | Configurable, researcher-controlled |
| **Bias Mitigation** | Pre-deployment fairness audits, continuous monitoring | Full exposure of biases for research |
| **Accountability** | Provider + user shared | User/institution full responsibility |
| **Transparency** | AI-generated labels, watermarks | Full system internals |
| **Data Privacy** | GDPR-compliant, data minimization | Anonymized/synthetic data only |
| **Oversight** | Internal ethics teams + incident response | Independent multi-stakeholder ethics council |

PUBLIC mode implements four safety layers: pre-training data curation (quality filtering, bias auditing), safety alignment (RLHF, Constitutional AI principles), runtime filters (prompt shields, output classifiers across four core harm categories with configurable severity thresholds), and human-in-the-loop monitoring. Performance targets: false negative rate below 1%, false positive rate below 5%.

The governance framework aligns with NIST AI RMF 1.0, EU AI Act high-risk system requirements, and ISO/IEC 42001 AI Management System certification. A multi-stakeholder council of technical experts, ethicists, legal scholars, and civil society representatives oversees RAW mode access and adjudicates disputes.

The specification draws on Godber and Origgi's framework for **virtuous persuasion**: rational persuasion (facts, evidence, logic) is encouraged, non-rational persuasion (emotion, ethos) is acceptable when accompanied by rational persuasion, and manipulative persuasion (fallacies, falsehoods) is prohibited. This ethical framework is not bolted on as an afterthought but woven into the system's rhetorical analysis capabilities — the same engine that detects persuasive strategies in input text enforces ethical constraints on generated output.

---

## Technical Architecture

The design corpus specifies a long-horizon production stack. The current repository implements an MVP subset:

- **Runtime**: Python 3.11+, FastAPI for service layer
- **ML Framework**: PyTorch 2.0+ with Hugging Face Transformers
- **Graph Infrastructure**: Neo4j for persistent hypergraph storage, NetworkX for in-memory operations, PyTorch Geometric for graph neural networks
- **Multimodal**: OpenAI CLIP for vision-language alignment, Whisper for speech processing, timm for image models
- **Orchestration**: Kubernetes for deployment, Ray for distributed computation
- **Meta-Learning**: MAML for rapid adaptation to new languages and domains
- **Language Coverage**: 100+ languages targeted, with explicit support tiers

Implemented MVP API endpoints are under `/api/v1/*`, including ingest, analyze, branch evolution, rhetorical analysis, governance evaluation, and hypergraph integrity checks.

The visualization system uses a "Semiotic Garden" metaphor — concepts as plants with size proportional to salience, relations as pathways with style encoding type, layers as depth, and discourse unfolding as growth animation. The interface includes accessibility features: screen reader compatibility (ARIA labels), keyboard navigation, high-contrast mode, and alternative text for all visualizations.

**System requirements** range from development (16 cores, 64GB RAM, 1x A100) to production (64 cores, 256GB RAM, 4x A100/H100) to enterprise scale (100+ GPUs, petabyte storage, global CDN). Training procedures span 12-18 months across four phases: multimodal pre-training, meta-training, safety alignment, and continual adaptation.

---

## Cross-Organ Position

Within the eight-organ system, Nexus Babel Alexandria represents **ORGAN-I at its most ambitious**: a rigorous theoretical corpus now paired with a working MVP scaffold.

The dependency flows are clear:

- **ORGAN-I -> ORGAN-II (Poiesis)**: The plexus architecture provides the theoretical vocabulary for generative art systems. The nine-layer model of linguistic cognition maps onto multi-layered creative processes — a generative music system, for instance, can be understood as operating across phonological (timbral), syntactic (harmonic), semantic (emotional), and pragmatic (performative) layers simultaneously.

- **ORGAN-I -> ORGAN-III (Ergon)**: The 84 function specifications and API design provide blueprints for commercial NLP products. The rhetorical analysis engine, the multilingual processing pipeline, the multimodal integration architecture — each could seed a product vertical. The dual-mode governance framework provides the ethical architecture that commercial deployment requires.

- **ORGAN-I -> ORGAN-IV (Taxis)**: The category-theoretic framework provides a formal model for orchestration systems. Functors between categories, natural transformations between functors — these are precisely the mathematical objects needed to model information flow across organizational boundaries. The plexus architecture itself is a governance model: fully connected, bidirectional, with no single layer claiming authority over the others.

- **ORGAN-I -> ORGAN-V (Logos)**: The specification is itself a contribution to public process — building in public means sharing not just finished products but the theoretical foundations from which products emerge. Essays on computational rhetoric, on the gap between specification and implementation, on the politics of language technology design all flow naturally from this document.

---

## Repository Contents

```
.
├── src/nexus_babel/                             # FastAPI services + models
├── tests/                                       # MVP and hardening tests
├── scripts/                                     # local ingest/load utilities
├── docs/
│   ├── OPERATOR_RUNBOOK.md
│   ├── roadmap.md
│   └── corpus/                                  # original RLOS/ARC4N design documents
└── .github/                                     # workflows, community health files
```

The repository contains both the long-form design documents (in `docs/corpus/`) and implementation code used for the current MVP.

The main specification document is organized in twelve parts: Architectural Foundations, Formal Foundations, The 84 Core Functions, Semiotic Engine, Rhetorical Strategy Engine, Multimodal Architecture, Meta-Learning and Evolution, Dual-Mode Governance, Implementation Specifications, Visualization and Interface, Cultural-Technical System, and Future Directions. The roadmap breaks implementation into 10 phases over 12 months with 200+ atomic tasks, each with explicit dependencies, deliverables, and validation criteria.

**Note on repository hygiene:** The open issues and branches visible on GitHub may include bot-generated suggestions (automated Jules activity). Prioritize committed code and documents in this repository as source of truth.

---

## Related Work

The specification engages with and extends several active research programs:

- **Compositional Distributional Semantics**: Coecke, Sadrzadeh, and Clark (2010) established the DisCoCat framework; RLOS extends it with Frobenius algebras for recursion and density matrices for polysemy.
- **Abstract Meaning Representation**: Banarescu et al. (2013) defined AMR; RLOS extends it to multimodal, rhetorical, and temporal domains.
- **Computational Argumentation**: Stab and Gurevych (2017) established neural argumentation mining; RLOS integrates it with rhetorical analysis and audience modeling.
- **Multimodal NLP**: Baltrusaitis, Ahuja, and Morency (2019) surveyed multimodal ML; RLOS adds semiotic grounding and modal affordance theory.
- **Enhanced RST**: Zeldes et al. (2021) developed graph-based RST; RLOS adopts this as its primary discourse representation.
- **AI Safety and Governance**: Alignment with NIST AI RMF 1.0, EU AI Act, and ISO/IEC 42001 reflects current best practice in responsible AI development.
- **Media Archaeology**: Kittler's *Discourse Networks 1800/1900* (1990) and *Gramophone, Film, Typewriter* (1999) provide the critical media-theoretic frame.

---

## Contributing

This repository has both theory documents and an executable MVP. Contributions that engage either surface are welcome:

- **Theoretical critique**: Identify gaps, inconsistencies, or missed connections in the specification.
- **Formal extensions**: Propose additional categorical structures, semiotic models, or rhetorical formalisms.
- **Implementation prototypes**: Build proof-of-concept implementations of individual functions or subsystems.
- **Cross-linguistic validation**: Assess the architecture's claims about multilingual coverage against specific languages.

### Certainty Artifacts (When to Regenerate)

Regenerate the committed certainty artifacts when a change affects repository truth surfaces, including:

- files or paths included in the repository manifest
- `/api/v1` route modules or documented endpoint references
- `README.md`, `docs/OPERATOR_RUNBOOK.md`, or `docs/roadmap.md`
- generated evidence/reporting scripts under `scripts/`

Commands:

- `make certainty` to regenerate `docs/certainty/*`
- `make certainty-check` to verify committed artifacts are current
- `make verify` to run lint + certainty freshness + tests before a PR

### `uv.lock` Hygiene (When to Regenerate)

Regenerate `~/Workspace/organvm-i-theoria/nexus--babel-alexandria-/uv.lock` when dependency metadata changes, such as:

- `pyproject.toml` dependency/extra additions or version range updates
- intentional lock refreshes or package upgrades
- new tools added to the dev extra that CI/local `uv run` workflows rely on

Do not churn `uv.lock` for pure code/docs/test changes that do not modify dependency declarations.
If you intentionally refresh it, validate with `make verify` before committing.

Please open an issue to discuss substantial contributions before submitting a pull request.

---

## License

[MIT](LICENSE)

The specification itself is released under MIT. The document references CC BY-NC-SA 4.0 for certain future components — the MIT license applies to the current repository contents.

---

## Author

**[@4444J99](https://github.com/4444J99)**

Part of [ORGAN-I: Theoria](https://github.com/organvm-i-theoria) — the theory organ of the [ORGANVM](https://github.com/meta-organvm) system.

<!-- SYSTEM-NAV-START -->

---

<sub>[Portfolio](https://4444j99.github.io/portfolio/) · [System Directory](https://4444j99.github.io/portfolio/directory/) · [ORGAN I · Theoria](https://organvm-i-theoria.github.io/) · Part of the <a href="https://4444j99.github.io/portfolio/directory/">ORGANVM eight-organ system</a></sub>

<!-- SYSTEM-NAV-END -->
