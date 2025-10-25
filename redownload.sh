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

# ===== Directory Setup (overwrite allowed) =====
log "▶ Creating directories..."
mkdir -p "$INPUT_DIR" "$SEED_DIR" "$REPORT_DIR" "$PROJECT_DIR"

# ===== Download and Extract OSV Dataset =====
log "▶ Downloading OSV dataset..."
curl -L -o "${INPUT_DIR}/all.zip" "https://storage.googleapis.com/osv-vulnerabilities/all.zip"

log "▶ Unzipping dataset into ${INPUT_DIR}..."
unzip -q -o "${INPUT_DIR}/all.zip" -d "${INPUT_DIR}"
rm -f "${INPUT_DIR}/all.zip"