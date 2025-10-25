#!/usr/bin/env bash
set -euo pipefail

# ===== Configuration =====
TYPE="OSV"
LANGS="C,C++"

BASE_DIR="$(pwd)"
ARTIFACT_DIR="${BASE_DIR}/artifact"
INPUT_DIR="${ARTIFACT_DIR}/input"
SEED_DIR="${ARTIFACT_DIR}/1-seed"
REPORT_DIR="${ARTIFACT_DIR}/2-report"
PROJECT_DIR="${ARTIFACT_DIR}/3-project"

# ===== Logging =====
log() { echo -e "\033[1;34m[$(date '+%H:%M:%S')] $*\033[0m"; }

# ===== Generate File Name Slug (osv-c-cpp-data.jsonl) =====
to_slug() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -e 's/c++/cpp/g' \
    | tr ',' '-' \
    | tr -d ' ' \
    | sed -E 's/-+/-/g; s/^-+//; s/-+$//'
}
type_slug="$(to_slug "$TYPE")"
langs_slug="$(to_slug "$LANGS")"
base_name="${type_slug}-${langs_slug}-data.jsonl"

seed_out="${SEED_DIR}/${base_name}"
report_out="${REPORT_DIR}/${base_name}"
project_out="${PROJECT_DIR}/${base_name}"

# ===== Main Pipeline =====
log "▶ Running seed stage..."
python -m secb.preprocessor.seed \
  --input-dir "${INPUT_DIR}" \
  --output-file "${seed_out}"

log "▶ Running report stage..."
# Optional batching for report stage to reduce API usage; set REPORT_MAX_ENTRIES to enable
REPORT_OPTS=()
if [[ -n "${REPORT_MAX_ENTRIES:-}" ]]; then
  REPORT_OPTS+=(--max-entries "${REPORT_MAX_ENTRIES}")
fi
python -m secb.preprocessor.report \
  --input-file "${seed_out}" \
  --output-file "${report_out}" \
  --type "${TYPE}" \
  --lang "${LANGS}" \
  --oss-fuzz \
  "${REPORT_OPTS[@]:-}"

log "▶ Running project stage..."
# Make project stage resumable and rate-limit friendly
# - PROJECT_APPEND=1 (default) will append results instead of overwriting
# - PROJECT_MAX_ENTRIES=N limits batch size (e.g., 100)
# - PROJECT_FORCE=1 forces reprocessing of entries marked in tracking
# - PROJECT_SANITIZER_ONLY=1 filters to sanitizer error entries only
PROJECT_OPTS=()
if [[ "${PROJECT_APPEND:-1}" == "1" ]]; then
  PROJECT_OPTS+=(--append)
fi
if [[ -n "${PROJECT_MAX_ENTRIES:-}" ]]; then
  PROJECT_OPTS+=(--max-entries "${PROJECT_MAX_ENTRIES}")
fi
if [[ "${PROJECT_FORCE:-0}" == "1" ]]; then
  PROJECT_OPTS+=(--force)
fi
if [[ "${PROJECT_SANITIZER_ONLY:-0}" == "1" ]]; then
  PROJECT_OPTS+=(--sanitizer-only)
fi
python -m secb.preprocessor.project \
  --input-file "${report_out}" \
  --output-file "${project_out}" \
  "${PROJECT_OPTS[@]:-}"

# ===== Done =====
log "✅ Done."
echo "  Seed:    ${seed_out}"
echo "  Report:  ${report_out}"
echo "  Project: ${project_out}"
