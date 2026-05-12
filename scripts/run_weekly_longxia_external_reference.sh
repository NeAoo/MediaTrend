#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
JOB_LOG_FILE="${LOG_DIR}/mac_weekly_longxia_external_reference.log"
LOCK_DIR="${PROJECT_DIR}/.weekly_longxia_external_reference.lock"

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
  log "skip: previous weekly external_reference job still active" | tee -a "${JOB_LOG_FILE}"
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
LOCAL_OUTPUT_ROOT="${LONGXIA_WEEKLY_EXTERNAL_REFERENCE_EXPORT_DIR:-${PROJECT_DIR}/output/longxia_weekly_external_reference}"
REMOTE_ROOT="${LONGXIA_REMOTE_EXTERNAL_REFERENCE_ROOT:-}"
SCORED_DIR="${LONGXIA_WEEKLY_EXTERNAL_REFERENCE_SCORED_DIR:-${PROJECT_DIR}/scored_data}"

{
  log "start weekly external_reference package build"
  log "project=${PROJECT_DIR}"
  log "python=${PYTHON_BIN}"
  require_env LONGXIA_SSH_TARGET
  require_env LONGXIA_REMOTE_EXTERNAL_REFERENCE_ROOT
  export PYTHONUNBUFFERED=1

  if [ ! -x "${PYTHON_BIN}" ]; then
    log "error: python not executable: ${PYTHON_BIN}"
    exit 1
  fi

  WEEK_INFO="$("${PYTHON_BIN}" - <<'PY'
from datetime import date, timedelta
today = date.today()
this_monday = today - timedelta(days=today.weekday())
# The launchd job runs on Sunday evening, before OpenClaw reads the package on
# Monday morning. On Sunday, build the week that is ending today; on any other
# day, build the previous complete Monday-Sunday week.
if today.weekday() == 6:
    start = this_monday
    end = today
else:
    start = this_monday - timedelta(days=7)
    end = start + timedelta(days=6)
print(start.isoformat(), end.isoformat(), f"{start.isoformat()}_to_{end.isoformat()}")
PY
)"
  read -r WEEK_START WEEK_END WEEK_ID <<< "${WEEK_INFO}"

  log "week=${WEEK_ID}"
  LOCAL_DIR="${LOCAL_OUTPUT_ROOT}/${WEEK_ID}"
  REMOTE_DIR="${REMOTE_ROOT}/${WEEK_ID}"

  if [ -d "${LOCAL_DIR}" ] && "${PYTHON_BIN}" - "${LOCAL_DIR}" "${WEEK_START}" "${WEEK_END}" <<'PY'
import sys
from datetime import datetime
from pathlib import Path

from formatters.weekly_external_reference import validate_package

package_dir = Path(sys.argv[1])
week_start = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
week_end = datetime.strptime(sys.argv[3], "%Y-%m-%d").date()
errors = validate_package(package_dir, week_start, week_end)
if errors:
    for error in errors:
        print(error)
    raise SystemExit(1)
PY
  then
    LOCAL_MANIFEST_HASH="$("${PYTHON_BIN}" -c 'from pathlib import Path; import hashlib, sys; print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())' "${LOCAL_DIR}/manifest.json")"
    REMOTE_MANIFEST_HASH="$(ssh "${LONGXIA_SSH_TARGET}" "test -s '${REMOTE_DIR}/manifest.json' && test -s '${REMOTE_DIR}/ranked_articles.json' && test -s '${REMOTE_DIR}/top2/01.md' && test -s '${REMOTE_DIR}/top2/02.md' && test -s '${REMOTE_DIR}/last1/01.md' && python3 -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path(\"'${REMOTE_DIR}'/manifest.json\").read_bytes()).hexdigest())'" || true)"
    if [ "${REMOTE_MANIFEST_HASH}" = "${LOCAL_MANIFEST_HASH}" ]; then
      log "skip: local and remote weekly external_reference package already valid"
      exit 0
    fi
  fi

  "${PYTHON_BIN}" -u "${PROJECT_DIR}/scripts/build_weekly_external_reference.py" \
    --scored-dir "${SCORED_DIR}" \
    --output-root "${LOCAL_OUTPUT_ROOT}" \
    --week-start "${WEEK_START}" \
    --week-end "${WEEK_END}"

  if [ ! -s "${LOCAL_DIR}/manifest.json" ]; then
    log "error: manifest not found or empty: ${LOCAL_DIR}/manifest.json"
    exit 1
  fi
  if [ ! -s "${LOCAL_DIR}/ranked_articles.json" ]; then
    log "error: ranked_articles not found or empty: ${LOCAL_DIR}/ranked_articles.json"
    exit 1
  fi

  log "upload weekly external_reference package to ${LONGXIA_SSH_TARGET}:${REMOTE_DIR}"
  ssh "${LONGXIA_SSH_TARGET}" "mkdir -p '${REMOTE_DIR}'"
  rsync -av --delete "${LOCAL_DIR}/" "${LONGXIA_SSH_TARGET}:${REMOTE_DIR}/"
  log "finish weekly external_reference upload"
} >> "${JOB_LOG_FILE}" 2>&1
