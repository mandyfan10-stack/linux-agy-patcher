#!/usr/bin/env bash
set -euo pipefail
BIN="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"

if command -v systemctl >/dev/null 2>&1; then
  systemctl --user disable --now agy-watchdog.timer 2>/dev/null || true
  systemctl --user disable --now agy-watchdog.path 2>/dev/null || true
  systemctl --user stop agy-watchdog.service 2>/dev/null || true
  systemctl --user disable --now agy-cloudcode-proxy.service 2>/dev/null || true
fi
rm -f "$UNIT_DIR/agy-cloudcode-proxy.service" \
      "$UNIT_DIR/agy-watchdog.service" \
      "$UNIT_DIR/agy-watchdog.path" \
      "$UNIT_DIR/agy-watchdog.timer"
pkill -f "$BIN/agy-cloudcode-proxy" 2>/dev/null || true

restore=""
if [[ -f "$BIN/agy.agybak" ]]; then
  restore="$BIN/agy.agybak"
elif [[ -f "$BIN/agy.real.agybak" ]]; then
  restore="$BIN/agy.real.agybak"
elif [[ -f "$BIN/agy.real" ]] && file -b "$BIN/agy.real" | grep -q ELF; then
  restore="$BIN/agy.real"
fi

if [[ -n "$restore" ]]; then
  cp -a "$restore" "$BIN/agy"
  chmod 0755 "$BIN/agy"
  echo "восстановлен $BIN/agy из $restore"
fi

rm -f "$BIN/agy-cloudcode-proxy" "$BIN/agy-repatch" "$BIN/agy-patcher" "$BIN/agy.real" "$BIN/agy-wrapper.tmpl"
echo "прокси, watchdog и обёртка сняты. бэкап *.agybak не удалялся."
