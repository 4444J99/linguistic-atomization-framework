from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Mode = Literal["RAW", "PUBLIC"]
ExecutionMode = Literal["sync", "async", "shadow"]
RemixStrategy = Literal["interleave", "thematic_blend", "temporal_layer", "glyph_collide"]
MergeStrategy = Literal["left_wins", "right_wins", "interleave"]


class GlyphSeed(BaseModel):
    """Rich glyph-seed: active generative glyph matter with metadata."""

    character: str
    unicode_name: str
    phoneme_hint: str | None = None
    historic_forms: list[str] = Field(default_factory=list)
    visual_mutations: list[str] = Field(default_factory=list)
    thematic_tags: list[str] = Field(default_factory=list)
    future_seeds: list[str] = Field(default_factory=list)
    position: int


class IngestBatchRequest(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    parse_options: dict[str, Any] = Field(default_factory=dict)
    atom_tracks: list[str] | None = None


class IngestBatchResponse(BaseModel):
    ingest_job_id: str
    documents_ingested: int
    documents_unchanged: int = 0
    atoms_created: int
    provenance_digest: str
    ingest_scope: str = "partial"
    warnings: list[str] = Field(default_factory=list)


class IngestFileStatus(BaseModel):
    path: str
    status: str
    document_id: str | None = None
    error: str | None = None


class IngestJobResponse(BaseModel):
    ingest_job_id: str
    status: str
    files: list[IngestFileStatus]
    errors: list[str]
    documents_ingested: int
    documents_unchanged: int = 0
    atoms_created: int
    provenance_digest: str
    ingest_scope: str = "partial"
    warnings: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    document_id: str | None = None
    branch_id: str | None = None
    layers: list[str] = Field(default_factory=list)
    mode: Mode = "PUBLIC"
    execution_mode: ExecutionMode = "sync"
    plugin_profile: str | None = None


class AnalyzeResponse(BaseModel):
    analysis_run_id: str | None = None
    mode: Mode
    layers: dict[str, Any]
    confidence_bundle: dict[str, float]
    hypergraph_ids: dict[str, Any]
    plugin_provenance: dict[str, Any] = Field(default_factory=dict)
    job_id: str | None = None
    status: str = "completed"


class EvolveBranchRequest(BaseModel):
    parent_branch_id: str | None = None
    root_document_id: str | None = None
    event_type: str
    event_payload: dict[str, Any] = Field(default_factory=dict)
    mode: Mode = "PUBLIC"


class EvolveBranchResponse(BaseModel):
    new_branch_id: str
    event_id: str
    diff_summary: dict[str, Any]


class MultiEvolveEventInput(BaseModel):
    event_type: str
    event_payload: dict[str, Any] = Field(default_factory=dict)


class MultiEvolveRequest(BaseModel):
    parent_branch_id: str | None = None
    root_document_id: str | None = None
    events: list[MultiEvolveEventInput] = Field(default_factory=list)
    mode: Mode = "PUBLIC"


class MultiEvolveResponse(BaseModel):
    branch_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    final_branch_id: str
    event_count: int
    final_text_hash: str
    final_preview: str


class MergeBranchesRequest(BaseModel):
    left_branch_id: str
    right_branch_id: str
    strategy: MergeStrategy = "interleave"
    mode: Mode = "PUBLIC"


class MergeBranchesResponse(BaseModel):
    new_branch_id: str
    event_id: str
    strategy: MergeStrategy
    lca_branch_id: str | None = None
    conflict_semantics: dict[str, Any] = Field(default_factory=dict)
    diff_summary: dict[str, Any] = Field(default_factory=dict)


class BranchEventView(BaseModel):
    branch_id: str
    event_id: str
    event_index: int
    event_type: str
    event_payload: dict[str, Any]
    diff_summary: dict[str, Any]
    created_at: datetime


class BranchTimelineResponse(BaseModel):
    branch_id: str
    root_document_id: str | None
    events: list[BranchEventView]
    replay_snapshot: dict[str, Any]


class BranchVisualizationNode(BaseModel):
    id: str
    kind: str
    branch_id: str
    lineage_role: str = "primary"
    parent_branch_id: str | None = None
    root_document_id: str | None = None
    event_index: int
    event_type: str
    phase: str | None = None
    mode: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class BranchVisualizationEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BranchVisualizationSummary(BaseModel):
    event_count: int
    edge_count: int
    lineage_depth: int
    secondary_lineage_branch_count: int = 0
    merge_secondary_edge_count: int = 0


class BranchVisualizationResponse(BaseModel):
    branch_id: str
    root_document_id: str | None = None
    nodes: list[BranchVisualizationNode] = Field(default_factory=list)
    edges: list[BranchVisualizationEdge] = Field(default_factory=list)
    summary: BranchVisualizationSummary


class RhetoricalAnalysisRequest(BaseModel):
    text: str | None = None
    document_id: str | None = None
    audience_profile: dict[str, Any] = Field(default_factory=dict)


class RhetoricalAnalysisResponse(BaseModel):
    ethos_score: float
    pathos_score: float
    logos_score: float
    strategies: list[str]
    fallacies: list[str]
    explainability: dict[str, Any]


class GovernanceEvaluateRequest(BaseModel):
    candidate_output: str
    mode: Mode = "PUBLIC"


class GovernanceEvaluateResponse(BaseModel):
    allow: bool
    policy_hits: list[str]
    redactions: list[str]
    audit_id: str
    decision_trace: dict[str, Any] = Field(default_factory=dict)


class JobSubmitRequest(BaseModel):
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    execution_mode: ExecutionMode = "async"
    idempotency_key: str | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str
    job_type: str
    execution_mode: ExecutionMode


class JobAttemptView(BaseModel):
    attempt_number: int
    status: str
    error_text: str | None = None
    runtime_ms: int | None = None
    started_at: datetime
    finished_at: datetime | None = None


class JobArtifactView(BaseModel):
    artifact_type: str
    artifact_ref: str | None = None
    artifact_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error_text: str | None = None
    execution_mode: ExecutionMode
    idempotency_key: str | None = None
    max_attempts: int
    attempt_count: int
    next_run_at: datetime
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    attempts: list[JobAttemptView] = Field(default_factory=list)
    artifacts: list[JobArtifactView] = Field(default_factory=list)


class AnalysisRunResponse(BaseModel):
    analysis_run_id: str
    document_id: str | None = None
    branch_id: str | None = None
    mode: Mode
    execution_mode: ExecutionMode
    plugin_profile: str | None = None
    layers: list[str] = Field(default_factory=list)
    confidence_bundle: dict[str, float] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    layer_outputs: list[dict[str, Any]] = Field(default_factory=list)


class BranchReplayResponse(BaseModel):
    branch_id: str
    event_count: int
    text_hash: str
    preview: str
    replay_snapshot: dict[str, Any] = Field(default_factory=dict)


class BranchCompareResponse(BaseModel):
    left_branch_id: str
    right_branch_id: str
    left_hash: str
    right_hash: str
    distance: int
    same: bool
    preview_left: str
    preview_right: str


class RemixRequest(BaseModel):
    source_document_id: str | None = None
    source_branch_id: str | None = None
    target_document_id: str | None = None
    target_branch_id: str | None = None
    strategy: RemixStrategy = "interleave"
    seed: int = 0
    mode: Mode = "PUBLIC"


class RemixResponse(BaseModel):
    new_branch_id: str
    event_id: str
    strategy: str
    diff_summary: dict[str, Any]


class RemixAtomRef(BaseModel):
    atom_id: str
    atom_level: str
    ordinal: int
    role: str


class RemixComposeRequest(BaseModel):
    source_document_id: str | None = None
    source_branch_id: str | None = None
    target_document_id: str | None = None
    target_branch_id: str | None = None
    strategy: RemixStrategy = "interleave"
    seed: int = 0
    mode: Mode = "PUBLIC"
    atom_levels: list[str] = Field(default_factory=list)
    create_branch: bool = True
    persist_artifact: bool = True


class RemixComposeResponse(BaseModel):
    strategy: str
    seed: int
    mode: Mode
    remixed_text: str
    text_hash: str
    payload_hash: str
    source_atom_refs: list[RemixAtomRef] = Field(default_factory=list)
    remix_artifact_id: str | None = None
    governance_decision_id: str | None = None
    governance_trace: dict[str, Any] = Field(default_factory=dict)
    create_branch: bool = True
    new_branch_id: str | None = None
    event_id: str | None = None
    diff_summary: dict[str, Any] = Field(default_factory=dict)


class RemixSourceLinkView(BaseModel):
    role: str
    document_id: str | None = None
    branch_id: str | None = None
    atom_level: str | None = None
    atom_count: int = 0
    atom_refs: list[dict[str, Any]] = Field(default_factory=list)


class RemixArtifactResponse(BaseModel):
    remix_artifact_id: str
    strategy: str
    seed: int
    mode: Mode
    remixed_text: str
    text_hash: str
    payload_hash: str
    rng_seed_hex: str
    create_branch: bool
    source_document_id: str | None = None
    source_branch_id: str | None = None
    target_document_id: str | None = None
    target_branch_id: str | None = None
    branch_id: str | None = None
    branch_event_id: str | None = None
    governance_decision_id: str | None = None
    governance_trace: dict[str, Any] = Field(default_factory=dict)
    lineage_graph_refs: dict[str, Any] = Field(default_factory=dict)
    source_links: list[RemixSourceLinkView] = Field(default_factory=list)
    created_at: datetime


class RemixArtifactListItem(BaseModel):
    remix_artifact_id: str
    strategy: str
    seed: int
    mode: Mode
    text_hash: str
    create_branch: bool
    branch_id: str | None = None
    governance_decision_id: str | None = None
    source_document_id: str | None = None
    target_document_id: str | None = None
    created_at: datetime


class RemixArtifactListResponse(BaseModel):
    remixes: list[RemixArtifactListItem] = Field(default_factory=list)
    total: int
    offset: int
    limit: int


class SeedTextEntry(BaseModel):
    title: str
    author: str
    language: str
    source_url: str
    local_path: str | None = None
    atomization_status: str = "not_provisioned"


class SeedTextListResponse(BaseModel):
    seeds: list[SeedTextEntry]


class SeedProvisionRequest(BaseModel):
    title: str


class SeedProvisionResponse(BaseModel):
    title: str
    status: str
    local_path: str | None = None
    document_id: str | None = None
