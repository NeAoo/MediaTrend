#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
JOB_LOG_FILE="${LOG_DIR}/mac_daily_longxia_candidates.log"
LOCK_DIR="${PROJECT_DIR}/.daily_longxia_candidates.lock"

mkdir -p "${LOG_DIR}"

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

log() {
  echo "[$(timestamp)] $*"
}

require_env() {
  local name="$1"
  local value="${!name:-}"
  if [ -z "${value}" ]; then
    log "error: ${name} must be set in .env or environment for private remote upload"
    exit 1
  fi
}

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  log "skip: previous local longxia candidate job still active" | tee -a "${JOB_LOG_FILE}"
  exit 0
fi

cleanup() {
  rmdir "${LOCK_DIR}" 2>/dev/null || true
}
trap cleanup EXIT

cd "${PROJECT_DIR}"

if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.env"
  set +a
fi

export TZ="${LONGXIA_CANDIDATE_TIMEZONE:-Asia/Shanghai}"

PYTHON_BIN="${PYTHON_BIN:-${PROJECT_DIR}/.venv/bin/python}"
LONGXIA_SSH_TARGET="${LONGXIA_SSH_TARGET:-}"
LONGXIA_REMOTE_CANDIDATE_ROOT="${LONGXIA_REMOTE_CANDIDATE_ROOT:-}"
LONGXIA_REMOTE_SCORED_ROOT="${LONGXIA_REMOTE_SCORED_ROOT:-}"
LONGXIA_CANDIDATE_EXPORT_DIR="${LONGXIA_CANDIDATE_EXPORT_DIR:-${PROJECT_DIR}/output/longxia_trend_candidates}"
LONGXIA_SCORED_DATA_DIR="${LONGXIA_SCORED_DATA_DIR:-${PROJECT_DIR}/scored_data}"

{
  log "start local collection for longxia candidates"
  log "project=${PROJECT_DIR}"
  log "python=${PYTHON_BIN}"
  require_env LONGXIA_SSH_TARGET
  require_env LONGXIA_REMOTE_CANDIDATE_ROOT
  require_env LONGXIA_REMOTE_SCORED_ROOT
  export PYTHONUNBUFFERED=1

  if [ ! -x "${PYTHON_BIN}" ]; then
    log "error: python not executable: ${PYTHON_BIN}"
    exit 1
  fi

  "${PYTHON_BIN}" -u "${PROJECT_DIR}/main.py" run

  DATE_LABEL="$(date +%F)"
  LOCAL_DIR="${LONGXIA_CANDIDATE_EXPORT_DIR}/${DATE_LABEL}"
  REMOTE_DIR="${LONGXIA_REMOTE_CANDIDATE_ROOT}/${DATE_LABEL}"

  if [ ! -d "${LOCAL_DIR}" ]; then
    log "error: candidate directory not found: ${LOCAL_DIR}"
    exit 1
  fi

  CANDIDATE_COUNT="$(find "${LOCAL_DIR}" -maxdepth 1 -type f -name "${DATE_LABEL}_*.md" -size +0c | wc -l | tr -d ' ')"
  if [ "${CANDIDATE_COUNT}" -lt 1 ]; then
    log "error: no non-empty candidate md files in ${LOCAL_DIR}"
    exit 1
  fi

  DATE_STAMP="$(date +%Y%m%d)"
  if [ ! -d "${LONGXIA_SCORED_DATA_DIR}" ]; then
    log "error: scored data directory not found: ${LONGXIA_SCORED_DATA_DIR}"
    exit 1
  fi
  SCORED_FILE="$(find "${LONGXIA_SCORED_DATA_DIR}" -maxdepth 1 -type f -name "merged_hotspots_${DATE_STAMP}_*.json" -size +0c -print | sort | tail -n 1)"
  if [ -z "${SCORED_FILE}" ]; then
    log "error: scored data file not found for ${DATE_STAMP} in ${LONGXIA_SCORED_DATA_DIR}"
    exit 1
  fi

  SCORED_COUNT="$("${PYTHON_BIN}" - "${SCORED_FILE}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8-sig"))
hotspots = data.get("hotspots")
if not isinstance(hotspots, list) or not hotspots:
    raise SystemExit("scored data has no hotspots")

def is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False

scored_count = 0
required_dimensions = (
    "heat",
    "authority",
    "quality",
    "resonance",
    "timeliness",
    "reference_value",
    "risk_control",
)
for index, item in enumerate(hotspots, start=1):
    if not isinstance(item, dict):
        raise SystemExit(f"hotspot #{index} is not an object")
    if not is_number(item.get("score")):
        raise SystemExit(f"hotspot #{index} missing numeric score")
    score_details = item.get("score_details")
    if not isinstance(score_details, dict):
        raise SystemExit(f"hotspot #{index} missing score_details")
    for dimension in required_dimensions:
        if not is_number(score_details.get(dimension)):
            raise SystemExit(f"hotspot #{index} missing numeric score_details.{dimension}")
    scored_count += 1

print(scored_count)
PY
)"
  if [ "${SCORED_COUNT}" -lt 1 ]; then
    log "error: scored data validation returned zero items: ${SCORED_FILE}"
    exit 1
  fi

  log "upload ${CANDIDATE_COUNT} candidate md files to ${LONGXIA_SSH_TARGET}:${REMOTE_DIR}"
  ssh "${LONGXIA_SSH_TARGET}" "mkdir -p '${REMOTE_DIR}'"
  rsync -av --delete "${LOCAL_DIR}/" "${LONGXIA_SSH_TARGET}:${REMOTE_DIR}/"
  REMOTE_SCORED_DIR="${LONGXIA_REMOTE_SCORED_ROOT}/${DATE_LABEL}"
  log "upload scored data (${SCORED_COUNT} items) to ${LONGXIA_SSH_TARGET}:${REMOTE_SCORED_DIR}"
  ssh "${LONGXIA_SSH_TARGET}" "mkdir -p '${REMOTE_SCORED_DIR}'"
  rsync -av "${SCORED_FILE}" "${LONGXIA_SSH_TARGET}:${REMOTE_SCORED_DIR}/"
  log "finish local collection and upload"
} >> "${JOB_LOG_FILE}" 2>&1
