#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/mac_daily_longxia_candidates.log"
LOCK_DIR="${PROJECT_DIR}/.daily_longxia_candidates.lock"

mkdir -p "${LOG_DIR}"

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

log() {
  echo "[$(timestamp)] $*"
}

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  log "skip: previous local longxia candidate job still active" | tee -a "${LOG_FILE}"
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
LONGXIA_SSH_TARGET="${LONGXIA_SSH_TARGET:-longxia}"
LONGXIA_REMOTE_CANDIDATE_ROOT="${LONGXIA_REMOTE_CANDIDATE_ROOT:-/home/admin/neo/auto_gongzhonghao/edu_renjiao/research/trend_candidates}"
LONGXIA_CANDIDATE_EXPORT_DIR="${LONGXIA_CANDIDATE_EXPORT_DIR:-${PROJECT_DIR}/output/longxia_trend_candidates}"

{
  log "start local collection for longxia candidates"
  log "project=${PROJECT_DIR}"
  log "python=${PYTHON_BIN}"
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

  log "upload ${CANDIDATE_COUNT} candidate md files to ${LONGXIA_SSH_TARGET}:${REMOTE_DIR}"
  ssh "${LONGXIA_SSH_TARGET}" "mkdir -p '${REMOTE_DIR}'"
  rsync -av --delete "${LOCAL_DIR}/" "${LONGXIA_SSH_TARGET}:${REMOTE_DIR}/"
  log "finish local collection and upload"
} >> "${LOG_FILE}" 2>&1
