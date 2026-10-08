# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit and package recorded-fit results; inventory only documented kept originals."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from collections import Counter

from lll import ilvis0 as il, ilvis0_followup as follow


def load(path):
    if str(path).endswith('.gz'):
        with gzip.open(path,'rt') as f:return json.load(f)
    return json.loads(Path(path).read_text())


def run(root):
    source=root/'data/ilvis0-exploratory-20261008';dest=Path(__file__).resolve().parent
    complete=load(source/'completion.json');manifest=load(source/'manifest.json')
    if complete['state']!='complete' or complete['files']!=6 or complete['optimizer_starts']>24:
        raise ValueError('six-file completion required')
    for filename,key in [('manifest.json','manifest_sha256'),('summary.json.gz','summary_sha256')]:
        if il.sha256(source/filename)!=complete[key]:raise ValueError('completion hash mismatch')
    for name,digest in {**manifest['sources'],**manifest['inputs']}.items():
        if il.sha256(name)!=digest:raise ValueError('frozen source/input mismatch')
    summary=load(source/'summary.json.gz')
    starts=[json.loads(line) for line in (source/'empirical-starts.jsonl').read_text().splitlines()]
    if len(starts)!=complete['optimizer_starts'] or any(r['start']!=i+1 or r['manifest_sha256']!=complete['manifest_sha256']
        or r['maximum_evaluations']>200 for i,r in enumerate(starts)):raise ValueError('invalid start journal')
    rows=[];originals=[]
    for r in summary['results']:
        if r['manifest_sha256']!=complete['manifest_sha256'] or il.sha256(source/(r['task']+'-native.csv.gz'))!=r['native_sha256']:
            raise ValueError('recorded result or raw cache mismatch')
        for f in r['fits']:
            if f.get('scientific_eligible') or f.get('scientific_decision')!='abstain':raise ValueError('invalid scientific promotion')
            if not f.get('error'):
                if f['evaluations']>200 or f['start_charge']!=starts[f['start_charge']['start']-1]:raise ValueError('evaluation/charge mismatch')
                rms=f['residual_rms_neu_m']
                rows.append(dict(filename=r['filename'],task=r['task'],label=f['label'],
                    duration_s=r['provenance']['duration_nominal_s'],gps_epochs=r['provenance']['receiver_epochs'],
                    converged=f['converged'],evaluations=f['evaluations'],weighted_cost=f['residual_sum_squares'],
                    north_rms_m=rms[0],east_rms_m=rms[1],up_rms_m=rms[2],
                    earth_removal_fraction=f['parameters']['earth_removal'],active_bounds=';'.join(f['active_bounds']),
                    nuisance_rank=f['nuisance_rank'],conservative_fixed_parameter_cost=f['conservative_covariance_fixed_parameter_cost']))
    with (dest/'comparison.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    # Enumerate exact catalog-record paths only, honoring later cleanup by existence.
    corpus=root/'data/ilvis0-ready'
    records={r['task_id']:r for r in map(json.loads,(corpus/'records.jsonl').read_text().splitlines())}
    followup_path=root/'data/ilvis0-followup-20261007/summary.json'
    contexts={r['task_id']:r for r in load(followup_path)['results']}
    for task,record in records.items():
        try:path=follow.source_path(corpus,record)
        except ValueError:continue
        context=contexts.get(task);inspection=context['inspection'] if context else record
        if context:
            types=','.join(sorted(inspection['imu_types']));rates=','.join(sorted(inspection['rate_codes']))
        else:
            config=json.loads(record['configuration']);types=','.join(sorted(config[1]));rates=','.join(sorted(config[2]))
        originals.append(dict(task=task,filename=record['filename'],source_path=str(path),
            source_sha256=record['source_sha256'],compressed_bytes=path.stat().st_size,
            imu_type=types,rate_code=rates,
            embedded_dates=';'.join(context['timing'].get('dates',[])) if context else '',
            validated_utc_mapping=bool(context and context['timing']['accepted']),
            six_file_fit_completed=task in manifest['tasks'],
            expansion_status='completed six-file pilot' if task in manifest['tasks'] else 'pending conditional preparation; no calibrated science gate',
            configuration=json.dumps(inspection.get('versions',{}),sort_keys=True)))
    if len(originals)!=232:raise ValueError('current kept-original inventory changed')
    with (dest/'corpus-inventory.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(originals[0]));writer.writeheader();writer.writerows(originals)
    for name in ('manifest.json','completion.json','summary.json.gz','empirical-starts.jsonl'):
        shutil.copyfile(source/name,dest/name)
    shutil.copytree(source/'source-freeze',dest/'source-freeze',dirs_exist_ok=True)
    receipt=dict(state='complete',files=6,fits=complete['fits'],converged_fits=complete['converged_fits'],
        failed_fits=complete['failed_fits'],optimizer_starts=len(starts),originals_preserved=232,
        corpus_imu_types=dict(Counter(r['imu_type'] for r in originals)),
        artifacts={name:il.sha256(dest/name) for name in ('manifest.json','completion.json','summary.json.gz',
            'empirical-starts.jsonl','comparison.csv','corpus-inventory.csv','build_report.py')},
        prior_context_sha256=il.sha256(followup_path),scientific_decision='abstain')
    follow.atomic_json(dest/'evidence-receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('artifacts','prior_context_sha256')}))


if __name__=='__main__':run(Path(__file__).resolve().parents[2])
