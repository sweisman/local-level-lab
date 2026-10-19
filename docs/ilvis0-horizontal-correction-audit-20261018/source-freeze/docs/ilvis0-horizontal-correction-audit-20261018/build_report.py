# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-array audit; --render-only never performs numerical work."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
NAME='ilvis0-horizontal-correction-audit-20261018'
DATA=ROOT/'data'/NAME
PUBLIC=ROOT/'docs'/NAME
PARENT=ROOT/'docs/ilvis0-projected-horizontal-fullcal-20261018'
sys.path.insert(0,str(ROOT/'analysis'))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def write(path,value):
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,sort_keys=True,allow_nan=False)+'\n')
    temporary.replace(path)


def render():
    summary=load(DATA/'summary.json');done=load(DATA/'completion.json')
    if done['summary_sha256']!=sha(DATA/'summary.json') or done['manifest_sha256']!=sha(DATA/'manifest.json'):
        raise ValueError('completed audit hash mismatch')
    for name in ('manifest.json','summary.json','completion.json','starts.jsonl'):
        shutil.copy2(DATA/name,PUBLIC/name)
    lines=['# Saved horizontal correction audit','',
        'All twelve saved endpoints were inspected with three affine formulations each: **36 linear solves**, zero native predictions and zero model refits. The failed parent qualification remains unchanged.','',
        '| Endpoint | Original fit passed | Rank / columns | Original probe max step | Scaled probe max step | Ridge probe max step |',
        '|---|---|---:|---:|---:|---:|']
    for row in summary['results']:
        values=[f"{c['maximum_normalized_step']:.3g}" for c in row['corrections']]
        lines.append(f"| {row['identity']} | {row['original_fit_passed']} | {row['numerical_rank']}/{row['columns']} | {' | '.join(values)} |")
    lines+=['','These are linear predictions at saved endpoints. They cannot establish a fresh nonlinear improvement, change stopping labels or qualify observed-data fitting. Ridge regularization changes the diagnostic correction objective; it does not change any physical-model score.',
        '', '[Scope and call-allowance correction](PLAN.md) · [Interpretation](INTERPRETATION.md) · [Next analyses](../NEXT_STEPS.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    names=('manifest.json','summary.json','completion.json','starts.jsonl','README.md','PLAN.md')
    write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:sha(PUBLIC/n) for n in names}))


def run():
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'manifest.json').exists():raise ValueError('charged audit cannot restart; render only')
        if any(os.environ.get(n)!='4' for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')):
            raise ValueError('run through run_numerical.py --threads 4')
        done=load(PARENT/'completion.json')
        if done['manifest_sha256']!=sha(PARENT/'manifest.json') or done['summary_sha256']!=sha(PARENT/'summary.json'):
            raise ValueError('parent hashes disagree')
        for filename,digest in load(PARENT/'evidence-receipt.json')['artifacts'].items():
            if sha(PARENT/filename)!=digest:raise ValueError('parent publication changed')
        parent=load(PARENT/'summary.json');rows=parent['results']
        expected={f'{model}-{case}-horizontal-{start}' for model in ('sphere_rotating','sphere_still','flat_still')
                  for case in ('bias1_unsubtracted','bias1_profiled_removal') for start in ('zero','opposed')}
        if len(rows)!=12 or {r['identity'] for r in rows}!=expected:raise ValueError('exact twelve parent endpoints required')
        sources=['analysis/lll/ilvis0_horizontal_correction_audit.py',
                 'analysis/tests/test_ilvis0_horizontal_correction_audit.py',
                 str(Path(__file__).relative_to(ROOT)),str((PUBLIC/'PLAN.md').relative_to(ROOT)),
                 'analysis/tests/run_numerical.py','analysis/lll/compute_budget.py']
        manifest=dict(version='saved-horizontal-correction-audit-v1',
            sources={p:sha(ROOT/p) for p in sources},
            inputs={str((PARENT/p).relative_to(ROOT)):sha(PARENT/p) for p in ('manifest.json','summary.json','completion.json','evidence-receipt.json')},
            environment=dict(python=platform.python_version(),numpy=importlib.metadata.version('numpy'),scipy=importlib.metadata.version('scipy')),
            limits=dict(affine_solves=36,svds=12,maximum_wall_s=60,numerical_threads=4,native_evaluations=0,observed_starts=0))
        write(DATA/'manifest.json',manifest)
        for p in sources:
            target=PUBLIC/'source-freeze'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,target)
        from lll.ilvis0_horizontal_correction_audit import audit
        started=time.monotonic();results=[]
        for row in rows:
            if time.monotonic()-started>60:raise TimeoutError('finite audit ceiling exceeded')
            with (DATA/'starts.jsonl').open('a') as journal:
                journal.write(json.dumps(dict(identity=row['identity'],charged_affine_solves=3))+'\n');journal.flush();os.fsync(journal.fileno())
            results.append(audit(row))
            write(DATA/'progress.json',dict(completed=len(results),passed=0))
        summary=dict(state='complete',results=results,affine_solves=36,native_evaluations=0,
                     observed_starts=0,elapsed_s=time.monotonic()-started,scientific_decision='abstain',
                     parent_qualification_passed=parent['passed'],parent_pairs=parent['pairs'])
        write(DATA/'summary.json',summary)
        write(DATA/'completion.json',dict(state='complete',manifest_sha256=sha(DATA/'manifest.json'),summary_sha256=sha(DATA/'summary.json')))
        render();print('Completed 12 endpoints /36 affine solves; zero native predictions or fits.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    render() if args.render_only else run()
