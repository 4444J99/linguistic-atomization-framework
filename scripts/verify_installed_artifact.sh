#!/usr/bin/env bash
# Verify a built LingFrame wheel or sdist in an isolated venv outside the checkout.
# Usage: verify_installed_artifact.sh <artifact.whl|artifact.tar.gz> <sample.txt>
set -euo pipefail

ARTIFACT="${1:?artifact path required}"
SAMPLE="${2:?sample text path required}"
ARTIFACT="$(cd "$(dirname "$ARTIFACT")" && pwd)/$(basename "$ARTIFACT")"
SAMPLE="$(cd "$(dirname "$SAMPLE")" && pwd)/$(basename "$SAMPLE")"

if [[ ! -f "$ARTIFACT" ]]; then
  echo "ERROR: artifact not found: $ARTIFACT" >&2
  exit 1
fi
if [[ ! -f "$SAMPLE" ]]; then
  echo "ERROR: sample not found: $SAMPLE" >&2
  exit 1
fi

WORK="$(mktemp -d /tmp/lingframe-verify-XXXXXX)"
VENV="$WORK/venv"
RUNDIR="$WORK/rundir"
NBDIR="$WORK/notebooks"
REPORT="$WORK/report.html"
QUICK_OUT="$WORK/quick.out"
ANALYZE_OUT="$WORK/analyze.out"

cleanup() { rm -rf "$WORK"; }
# Keep artifacts on failure for CI logs; always remove venv tree at end via EXIT.
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$RUNDIR" "$NBDIR"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install "$ARTIFACT"

LF="$VENV/bin/lingframe"
test -x "$LF"

# Leave the checkout entirely so site-packages (not the source tree) resolve imports.
cd "$RUNDIR"

echo "== --version =="
"$LF" --version | tee "$WORK/version.out"
grep -E 'lingframe[[:space:]]+1\.' "$WORK/version.out"

echo "== list-modules =="
"$LF" list-modules | tee "$WORK/modules.out"
grep -q 'Available Analysis Modules' "$WORK/modules.out"
grep -q 'semantic' "$WORK/modules.out"
grep -q 'evaluation' "$WORK/modules.out"

echo "== list-projects =="
"$LF" list-projects | tee "$WORK/projects.out"
grep -q 'Available Projects' "$WORK/projects.out"
grep -q 'tomb-unknowns' "$WORK/projects.out"
grep -q 'MET4MORFOSES' "$WORK/projects.out"

echo "== init-notebooks =="
"$LF" init-notebooks --dir "$NBDIR" | tee "$WORK/notebooks.out"
test -f "$NBDIR/exploration.ipynb"
test -f "$NBDIR/evaluation.ipynb"
test -f "$NBDIR/visualization.ipynb"
grep -q 'Notebooks initialized' "$WORK/notebooks.out"

echo "== quick (functional) =="
"$LF" quick "$SAMPLE" -t "Sample Rhetoric" | tee "$QUICK_OUT"
grep -q 'Quick Analysis: Sample Rhetoric' "$QUICK_OUT"
grep -q 'By Phase:' "$QUICK_OUT"
# Score line must include a numeric percentage (marker-density indicator, not a writing-quality grade).
grep -Eq 'Overall Score:[[:space:]]*[0-9]+%' "$QUICK_OUT"
# Friendly phase labels from framework.output.terminology (not raw logos/pathos keys).
grep -Eq 'Rhetorical Analysis|Checking Consistency|Finding Vulnerabilities|Discovering Opportunities' "$QUICK_OUT"
grep -q 'Top Recommendations:' "$QUICK_OUT"

echo "== analyze (functional) =="
"$LF" analyze "$SAMPLE" -t "Sample Rhetoric" -o "$REPORT" --no-open | tee "$ANALYZE_OUT"
grep -q 'Analysis complete!' "$ANALYZE_OUT"
grep -q "Report: $REPORT" "$ANALYZE_OUT"
test -s "$REPORT"
grep -qi 'html' "$REPORT"
grep -q 'Sample Rhetoric' "$REPORT"

echo "OK: isolated verify passed for $(basename "$ARTIFACT")"
