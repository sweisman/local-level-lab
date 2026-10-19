# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build a credential-free iMAR catalog from the eight saved FTPS listings."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
DATA=ROOT/'data/external-imu-survey-20261018/esa-sample'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with (HERE/'esa-reported-imu-files.csv').open() as stream:reported={r['filename']:r for r in csv.DictReader(stream)}
    rows=[];inputs={}
    receipt=json.loads((DATA/'download-completion.json').read_text())
    for day in ('178','179','180','182','183','184','186','187'):
        listing=DATA/'catalog'/f'lvl0-{day}-rqh01-list.txt';inputs[str(listing.relative_to(ROOT))]=sha(listing)
        for line in listing.read_text().splitlines():
            fields=line.split(maxsplit=8)
            if len(fields)!=9 or not fields[0].startswith('-'):raise ValueError('explicit regular-file listing required')
            name=fields[8];size=int(fields[4])
            if name not in reported or size<=0:raise ValueError('unexpected raw iMAR catalog entry')
            metadata=reported[name];downloaded=name==receipt['filename']
            if downloaded and size!=receipt['size_bytes']:raise ValueError('download/catalog size mismatch')
            rows.append(dict(filename=name,date=metadata['date'],flight_ids=metadata['flight_ids'],size_bytes=size,
                url=f'ftps://tpm-if.eo.esa.int/lvl0/{day}/rqh01/{name}',downloaded=downloaded,
                local_sha256=receipt['sha256'] if downloaded else '',eligibility='not evaluated'))
    if len(rows)!=9 or {r['filename'] for r in rows}!=reported.keys():raise ValueError('complete unique nine-file catalog required')
    catalog=HERE/'esa-live-imu-files.csv'
    with catalog.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report=dict(files=len(rows),total_bytes=sum(r['size_bytes'] for r in rows),downloaded_files=sum(r['downloaded'] for r in rows),
        inputs=inputs,script_sha256=sha(Path(__file__)),catalog_sha256=sha(catalog),credentials_stored=False,earth_model_fits=0)
    (HERE/'esa-live-inventory.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('files','total_bytes','downloaded_files')}))


if __name__=='__main__':main()
