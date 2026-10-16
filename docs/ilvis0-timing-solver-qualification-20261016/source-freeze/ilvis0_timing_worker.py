# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three frozen endpoints, at most 34 native predictions, zero optimizer starts."""
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
import time

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'data/ilvis0-timing-derivative-20261016'
GUIDE=ROOT/'docs/ilvis0-timing-derivative-20261016'
PARENT=ROOT/'docs/ilvis0-trust-trial-20261015'
AUDIT=ROOT/'docs/ilvis0-final-stability-audit-20261015'
PREFIX='fd7b81e48a4122b149c4925b::bias1_profiled_removal::sphere_still::'
CONTROL='233183f67270980491416678::bias1_unsubtracted::sphere_rotating::control'
VERSION='ilvis0-native-timing-check-v1'
_engine=None


def load(path):return json.loads(path.read_text())


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def select_tasks(parent,summary,audit):
    original={t['identity']:t for t in parent['plan']['tasks']}
    corrections={r['identity']:next(m['step'] for m in r['audit']['methods'] if m['method']=='original_bvls')
                 for r in audit['results']}
    tasks=[]
    for identity in (CONTROL,PREFIX+'primary',PREFIX+'repeat'):
        ref=summary['results'][identity]
        if bool(ref['converged'])!=(identity==CONTROL):raise ValueError('fixed control/failure labels required')
        correction=None if identity==CONTROL else corrections[identity]
        tasks.append(dict(copy.deepcopy(original[identity]),reference=ref,correction=correction,
                          maximum_native_evaluations=10 if correction is None else 12))
    return tasks


def engine():
    global _engine
    if _engine is not None:return _engine
    sys.path.insert(0,str(ROOT/'analysis'));sys.path.insert(0,str(ROOT/'analysis/tests'))
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    spec=importlib.util.spec_from_file_location('_timing_engine',ROOT/'analysis/tests/ilvis0_precision_continuation_worker.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);_engine=value
    return value


def prepare():
    if (OUTPUT/'manifest.json').exists():return verify()
    e=engine()
    from lll import ilvis0_timing_probes as probes
    parent=load(PARENT/'manifest.json');summary=load(PARENT/'summary.json')
    inputs=dict(parent['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json','evidence-receipt.json')),
                            (AUDIT,('manifest.json','diagnosis.json','completion.json','evidence-receipt.json')),
                            (GUIDE,('PLAN.md',))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    for directory in (PARENT,AUDIT):
        receipt=load(directory/'evidence-receipt.json')
        if any(sha(directory/n)!=h for n,h in receipt['artifacts'].items()):raise ValueError('sealed evidence mismatch')
    complete=load(PARENT/'completion.json')
    if complete['manifest_sha256']!=sha(PARENT/'manifest.json') or complete['summary_sha256']!=sha(PARENT/'summary.json'):
        raise ValueError('parent completion mismatch')
    tasks=select_tasks(parent,summary,load(AUDIT/'diagnosis.json'))
    sources=dict(parent['sources'])
    for path in (Path(__file__),Path(probes.__file__),ROOT/'analysis/tests/test_ilvis0_timing_probes.py',
                 ROOT/'analysis/tests/test_ilvis0_timing_worker.py'):
        sources[str(path.resolve())]=sha(path)
    originals={t['selected']['source_path']:parent['originals'][t['selected']['source_path']] for t in tasks}
    for group in (sources,inputs,originals):e.prior.checks(group)
    _,meta=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if meta!=parent['extended_kernel']:raise ValueError('qualified arithmetic changed')
    freeze=OUTPUT/'source-freeze';freeze.mkdir(exist_ok=True)
    if len({Path(p).name for p in sources})!=len(sources):raise ValueError('source snapshot collision')
    for name in sources:shutil.copyfile(name,freeze/Path(name).name)
    shutil.copyfile(OUTPUT/'kernel'/meta['source_file'],freeze/meta['source_file'])
    value=dict(version=VERSION,tasks=tasks,sources=sources,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),numerical_threads=4,extended_kernel=meta,
        value_kernel=parent['ordinary_value_kernel'],maximum_identities=3,maximum_native_evaluations=34,
        observed_fit_starts=0,retries=0,steps_s=list(probes.STEPS_S),scientific_decision='abstain')
    e.base.follow.atomic_json(OUTPUT/'manifest.json',value);return value


