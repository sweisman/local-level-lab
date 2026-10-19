# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only finite affine diagnosis; --render-only never solves a system."""
import argparse
import csv
import fcntl
import gzip
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded
from lll.ilvis0_artifact_inventory import load,sha
NAME='ilvis0-horizontal-repeat-audit-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-horizontal-observed-20261018'


def write(p,value):durable_write(p,encoded(value),replace=True)


def render():
    s=load(DATA/'summary.json');c=load(DATA/'completion.json')
    if c['manifest_sha256']!=sha(DATA/'manifest.json') or c['summary_sha256']!=sha(DATA/'summary.json'):raise ValueError('completion mismatch')
    for n in ('manifest.json','summary.json','completion.json','starts.jsonl'):shutil.copy2(DATA/n,PUBLIC/n)
    rows=s['primary_metrics']
    with (PUBLIC/'primary-metrics.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    text=['# What horizontal-only refitting established','',
        'All twelve reconstructions and all 24 individual fits passed. The IMU8 stretch passes all six repeat checks and favors globe under both processing cases. The IMU21 stretch passes three of six repeat checks and remains unresolved in this sensitivity study; its primary and repeat costs both favor globe. The original 53-stretch findings remain unchanged.',
        '', '| IMU | Processing case | Model | Horizontal RMS (m) | Unscored height RMS (m) | Objective |',
        '|---:|---|---|---:|---:|---:|']
    for r in rows:text.append(f"| {r['imu_type']} | {r['case_id']} | {r['model']} | {r['horizontal_rms_m']:.4g} | {r['height_rms_m']:.4g} | {r['cost']:.6g} |")
    text+=['','The large unscored height errors are an important consequence of removing the vertical constraint. These solutions do not reconstruct plausible full three-dimensional flight paths. The successful IMU8 comparison shows that the score advantage persists without scoring height; it does not establish altitude or datum independence, isolate the gyroscope, or calibrate statistical significance.',
        '', '| Stretch | Case | Model | Repeat passed | Timing difference (ms) | Relative cost difference |',
        '|---|---|---|---|---:|---:|']
    for p in s['pairs']:text.append(f"| {p['segment_id']} | {p['case_id']} | {p['model']} | {p['passed']} | {p['timing_difference_s']*1000:.6g} | {p['relative_cost_difference']:.6g} |")
    text+=['','The saved audit completed 48 affine solves across all 24 endpoints, with no original-recording reads, native predictions or optimizer starts. Its linear predictions cannot establish actual improvement or relabel any fit.',
        '', '[Frozen audit scope](PLAN.md) · [Detailed interpretation](INTERPRETATION.md) · [Metrics CSV](primary-metrics.csv) · [Observed study](../ilvis0-horizontal-observed-20261018/README.md).']
    (PUBLIC/'README.md').write_text('\n'.join(text)+'\n')
    names=('manifest.json','summary.json','completion.json','starts.jsonl','README.md','PLAN.md','primary-metrics.csv')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names}))


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'manifest.json').exists():raise ValueError('charged audit cannot restart; render only')
        if any(os.environ.get(n)!='4' for n in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')):raise ValueError('use run_numerical.py --threads 4')
        c=load(PARENT/'completion.json')
        if c['manifest_sha256']!=sha(PARENT/'manifest.json') or c['summary_sha256']!=sha(PARENT/'summary.json'):raise ValueError('parent completion mismatch')
        receipt=load(PARENT/'evidence-receipt.json')
        for p,d in receipt['artifacts'].items():
            if sha(PARENT/p)!=d:raise ValueError('parent receipt mismatch')
        parent=load(PARENT/'summary.json');m=load(PARENT/'manifest.json');rows=parent['results']
        if len(rows)!=24 or len({r['identity'] for r in rows})!=24 or not all(r['passed'] for r in rows):raise ValueError('exact completed passing-fit set required')
        inputs={str((PARENT/p).relative_to(ROOT)):sha(PARENT/p) for p in receipt['artifacts']}
        sources={}
        for manifest in (m,load(ROOT/'docs/ilvis0-scaled-pair-boundary-20261018/manifest.json')):
            for p in manifest['sources']:
                path=Path(p)
                if path.is_absolute():
                    path=path.relative_to(ROOT) if path.is_relative_to(ROOT) else Path(*path.parts[path.parts.index('analysis'):])
                sources[str(path)]=sha(ROOT/path)
        for p in ('analysis/lll/ilvis0_horizontal_repeat_audit.py','analysis/tests/test_ilvis0_horizontal_repeat_audit.py',str(Path(__file__).relative_to(ROOT)),str((PUBLIC/'PLAN.md').relative_to(ROOT))):sources[p]=sha(ROOT/p)
        freeze=dict(version='horizontal-saved-repeat-audit-v1',sources=sources,inputs=inputs,
            environment=dict(python=platform.python_version(),numpy=importlib.metadata.version('numpy'),scipy=importlib.metadata.version('scipy')),
            limits=dict(affine_solves=48,maximum_wall_s=120,numerical_threads=4,native_evaluations=0,observed_starts=0),
            identities=[r['identity'] for r in rows])
        write(DATA/'manifest.json',freeze)
        for p in sources:
            target=PUBLIC/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
        from lll import ilvis0_horizontal_repeat_audit as audit
        from lll.ilvis0_horizontal_observed import repeat_check
        import math
        endpoints=[];saved={};started=time.monotonic()
        for r in rows:
            if time.monotonic()-started>120:raise TimeoutError('finite audit ceiling exceeded')
            with (DATA/'starts.jsonl').open('ab') as stream:stream.write(encoded(dict(identity=r['identity'],affine_solves=2)));stream.flush();os.fsync(stream.fileno())
            data=load(PARENT/r['linearization_file']);saved[r['identity']]=data
            endpoints.append(audit.endpoint(r,data))
        pairs=[];metrics=[]
        chosen={r['segment']['segment_id']:r for r in m['selected']}
        for a in rows:
            if a['role']!='primary':continue
            b=next(r for r in rows if (r['segment_id'],r['case_id'],r['model'],r['role'])==(a['segment_id'],a['case_id'],a['model'],'repeat'))
            pairs.append(dict(segment_id=a['segment_id'],case_id=a['case_id'],model=a['model'],**repeat_check(a,b),**audit.pair(a,b,saved[a['identity']],saved[b['identity']])))
            selection=chosen[a['segment_id']]
            metrics.append(dict(segment_id=a['segment_id'],filename=selection['filename'],imu_type=selection['segment']['imu_type'],
                duration_s=selection['segment']['duration_s'],case_id=a['case_id'],model=a['model'],cost=a['fit']['residual_sum_squares'],
                horizontal_rms_m=math.hypot(*a['track_rms_neu_m'][:2]),height_rms_m=a['track_rms_neu_m'][2]))
        if any(sha(ROOT/p)!=d for p,d in {**inputs,**sources}.items()):raise ValueError('frozen dependency changed')
        summary=dict(state='complete',endpoints=endpoints,pairs=pairs,primary_metrics=metrics,affine_solves=48,
                     native_evaluations=0,observed_starts=0,fit_labels_changed=False,elapsed_s=time.monotonic()-started)
        write(DATA/'summary.json',summary);write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        render();print('Completed 24 endpoints /48 affine solves, zero native predictions or fits.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    render() if args.render_only else run()
