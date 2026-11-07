#!/usr/bin/env python3
"""Assemble both DISKEmu AVR128DB48 personalities without modifying sources."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from ihex import FLASH_SIZE, EEPROM_SIZE, SRAM_START, SRAM_END, read_hex, flash_binary, reset_target

TOOLS = Path('/opt/avr')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(source, *args):
    result = subprocess.run(['git', '-c', f'safe.directory={source}', '-C', str(source), *args], text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def winpath(path):
    return subprocess.check_output(['winepath', '-w', str(path)], text=True).strip()


def map_symbols(path):
    return {name: (kind, int(value, 16)) for kind, name, value in
            re.findall(r'^(EQU|CSEG|DSEG)\s+(\S+)\s+([0-9a-fA-F]+)\s*$', path.read_text(), re.M)}


def validate(hex_file, map_file, output, date, clock, version):
    memory = read_hex(hex_file)
    image = flash_binary(memory)
    symbols = map_symbols(map_file)
    required = {'SIGNATURE_000': 0x1e, 'SIGNATURE_001': 0x97, 'SIGNATURE_002': 0x0c,
                'SRAM_START': SRAM_START, 'RAMEND': SRAM_END - 1, 'F_CPU': 24000000, 'F_CLK': 0x24}
    for name, expected in required.items():
        if symbols.get(name, (None, None))[1] != expected: raise ValueError('Unexpected device/clock definition: ' + name)
    target = reset_target(memory)
    if symbols['start'] != ('CSEG', target): raise ValueError('Reset vector does not jump to start')
    if not (0x10000 in memory): raise ValueError('Missing mapped-flash constant tables at byte address 0x10000')
    segments = {}
    for name, start, end, code, data, used, capacity, percent in re.findall(
            r'^\[\.(\w+)\]\s+(0x[\da-fA-F]+)\s+(0x[\da-fA-F]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%', output, re.M):
        segments[name] = {'start': int(start, 16), 'end': int(end, 16), 'used': int(used), 'capacity': int(capacity)}
    if set(segments) != {'cseg', 'dseg', 'eseg'}: raise ValueError('Assembler memory summary missing')
    if segments['cseg']['capacity'] != FLASH_SIZE or segments['cseg']['used'] != len(memory):
        raise ValueError('Flash image disagrees with assembler memory summary')
    ram = segments['dseg']
    if ram['capacity'] != SRAM_END - SRAM_START or not (SRAM_START <= ram['start'] <= ram['end'] < 0x5000):
        raise ValueError('Static SRAM overlaps reserved monitor/heap/logging space')
    banner = f'Universal Disk Emulator V5-1 {date} {clock}'.encode()
    if banner not in image or version.encode() not in image: raise ValueError('Build timestamp/version missing from firmware')
    return image, dict(segments=segments, programmed_bytes=len(memory), highest_flash_address=max(memory),
                       reset_target_word=target, device_signature='1e970c', cpu_hz=24000000)


def assemble(args, variant):
    source = args.source.resolve()
    if not (source / 'main.asm').is_file(): raise ValueError('Firmware source directory must contain main.asm')
    out = args.output.resolve() / variant
    if out.is_relative_to(source): raise ValueError('Output must be outside the firmware source directory')
    out.mkdir(parents=True, exist_ok=True)
    stem = 'diskemu-' + variant
    for suffix in ('.hex', '.bin', '.eep', '.json'):
        (out / (stem + suffix)).unlink(missing_ok=True)
    revision = git(source, 'rev-parse', 'HEAD')
    description = git(source, 'describe', '--tags', '--always', '--dirty=-dirty', '--abbrev=12')
    version = args.version or description or 'source-snapshot'
    if re.fullmatch(r'[0-9a-f]{12}(?:-dirty)?', version): version = 'git-' + version
    if not re.fullmatch(r'[A-Za-z0-9_.+\-]+', version): raise ValueError('Version contains unsupported characters')
    epoch = args.epoch
    if epoch is None: epoch = int(git(source, 'show', '-s', '--format=%ct', 'HEAD') or 0)
    when = datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)
    date = when.strftime('%b %d %Y')
    clock = when.strftime('%H:%M:%S')
    inputs = {}
    with tempfile.TemporaryDirectory(prefix='diskemu-avr-') as tmp:
        root = Path(tmp)
        work = root / 'source'
        work.mkdir()
        for path in sorted(source.rglob('*')):
            if path.is_file() and path.suffix.lower() in ('.asm', '.inc'):
                relative = path.relative_to(source)
                contents = path.read_bytes()
                inputs[relative.as_posix()] = hashlib.sha256(contents).hexdigest()
                dest = work / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(contents)
        prelude = root / 'build-prelude.inc'
        prelude.write_text('.include "AVR128DB48def.inc"\n#undef __DATE__\n#undef __TIME__\n'
                           f'#define __DATE__ "{date}"\n#define __TIME__ "{clock}"\n')
        command = ['wine', str(TOOLS / 'avrasm2.exe'), '-fI', '-o', stem + '.hex', '-m', stem + '.map',
                   '-l', stem + '.lss', '-S', stem + '.tmp', '-W+ie', '-I', winpath(TOOLS / 'include'),
                   '-I', winpath(TOOLS / 'device'), '-i', winpath(prelude), '-d', stem + '.obj', '-e', stem + '.eep',
                   '-D', 'mscpemulation' if variant == 'mscp' else 'rlv12emulation',
                   '-D', f'lasttag="{version}"', 'main.asm']
        print(f'Assembling {variant} for AVR128DB48, version {version}, timestamp {date} {clock} UTC', flush=True)
        process = subprocess.run(command, cwd=work, text=True, errors='replace', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log = out / (stem + '.log')
        log.write_text(process.stdout)
        # Always preserve diagnostics; publish programming files only after validation.
        for suffix in ('.map', '.lss', '.obj', '.tmp'):
            path = work / (stem + suffix)
            if path.exists(): shutil.copyfile(path, out / path.name)
        if process.returncode or not re.search(r'Assembly complete, 0 errors\.', process.stdout):
            print(process.stdout, file=sys.stderr)
            raise RuntimeError(f'Assembler failed; see {log}')
        image, checks = validate(work / (stem + '.hex'), work / (stem + '.map'), process.stdout, date, clock, version)
        eep = work / (stem + '.eep')
        if eep.exists(): read_hex(eep, EEPROM_SIZE)
        outputs = {stem + '.hex': (work / (stem + '.hex')).read_bytes(), stem + '.bin': image}
        if eep.exists(): outputs[eep.name] = eep.read_bytes()
        for name, contents in outputs.items(): (out / name).write_bytes(contents)
        metadata = dict(checks, variant=variant, source_revision=revision, version=version, source_date_epoch=epoch,
                        source_files=inputs, source_sha256=hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
                        dependencies=json.loads((TOOLS / 'sources.lock.json').read_text()),
                        assembler=next(line for line in process.stdout.splitlines() if line.startswith('AVRASM:')),
                        wine=subprocess.check_output(['wine', '--version'], text=True).strip(),
                        device_include_sha256=sha(TOOLS / 'device/AVR128DB48def.inc'),
                        images_sha256={name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
                        eeprom_image_present=eep.exists(), validation='Structural checks only; no known-good image comparison, simulation or hardware validation.')
        (out / (stem + '.json')).write_text(json.dumps(metadata, indent=2) + '\n')
        for line in process.stdout.splitlines():
            if line.startswith(('[.cseg]', '[.dseg]', '[.eseg]', 'Assembly complete')) or 'warning:' in line:
                print(line, flush=True)
        print(f'Validated {out / (stem + ".hex")} and {FLASH_SIZE}-byte flash binary', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/src/MSCPEmu-v4-0'))
    parser.add_argument('--output', type=Path, default=Path('/src/build/firmware'))
    parser.add_argument('--variant', choices=('all', 'mscp', 'rlv12'), default='all')
    parser.add_argument('--version', help='Override the embedded git tag/revision string')
    parser.add_argument('--epoch', type=int, default=int(os.environ['SOURCE_DATE_EPOCH']) if 'SOURCE_DATE_EPOCH' in os.environ else None,
                        help='UTC build timestamp; defaults to firmware commit time')
    args = parser.parse_args()
    if args.epoch is not None and args.epoch < 0: parser.error('Epoch must be nonnegative')
    for variant in (('mscp', 'rlv12') if args.variant == 'all' else (args.variant,)):
        assemble(args, variant)


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(1)