def verify():
    value=load(OUTPUT/'manifest.json');e=engine()
    if value['version']!=VERSION or value['maximum_native_evaluations']!=34 or len(value['tasks'])!=3:
        raise ValueError('finite timing scope mismatch')
    for group in ('sources','inputs','originals'):e.prior.checks(value[group])
    e.base.runtime.check_environment(value['environment'])
    for name,digest in value['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(name).name)!=digest:raise ValueError('source snapshot mismatch')
    meta=value['extended_kernel']
    if sha(OUTPUT/'source-freeze'/meta['source_file'])!=meta['source_sha256']:raise ValueError('generated source mismatch')
    return value


def package():
    complete=load(OUTPUT/'completion.json')
    if complete['manifest_sha256']!=sha(OUTPUT/'manifest.json') or complete['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed evidence mismatch')
    for name,digest in complete['journal_hashes'].items():
        if sha(OUTPUT/name)!=digest:raise ValueError('journal mismatch')
    names=('manifest.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl')
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    summary=load(OUTPUT/'summary.json')
    text='# Native timing-derivative checks\n\n'
    text+=f"Completed {len(summary['results'])} endpoints / {summary['native_evaluations']} native calls, with zero optimizer starts. "
    text+='These fixed-endpoint diagnostics preserve every scientific disposition and stopping limit.\n\n'
    text+='| Endpoint | Time step (ms) | Centered derivative relative error | Left/right difference | Packet changes − / + |\n'
    text+='|---|---:|---:|---:|---:|\n'
    for r in summary['results']:
        if r['status']!='complete':text+=f"| {r['identity']} | error | — | — | — |\n";continue
        for p in r['time_probes']:
            text+=f"| {r['identity'].split('::')[-1]} | {p['step_s']*1000:g} | {p['centered_derivative_relative_error']:.6g} | {p['left_right_derivative_relative_difference']:.6g} | {p['minus_changed_packet_epochs']} / {p['plus_changed_packet_epochs']} |\n"
    text+='\nThe smallest steps can encounter floating-point subtraction limits. Large-step differences may '
    text+='reflect real changes between adjacent measured increments; neither is automatically a derivative defect. '
    text+='The saved [measurements](summary.json) include per-axis errors, signed objective changes, '
    text+='packet distances and full/half coupled corrections. No result is relabeled.\n'
    (GUIDE/'RESULTS.md').write_text(text)
    engine().base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(
        artifacts={n:sha(GUIDE/n) for n in (*names,'RESULTS.md')},observed_fit_starts=0,
        native_evaluations=summary['native_evaluations'],scientific_decision='abstain'))


def run():
    e=engine()
    import numpy as np
    from lll import ilvis0_timing_probes as probes
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed diagnostic cannot restart')
        manifest=verify();digest=sha(OUTPUT/'manifest.json')
        book=e.prior.journal.Ledger(OUTPUT,digest,[t['identity'] for t in manifest['tasks']],fit_limit=1,diagnostic_limit=12)
        kernel,km=e.base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tm=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if km!=manifest['value_kernel'] or tm!=manifest['extended_kernel']:raise ValueError('kernel mismatch')
        contexts={r['task_id']:r for r in e.base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={c['case_id']:c for c in e.base.primary_cases()}
        assumptions={a.name:a for a in e.base.sensitivity.assumptions()};results=[]
        for task in manifest['tasks']:
            verify();identity=task['identity'];target=OUTPUT/(identity.replace('::','-')+'.json')
            saved=e.base.cached(target,digest)
            if saved is not None:results.append(saved);continue
            begin=time.monotonic()
            if identity in {r['identity'] for r in book.read('starts')}:
                result=dict(identity=identity,status='interrupted',retry=False)
            else:
                book.start(identity)
                e.base.follow.atomic_json(OUTPUT/'status.json',dict(state='timing_checks',pid=os.getpid(),identity=identity,completed=len(results),total=3))
                try:
                    chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=e.base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:raise ValueError('saved extraction provenance mismatch')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                    covariance=e.base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumptions['h1_v3_tau60'])
                    initial,_=e.base.corpus.initialize(times,gps,values,task['model'])
                    problem=e.base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,initial,
                        e.base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    if list(problem.bounds.active)!=task['reference']['active_parameters']:raise ValueError('saved parameter order mismatch')
                    def call(fn,*args):
                        if book.count(identity,'diagnostic')>=task['maximum_native_evaluations']:
                            raise ValueError('endpoint allowance exhausted')
                        return book.call(identity,'diagnostic','tangent',fn,*args)
                    result=probes.inspect(problem,task['reference']['normalized_parameters'],task['model'],call,correction=task['correction'])
                    if abs(result['center_cost']-task['reference']['residual_sum_squares'])>1e-8*max(result['center_cost'],1.):
                        raise ValueError('saved objective did not reproduce')
                    result.update(identity=identity,status='complete',original_converged=task['reference']['converged'])
                except Exception as error:result=dict(identity=identity,status='error',error=type(error).__name__+': '+str(error))
            result.update(native_evaluations=book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-begin)
            e.base.save(target,result,digest);results.append(result)
            print(json.dumps(dict(identity=identity,status=result['status'],completed=len(results),elapsed_s=result['elapsed_s'])),flush=True)
        sweeps=book.read('sweeps')
        if len(sweeps)>34 or any(r['phase']!='diagnostic' for r in sweeps):raise ValueError('finite diagnostic accounting mismatch')
        summary=dict(version=VERSION,state='complete',results=results,native_evaluations=len(sweeps),
                     observed_fit_starts=0,original_labels_changed=False,scientific_decision='abstain')
        e.base.follow.atomic_json(OUTPUT/'summary.json',summary)
        e.base.follow.atomic_json(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json'),
            journal_hashes={n:sha(OUTPUT/n) for n in ('starts.jsonl','sweeps.jsonl')}))
        e.base.follow.atomic_json(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(sweeps)))
        package()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--detach',action='store_true')
    parser.add_argument('--package-only',action='store_true');args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    if args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.package_only:package()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX)
            for directory in (OUTPUT,ROOT/'data/ilvis0-hybrid-remaining-20261015',ROOT/'data/ilvis0-trust-trial-20261015'):
                with (directory/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'completion.json').exists():raise ValueError('completed diagnostic cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            engine().base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,numerical_threads=4,maximum_native_evaluations=34))
            print(json.dumps(dict(pid=child.pid,state='launched',maximum_native_evaluations=34,numerical_threads=4)))
    else:run()


if __name__=='__main__':main()
