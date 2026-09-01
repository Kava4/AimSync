#!/bin/sh
# Resolve Makcu USB-serial (VID:PID 1A86:55D3) when AIMSYNC_MAKCU_DEVICE is unset.
set -eu

find_makcu_tty() {
  for byid in /dev/serial/by-id/*; do
    [ -e "$byid" ] || continue
    case "$(basename "$byid")" in
      *1A86*|*1a86*|*55D3*|*55d3*|*CH340*|*CH343*|*Makcu*|*makcu*)
        readlink -f "$byid" 2>/dev/null || echo "$byid"
        return 0
        ;;
    esac
  done

  for sysdev in /sys/class/tty/ttyUSB* /sys/class/tty/ttyACM*; do
    [ -e "$sysdev" ] || continue
    uevent="$sysdev/device/uevent"
    [ -f "$uevent" ] || uevent="$sysdev/device/../uevent"
    if [ -f "$uevent" ] && grep -qiE 'PRODUCT=1a86/55d3|PRODUCT=1a86/7523' "$uevent" 2>/dev/null; then
      echo "/dev/$(basename "$sysdev")"
      return 0
    fi
  done

  # Fallback: first USB serial device
  for cand in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do
    if [ -e "$cand" ]; then
      echo "$cand"
      return 0
    fi
  done
  return 1
}

if [ -z "${AIMSYNC_MAKCU_DEVICE:-}" ]; then
  if DEV="$(find_makcu_tty)"; then
    export AIMSYNC_MAKCU_DEVICE="$DEV"
    echo "[entrypoint] AIMSYNC_MAKCU_DEVICE=$AIMSYNC_MAKCU_DEVICE"
  else
    echo "[entrypoint] WARNING: Makcu serial device not found — plug USB and remount device"
  fi
fi

export AIMSYNC_DOCKER="${AIMSYNC_DOCKER:-1}"
export AIMSYNC_HEADLESS="${AIMSYNC_HEADLESS:-1}"
export AIMSYNC_RECOIL_ONLY="${AIMSYNC_RECOIL_ONLY:-1}"
export AIMSYNC_CONFIG_DIR="${AIMSYNC_CONFIG_DIR:-/data}"

if [ -z "${AIMSYNC_LAN_IP:-}" ]; then
  LAN_IP="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "src") { print $(i + 1); exit }}')"
  case "$LAN_IP" in
    172.*) LAN_IP="" ;;
  esac
  if [ -n "$LAN_IP" ]; then
    export AIMSYNC_LAN_IP="$LAN_IP"
    echo "[entrypoint] AIMSYNC_LAN_IP=$AIMSYNC_LAN_IP"
  fi
fi

mkdir -p "$AIMSYNC_CONFIG_DIR"
exec python -u main.py
