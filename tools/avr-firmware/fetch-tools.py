#!/usr/bin/env python3
"""Fetch the immutable/checksummed dependencies described by sources.lock.json."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

if __name__ == '__main__':
    cache = ROOT / 'downloads'
    cache.mkdir(exist_ok=True)
    for asset in json.loads((ROOT / 'sources.lock.json').read_text())['assets']:
        path = cache / asset['name']
        if path.exists() and digest(path) == asset['sha256']:
            print('Verified cached ' + path.name, flush=True)
            continue
        partial = path.with_suffix(path.suffix + '.partial')
        subprocess.run(['curl', '--fail', '--location', '--retry', '3', '--output', str(partial), asset['url']], check=True)
        if digest(partial) != asset['sha256']: raise SystemExit('Checksum mismatch: ' + str(partial))
        partial.replace(path)
