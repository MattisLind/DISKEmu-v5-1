#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
exec docker run --rm --init --platform linux/amd64 \
    --env SOURCE_DATE_EPOCH \
    --mount "type=bind,source=$root,target=/src" \
    "${AVR_FIRMWARE_IMAGE:-diskemu-avr:1}" "$@"
