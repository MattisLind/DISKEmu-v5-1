#!/usr/bin/env python3
"""Compare fresh builds of both variants; listings/debug files contain wall-clock dates."""
import argparse
import hashlib
import json
from pathlib import Path

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('first', type=Path)
    p.add_argument('second', type=Path)
    args = p.parse_args()
    for variant in ('mscp', 'rlv12'):
        stem = 'diskemu-' + variant
        for directory in (args.first, args.second):
            manifest = json.loads((directory / variant / (stem + '.json')).read_text())
            for name, digest in manifest['images_sha256'].items():
                if hashlib.sha256((directory / variant / name).read_bytes()).hexdigest() != digest:
                    raise SystemExit('Image does not match its manifest: ' + str(directory / variant / name))
        for suffix in ('.hex', '.bin'):
            first, second = (directory / variant / (stem + suffix) for directory in (args.first, args.second))
            if first.read_bytes() != second.read_bytes(): raise SystemExit('Images differ: ' + first.name)
            print(first.name + ': byte-identical, SHA256 ' + hashlib.sha256(first.read_bytes()).hexdigest())
