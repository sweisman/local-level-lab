# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build the offline selector from an explicitly downloaded OpenFlights snapshot."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


def build(path, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('supply the exact upstream git revision')
    airlines = []
    with path.open(encoding='utf-8', newline='') as source:
        for row in csv.reader(source):
            if len(row) != 8:
                raise ValueError('unexpected airline column count')
            identifier, name, alias, iata, icao, _, country, active = row
            iata = iata if re.fullmatch(r'[A-Z0-9]{2}', iata) else ''
            icao = icao if re.fullmatch(r'[A-Z]{3}', icao) else ''
            if not (iata or icao) or not name.strip() or name in ('Unknown', 'Private flight'):
                continue
            airlines.append(dict(id='openflights:'+identifier, name=name, alias='' if alias == r'\N' else alias,
                                 iata=iata, icao=icao, country='' if country == r'\N' else country,
                                 listed_active=active == 'Y'))
    if len({a['id'] for a in airlines}) != len(airlines):
        raise ValueError('duplicate airline identifier')
    return dict(format='airline-directory-1', source='https://openflights.org/data.php',
                source_revision=revision,
                source_url=f'https://raw.githubusercontent.com/jpatokal/openflights/{revision}/data/airlines.dat',
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                license='ODbL-1.0', status_policy='include all coded carriers; upstream active flag is not authoritative',
                airlines=sorted(airlines, key=lambda a: (a['name'].casefold(), a['id'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = build(args.source, args.revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
    print(f"Wrote {len(data['airlines'])} coded airline records")
