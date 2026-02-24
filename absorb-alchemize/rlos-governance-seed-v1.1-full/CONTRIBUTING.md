# Contributing to RE:GE_OS_RHETORICAL_LINGUISTICS

Thank you for contributing to the RLOS project.  
All work follows the **RAW → PUBLIC** development lifecycle.

## 🧠 Commit Rules

1. **Always reference a UFNS ID** in your commit message.
2. **No direct pushes to `main`** — use PRs from `raw/feature-*` or `public/update-*`.
3. **Semantic versioning**: Major / Minor / Patch.
4. **Run checks before commit**: `scripts/checksum.sh && pytest tests/`.
5. **Do not edit** `.copilot/config/manifest_full_lineage.yaml` manually.

## 🌐 AI-Collaborator Etiquette
- Each AI agent writes to its own namespace.
- Handoffs use `meta/agent_chain.yaml`.
- Logs are hashed for privacy.

## 🔒 Security & Compliance
- No PII or secrets in commits.
- PUBLIC builds undergo redaction automatically.
