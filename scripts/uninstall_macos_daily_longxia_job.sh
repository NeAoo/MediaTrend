#!/usr/bin/env bash

set -Eeuo pipefail

LABEL="com.mediatrend.longxia-candidates"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" >/dev/null 2>&1 || true
rm -f "${PLIST_PATH}"

echo "已卸载 macOS 定时任务：${LABEL}"
