#!/usr/bin/env python3
"""Export sourcing and JLCPCB BOMs from schematic fields and an inventory snapshot."""
import argparse
import collections
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def natural(text):
    return [int(piece) if piece.isdigit() else piece for piece in re.split(r'(\d+)', text)]


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', default=os.environ.get('KICAD_CLI'))
    parser.add_argument('--inventory', type=Path, default=ROOT / 'bom/inventory-2026-11-07.json')
    args = parser.parse_args()
    cli = args.kicad_cli or shutil.which('kicad-cli')
    if not cli:
        mac_cli = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
        if mac_cli.is_file():
            cli = str(mac_cli)
    if not cli:
        parser.error('Set KICAD_CLI or pass --kicad-cli with the KiCad executable path')
    snapshot = json.loads(args.inventory.read_text(encoding='utf-8'))
    parts = snapshot['parts']
    checked = snapshot['checked_date']
    with tempfile.TemporaryDirectory(prefix='diskemu-bom-') as temp:
        netlist = Path(temp) / 'netlist.xml'
        command = [cli, 'sch', 'export', 'netlist', '--format', 'kicadxml',
                   '--output', str(netlist), str(ROOT / 'DISKEmu-v5-1.kicad_sch')]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stderr or result.stdout)
        tree = ET.parse(netlist)
    grouped = collections.defaultdict(list)
    features = []
    seen = set()
    for component in tree.findall('./components/comp'):
        ref = component.get('ref')
        if ref in seen:
            raise ValueError(f'Duplicate reference {ref}')
        seen.add(ref)
        fields = {field.get('name'): field.text or '' for field in component.findall('./fields/field')}
        assembly = fields.get('Assembly', '')
        if assembly == 'PCB feature':
            features.append({'Designator': ref, 'Value': component.findtext('value'),
                             'Footprint': component.findtext('footprint'),
                             'Notes': 'Part of PCB fabrication; no purchased component or LCSC number'})
            continue
        if not assembly:
            raise ValueError(f'{ref}: missing Assembly field')
        code = fields.get('LCSC', '')
        if code:
            part = parts[code]
            if fields.get('Inventory Checked') != checked:
                raise ValueError(f'{ref}: schematic and snapshot check dates differ')
            if part['mpn'] != fields.get('MPN'):
                raise ValueError(f'{ref}: MPN differs from inventory snapshot')
        elif assembly != 'Separate sourcing':
            raise ValueError(f'{ref}: no LCSC number and no sourcing exception')
        key = (code, component.findtext('value'), component.findtext('footprint'), assembly,
               fields.get('MPN', ''), fields.get('Manufacturer', ''))
        grouped[key].append(ref)
    rows = []
    for (code, value, footprint, assembly, mpn, manufacturer), refs in grouped.items():
        part = parts.get(code, {})
        notes = ''
        if not code:
            notes = 'No verified inventory assignment; see the schematic procurement note.'
        elif code == 'C219301':
            notes = 'Only 1 available at check; ATF1504AS standard-power variant selected, not ASL.'
        elif code == 'C31179':
            notes = 'Only 7 available at check; reserve/sourcing check needed for a production order.'
        elif code == 'C1019766':
            notes = 'Only 14 available at check.'
        elif assembly == 'Hand-fit':
            notes = 'Through-hole connector/header; hand-fit or quote separate THT assembly. Check body clearance in PCB update.'
        rows.append({'Designator': ', '.join(sorted(refs, key=natural)), 'Quantity': len(refs),
                     'Value': value, 'Footprint': footprint, 'Manufacturer': manufacturer,
                     'MPN': mpn, 'LCSC Part #': code,
                     'JLCPCB Class': 'Basic' if part.get('tier') == 'base' else ('Extended' if code else 'Not listed'),
                     'Assembly': assembly, 'Available Order Qty': part.get('available', ''),
                     'Stock Qty': part.get('stock', ''), 'Unit Price USD': part.get('price', ''),
                     'Checked': checked, 'Source': f'https://jlcpcb.com/partdetail/{code}' if code else '',
                     'Notes': notes})
    # Five removable shunts are purchased accessories, not pick-and-place components.
    part = parts['C5305']
    rows.append({'Designator': 'JP1 shunts (2), JP2 shunts (3)', 'Quantity': 5,
                 'Value': '2.54mm removable shunt', 'Footprint': 'Accessory',
                 'Manufacturer': part['manufacturer'], 'MPN': part['mpn'], 'LCSC Part #': 'C5305',
                 'JLCPCB Class': 'Extended', 'Assembly': 'Accessory',
                 'Available Order Qty': part['available'], 'Stock Qty': part['stock'],
                 'Unit Price USD': part['price'], 'Checked': checked,
                 'Source': 'https://jlcpcb.com/partdetail/C5305',
                 'Notes': 'Fit two column-wise shunts on JP1 and three row-wise shunts on JP2.'})
    rows.sort(key=lambda row: natural(row['Designator']))
    columns = ['Designator', 'Quantity', 'Value', 'Footprint', 'Manufacturer', 'MPN', 'LCSC Part #',
               'JLCPCB Class', 'Assembly', 'Available Order Qty', 'Stock Qty', 'Unit Price USD',
               'Checked', 'Source', 'Notes']
    output = ROOT / 'bom'
    write_csv(output / 'bom.csv', columns, rows)
    hand = [row for row in rows if row['Assembly'] != 'JLCPCB SMT']
    write_csv(output / 'hand-assembly.csv', columns, hand)
    write_csv(output / 'pcb-features.csv', ['Designator', 'Value', 'Footprint', 'Notes'], features)
    smt = [row for row in rows if row['Assembly'] == 'JLCPCB SMT']
    jlc = [{'Comment': row['Value'], 'Designator': row['Designator'],
            'Footprint': row['Footprint'].split(':')[-1], 'LCSC Part #': row['LCSC Part #'],
            'Quantity': row['Quantity']} for row in smt]
    write_csv(output / 'jlcpcb-bom.csv', ['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Quantity'], jlc)
    for row in smt:
        if int(row['Available Order Qty']) < row['Quantity']:
            raise ValueError(f"Insufficient inventory for one board: {row['Designator']}")
    counts = collections.Counter(row['JLCPCB Class'] for row in smt)
    print(f"SMT: {sum(row['Quantity'] for row in smt)} components; "
          f"{counts['Basic']} unique Basic and {counts['Extended']} unique Extended parts")
    print(f"Assembly completion/accessories: {sum(row['Quantity'] for row in hand)} items")
    print(f"PCB features: {len(features)}; sourcing exceptions: "
          + (', '.join(row['Designator'] for row in rows if not row['LCSC Part #']) or 'none'))
    print(f'Inventory snapshot: {checked}; stock and pricing must be refreshed before ordering.')


if __name__ == '__main__':
    main()
