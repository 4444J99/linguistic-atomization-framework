# Architecture Diagram Notes

## Purpose

This diagram is the juror-facing overview for the Prix Ars Electronica Digital Humanity submission.
It presents the system as a 9-layer plexus from ingestion through analysis, governance, branching, remix, and artifact output.

## Reading Order

1. Start at Layer 1 (Corpus Ingestion) and follow the main vertical flow down to Layer 9.
2. Use the dashed arrows as cross-cutting data/control flows:
   - Ingestion data entering the analysis plexus
   - Hypergraph references attached to artifacts
   - Governance traces attached to remix artifacts
   - Optional remix-triggered branch break-offs

## Legend

- Solid arrows: primary processing pipeline
- Dashed arrows: cross-cutting references or control links
- "Artifact & Retrieval": persistence + retrieval endpoints + export outputs

## Rendered PNG

- Primary output target: `artifacts/prix-ars-2026/architecture_9_layer_plexus.png`
- Mermaid source of truth: `docs/prix_ars_2026/architecture_9_layer_plexus.mmd`
- Python-rendered PNG fallback script: `scripts/render_architecture_diagram.py`
