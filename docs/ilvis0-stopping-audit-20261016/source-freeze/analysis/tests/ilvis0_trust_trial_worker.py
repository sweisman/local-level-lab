# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately frozen eight-start trial after complete software qualification."""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'data/ilvis0-trust-trial-20261015'
GUIDE=ROOT/'docs/ilvis0-trust-trial-20261015'
PARENT=ROOT/'docs/ilvis0-budget-continuation-20261014'
QUALIFIED=ROOT/'docs/ilvis0-trust-v2-qualification-20261015'
VERSION='ilvis0-hybrid-trust-matched-trial-v1'
_engine=None


def load(path): return json.loads(path.read_text())


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()


def make_plan(parent,summary):
    plan=copy.deepcopy(parent['plan']);tasks=plan['tasks']
    if (len(tasks)!=8 or plan['maximum_starts']!=8 or plan['maximum_native_sweeps']!=1296
            or len(plan['target_segment_ids'])!=3 or len(set(plan['target_segment_ids']))!=3
            or sum(t['maximum_evaluations']+2 for t in tasks)!=1296
            or sum(t['role']=='control' for t in tasks)!=2
            or sum(t['role']=='primary' for t in tasks)!=3 or sum(t['role']=='repeat' for t in tasks)!=3):
        raise ValueError('exact eight-start matched scope required')
    for task in tasks:
        key=task['identity'].rsplit('::',1)[0]+'::primary' if task['role']=='repeat' else task['identity']
        task['reference']=copy.deepcopy(summary['results'][key])
        task['seed_policy']='latest_frozen_primary_plus_0.01' if task['role']=='repeat' else 'latest_frozen_primary'
    plan.update(version=VERSION,solver='lll.ilvis0_solver_trust_v2',retry_allowance=0)
    return plan


def engine():
    global _engine
    if _engine is not None: return _engine
    sys.path.insert(0,str(ROOT/'analysis'));sys.path.insert(0,str(ROOT/'analysis/tests'))
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    # A private module instance reuses tested accounting, extraction and
    # publication without changing any frozen source or another worker's globals.
    path=ROOT/'analysis/tests/ilvis0_precision_continuation_worker.py'
    spec=importlib.util.spec_from_file_location('_trust_trial_engine',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    from lll import ilvis0_solver_trust_v2
    value.OUTPUT=OUTPUT;value.GUIDE=GUIDE;value.VERSION=VERSION;value.solver=ilvis0_solver_trust_v2
    value.prepare=prepare;value.verify=verify;_engine=value
    return value


def check_qualification():
    receipt=load(QUALIFIED/'evidence-receipt.json')
    if any(sha(QUALIFIED/n)!=h for n,h in receipt['artifacts'].items()): raise ValueError('qualification publication mismatch')
    result=load(QUALIFIED/'result.json');completion=load(QUALIFIED/'completion.json')
    if (not result['passed'] or result['tests']!=48 or result['failures'] or result['errors'] or result['skipped']
            or completion['manifest_sha256']!=sha(QUALIFIED/'manifest.json')
            or completion['result_sha256']!=sha(QUALIFIED/'result.json')):
        raise ValueError('all 48 software controls must qualify before observed starts')
    for name,h in load(QUALIFIED/'manifest.json')['sources'].items():
        if sha(Path(name))!=h: raise ValueError('qualified source changed: '+name)


def prepare():
    if (OUTPUT/'manifest.json').exists(): return verify()
    e=engine();check_qualification();parent=load(PARENT/'manifest.json');summary=load(PARENT/'summary.json')
    complete=load(PARENT/'completion.json');receipt=load(PARENT/'evidence-receipt.json')
    if complete['summary_sha256']!=sha(PARENT/'summary.json') or complete['manifest_sha256']!=sha(PARENT/'manifest.json'):
        raise ValueError('completed matched parent required')
    if any(sha(PARENT/n)!=h for n,h in receipt['artifacts'].items()): raise ValueError('parent evidence mismatch')
    plan=make_plan(parent,summary)
    if {t['segment_id'] for t in plan['tasks'] if t['role']!='control'}!=set(parent['plan']['target_segment_ids']):
        raise ValueError('matched target population changed')
    _,meta=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if meta!=parent['extended_kernel']: raise ValueError('qualified integration kernel changed')
    sources=dict(parent['sources'])
    for path in (Path(__file__),ROOT/'analysis/lll/ilvis0_solver_trust_v2.py',
                 ROOT/'analysis/tests/test_ilvis0_solver_trust_v2.py',ROOT/'analysis/tests/test_ilvis0_trust_trial_worker.py'):
        sources[str(path.resolve())]=sha(path)
    inputs=dict(parent['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json','evidence-receipt.json')),
                            (QUALIFIED,('manifest.json','result.json','completion.json','evidence-receipt.json','tests.xml')),
                            (GUIDE,('PLAN.md',))):
        for name in names: inputs[str(directory/name)]=sha(directory/name)
    for name,h in dict(sources,**inputs).items():
        if sha(Path(name))!=h: raise ValueError('source or input changed: '+name)
    reused=copy.deepcopy(parent['reused_results'])
    if len(reused)!=15 or not all(f['converged'] for f in reused.values()): raise ValueError('fifteen passing companions required')
    for name,h in parent['reused_artifacts'].items():
        if Path(name).name!=name or sha(PARENT/name)!=h: raise ValueError('reused artifact mismatch')
        shutil.copyfile(PARENT/name,OUTPUT/name)
    for name,h in parent['originals'].items():
        if sha(Path(name))!=h: raise ValueError('retained original mismatch')
    freeze=OUTPUT/'source-freeze';freeze.mkdir(exist_ok=True)
    if len({Path(n).name for n in sources})!=len(sources): raise ValueError('snapshot basename collision')
    for name in sources: shutil.copyfile(name,freeze/Path(name).name)
    shutil.copyfile(OUTPUT/'kernel'/meta['source_file'],freeze/meta['source_file'])
    value=dict(version=VERSION,stage='matched_trust',plan=plan,sources=sources,inputs=inputs,
        originals=parent['originals'],reused_results=reused,reused_artifacts=parent['reused_artifacts'],
        extended_kernel=meta,ordinary_value_kernel=parent['ordinary_value_kernel'],
        environment=e.base.runtime.numerical_environment(),numerical_threads=4,cases=parent['cases'],
        scientific_decision='abstain',production_promotion=False)
    e.base.follow.atomic_json(OUTPUT/'manifest.json',value);return value


def verify():
    e=engine();value=load(OUTPUT/'manifest.json')
    if value['version']!=VERSION or value['plan']['maximum_starts']!=8 or value['plan']['maximum_native_sweeps']!=1296:
        raise ValueError('finite matched scope mismatch')
    for group in ('sources','inputs','originals'): e.prior.checks(value[group])
    e.base.runtime.check_environment(value['environment']);check_qualification()
    for name,h in value['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(name).name)!=h: raise ValueError('source snapshot mismatch')
    for name,h in value['reused_artifacts'].items():
        if sha(OUTPUT/name)!=h: raise ValueError('reused artifact mismatch')
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--detach',action='store_true')
    parser.add_argument('--package-only',action='store_true');args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    if args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX)
            with (OUTPUT/'worker.lock').open('a+') as lock:
                try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: print('Matched trial already running.');return
            if (OUTPUT/'completion.json').exists(): raise ValueError('completed trial cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                                       stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(pid=child.pid,state='launched',maximum_starts=8,numerical_threads=4)))
    elif args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.package_only: engine().publish()
    else: engine().run()


if __name__=='__main__': main()
