#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.mediatrend.longxia-weekly-external-reference"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
RUN_SCRIPT="${PROJECT_DIR}/scripts/run_weekly_longxia_external_reference.sh"
LOG_DIR="${PROJECT_DIR}/logs"

mkdir -p "${HOME}/Library/LaunchAgents" "${LOG_DIR}"
chmod +x "${RUN_SCRIPT}"

cat > "${PLIST_PATH}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUN_SCRIPT}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${PROJECT_DIR}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>0</integer>
    <key>Hour</key>
    <integer>20</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/launchd_weekly_external_reference.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/launchd_weekly_external_reference.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "${PLIST_PATH}"
launchctl enable "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true

echo "已安装 macOS 定时任务：每周日 20:00 运行"
echo "plist: ${PLIST_PATH}"
echo "日志: ${LOG_DIR}/mac_weekly_longxia_external_reference.log"
