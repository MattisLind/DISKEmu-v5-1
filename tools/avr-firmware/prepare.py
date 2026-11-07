#!/usr/bin/env python3
"""Verify vendor inputs and install only the assembler, shared source and device definitions."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import zipfile

if __name__ == '__main__':
    cache = Path(sys.argv[1])
    root = Path(__file__).resolve().parent
    for asset in json.loads((root / 'sources.lock.json').read_text())['assets']:
        path = cache / asset['name']
        if hashlib.sha256(path.read_bytes()).hexdigest() != asset['sha256']:
            raise SystemExit('Checksum mismatch: ' + str(path))
    shutil.copyfile(cache / 'avrasm2.exe', root / 'avrasm2.exe')
    include = root / 'include'
    include.mkdir()
    with tarfile.open(cache / 'include.tar.gz') as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts: continue
            target = include.joinpath(*parts)
            if not target.resolve().is_relative_to(include.resolve()): raise ValueError('Unsafe source archive path')
            if member.isdir(): target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
            else: raise ValueError('Unsupported archive entry: ' + member.name)
    definitions = root / 'device'
    definitions.mkdir()
    with zipfile.ZipFile(cache / 'Microchip.AVR-Dx_DFP.2.8.343.atpack') as pack:
        definitions.joinpath('AVR128DB48def.inc').write_bytes(pack.read('avrasm/inc/AVR128DB48def.inc'))
        for name in pack.namelist():
            if len(Path(name).parts) == 1 and Path(name).name.lower().startswith('license'):
                definitions.joinpath(Path(name).name).write_bytes(pack.read(name))
