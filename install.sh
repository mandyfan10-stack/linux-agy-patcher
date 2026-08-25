#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"

mkdir -p "$BIN" "$UNIT_DIR"

agy_path="$(command -v agy 2>/dev/null || true)"
if [[ -z "$agy_path" && -x "$BIN/agy" ]]; then
  agy_path="$BIN/agy"
fi
if [[ -z "$agy_path" ]]; then
  echo "agy не найден. Установите CLI: curl -fsSL https://antigravity.google/cli/install.sh | bash" >&2
  exit 1
fi

if file -b "$agy_path" | grep -q ELF; then
  :
elif [[ -x "$BIN/agy.real" ]]; then
  agy_path="$BIN/agy.real"
else
  echo "ожидался ELF agy, сейчас: $agy_path ($(file -b "$agy_path"))" >&2
  exit 1
fi

install -m 0755 "$ROOT/bin/agy-cloudcode-proxy" "$BIN/agy-cloudcode-proxy"
install -m 0755 "$ROOT/bin/agy-repatch" "$BIN/agy-repatch"
install -m 0755 "$ROOT/bin/agy-patcher" "$BIN/agy-patcher"
install -m 0644 "$ROOT/systemd/agy-cloudcode-proxy.service" "$UNIT_DIR/agy-cloudcode-proxy.service"
install -m 0644 "$ROOT/systemd/agy-watchdog.service" "$UNIT_DIR/agy-watchdog.service"
install -m 0644 "$ROOT/systemd/agy-watchdog.path" "$UNIT_DIR/agy-watchdog.path"

if [[ "$(readlink -f "$agy_path")" != "$(readlink -f "$BIN/agy.real")" ]]; then
  if [[ -f "$BIN/agy.real" ]] && file -b "$BIN/agy.real" | grep -q ELF; then
    :
  else
    cp -a "$agy_path" "$BIN/agy.real"
  fi
fi

AGY_BIN="$BIN/agy.real" "$BIN/agy-repatch"

if command -v loginctl >/dev/null 2>&1; then
  loginctl enable-linger "$USER" >/dev/null 2>&1 || true
fi

if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload
  systemctl --user enable agy-cloudcode-proxy.service
  systemctl --user restart agy-cloudcode-proxy.service
  systemctl --user enable --now agy-watchdog.path
fi

echo
"$BIN/agy-patcher" status || true
echo
echo "Проверка CloudCode через прокси..."
"$BIN/agy-patcher" probe || true
echo
echo "Готово. Если agy уже запущен — закройте и откройте снова."
echo "После 'agy update' watchdog перепатчит сам; иначе: agy-repatch"
echo "Статус: agy-patcher status"
