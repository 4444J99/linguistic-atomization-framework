#!/usr/bin/env bash
set -euo pipefail
mf=".copilot/config/manifest_full_lineage.yaml"
sha=$(python - <<'PY'
import hashlib, sys
p=sys.argv[1]
print(hashlib.sha256(open(p,"rb").read()).hexdigest())
PY
"$mf")
echo "SHA256: $sha"
