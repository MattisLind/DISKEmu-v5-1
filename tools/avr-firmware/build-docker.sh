#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 "$root/fetch-tools.py"
exec docker build --platform linux/amd64 -t "${AVR_FIRMWARE_IMAGE:-diskemu-avr:1}" "$@" "$root"
