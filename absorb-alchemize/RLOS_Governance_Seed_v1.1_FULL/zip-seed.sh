#!/usr/bin/env bash
set -euo pipefail
ZIP="RLOS_governance_seed_v1.1.zip"
mkdir -p exports
zip -r "exports/$ZIP"   .copilot/config/manifest_full_lineage.yaml   .github/workflows/copilot-governance.yml   .github/workflows/ai-agent-chain.yml   meta/agent_chain.yaml   scripts/checksum.sh   zip_seed.sh
echo "✅ exports/$ZIP"
