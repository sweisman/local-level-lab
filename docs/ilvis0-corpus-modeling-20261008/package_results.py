# SPDX-License-Identifier: AGPL-3.0-or-later
"""Automatically audit/package the completed corpus; waiting consumes no model calls."""
import argparse
from collections import Counter
import csv
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from lll import ilvis0 as il, ilvis0_followup as follow


def load(path):return json.loads(Path(path).read_text())


def package(root):
    source=root/'data/ilvis0-corpus-modeling-v2-20261008';dest=Path(__file__).resolve().parent
    complete=load(source/'completion.json');manifest=load(source/'manifest.json')
    if complete['state']!='complete' or complete['files']!=232:raise ValueError('complete 232-file inventory required')
    for name,key in [('manifest.json','manifest_sha256'),('summary.json.gz','summary_sha256')]:
        if il.sha256(source/name)!=complete[key]:raise ValueError('completion digest mismatch')
    for name,digest in {**manifest['sources'],**manifest['inputs']}.items():
        if il.sha256(name)!=digest:raise ValueError('frozen source/input changed')
    with gzip.open(source/'summary.json.gz','rt') as stream:summary=json.load(stream)
    starts=[json.loads(line) for line in (source/'starts.jsonl').read_text().splitlines()]
    prior=manifest['carried_forward_starts'];all_starts=starts+prior
    if len(all_starts)!=complete['starts'] or len(all_starts)>764 or any(n>2 for n in Counter(r['identity'] for r in all_starts).values()):
        raise ValueError('corpus attempt accounting mismatch')
    if any(r['start']!=i+1 or r['manifest_sha256']!=complete['manifest_sha256'] or r['maximum_evaluations']!=200
           for i,r in enumerate(starts)):raise ValueError('invalid current journal')
    if len(summary['results'])!=232 or len({r['task'] for r in summary['results']})!=232:
        raise ValueError('missing/duplicate per-file outcomes')
    rows=[];unsupported=[]
    for r in summary['results']:
        if r['scientific_decision']!='abstain' or not r['original_preserved']:raise ValueError('unjustified promotion/deletion')
        if r['state']=='unsupported':unsupported.append(dict(filename=r['filename'],task=r['task'],reason=r['reason']));continue
        for fit in r['fits']:
            charged=fit['start_charge']
            if charged!=starts[charged['start']-1]:raise ValueError('per-fit start mismatch')
            if fit.get('evaluations',0)>200 or fit.get('scientific_eligible'):raise ValueError('invalid result gate/budget')
            rows.append(dict(filename=r['filename'],task=r['task'],imu_type=r['provenance']['imu_type'],
                model=fit['model'],seconds=r['provenance']['duration_nominal_s'],
                converged=fit.get('converged',False),evaluations=fit.get('evaluations'),
                weighted_cost=fit.get('residual_sum_squares'),rms_neu_m=json.dumps(fit.get('residual_rms_neu_m')),
                stationarity=fit.get('exact_projected_gradient_relative'),
                earth_removal=fit.get('parameters',{}).get('earth_removal'),
                active_bounds=';'.join(fit.get('active_bounds',[])),error=fit.get('error','')))
    for name,records,fields in [('fits.csv',rows,['filename','task','imu_type','model','seconds','converged',
        'evaluations','weighted_cost','rms_neu_m','stationarity','earth_removal','active_bounds','error']),
        ('unsupported.csv',unsupported,['filename','task','reason'])]:
        with (dest/name).open('w',newline='') as out:
            writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader();writer.writerows(records)
    lines=['# Completed conditional corpus results','',
        f"All {complete['files']} kept files have an outcome. {complete['fitted_files']} files were fitted; "
        f"{complete['unsupported_files']} have an explicit unsupported-data reason.",'',
        f"The study used {complete['starts']} charged starts, including the carried-forward interrupted start. "
        f"There are {complete['converged_fits']} numerically converged fits and {complete['failed_fits']} failed fits.",'',
        'These counts describe recorded files and model fits, not independent flights or trials. '
        'Overlapping streams and duplicate recordings must not be pooled as independent evidence.','',
        '[Per-fit results](fits.csv) preserve errors, convergence, stationarity, residuals, nuisance limits '
        'and the hypothesized logging correction. [Unsupported files](unsupported.csv) preserve every reason.','',
        'Numerical convergence checks a local stationary point. It does not prove a global optimum, '
        'instrument calibration, logging independence, uncertainty coverage or an Earth-model winner. '
        'All decisions remain abstentions. The documented processing and GPS-geometry assumptions still apply.','',
        'Next work should compare matched, converged profiles under independently supported calibration '
        'and processing information where available, and preserve conflicting or inconclusive outcomes. '
        'Further fits require a separately frozen finite scope. No original was deleted and no '
        'synthetic campaign or calibrated production decision was enabled.','']
    (dest/'RESULTS.md').write_text('\n'.join(lines))
    for name in ('manifest.json','completion.json','summary.json.gz','starts.jsonl'):
        shutil.copyfile(source/name,dest/name)
    shutil.copytree(source/'source-freeze',dest/'source-freeze',dirs_exist_ok=True)
    receipt=dict(state='complete',files=232,starts=complete['starts'],scientific_decision='abstain',
        artifacts={name:il.sha256(dest/name) for name in ('manifest.json','completion.json','summary.json.gz','starts.jsonl',
            'fits.csv','unsupported.csv','RESULTS.md','package_results.py')})
    follow.atomic_json(dest/'evidence-receipt.json',receipt)
    readiness=root/'docs/research-next-stage-20261006/readiness.json';metadata=load(readiness)
    stage=metadata['ilvis0_physical_pipeline']['conditional_recorded_modeling']
    stage.update(state='six_file_and_corpus_complete',corpus_completion=complete,
        corpus_report='docs/ilvis0-corpus-modeling-20261008/RESULTS.md')
    metadata['ilvis0_physical_pipeline']['earth_model_fit_attempts']=24+complete['starts']
    for name,digest in receipt['artifacts'].items():metadata['artifact_sha256'][str((dest/name).relative_to(root))]=digest
    follow.atomic_json(readiness,metadata)
    follow.atomic_json(source/'package-status.json',dict(state='complete',evidence_receipt_sha256=il.sha256(dest/'evidence-receipt.json')))
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--watch',action='store_true');parser.add_argument('--detach',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[2];source=root/'data/ilvis0-corpus-modeling-v2-20261008'
    if args.detach:
        with (root/'data/ilvis0-corpus-package-20261008.log').open('ab',buffering=0) as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--watch'],cwd=root,
                stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
        print(json.dumps(dict(pid=child.pid)))
    else:
        with (source/'package.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            deadline=time.monotonic()+12*3600
            while args.watch and not (source/'completion.json').exists():
                status=load(source/'status.json');os.kill(status['pid'],0)
                if time.monotonic()>deadline:raise RuntimeError('12-hour packaging wait expired; worker untouched')
                time.sleep(30)
            package(root)
