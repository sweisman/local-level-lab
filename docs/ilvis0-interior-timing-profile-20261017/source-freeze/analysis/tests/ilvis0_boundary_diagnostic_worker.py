# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite all-six timing-only diagnostics, with precharged native calls."""
import argparse
import copy
import fcntl
import gzip
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
OUTPUT=ROOT/'data/ilvis0-boundary-diagnostic-20261016'
GUIDE=ROOT/'docs/ilvis0-boundary-diagnostic-20261016'
PREPARATION=ROOT/'docs/ilvis0-boundary-adapter-preparation-20261016'
CLOCK=ROOT/'docs/ilvis0-timing-trial-20261016'
QUALIFICATIONS=tuple(ROOT/'docs'/n for n in ('ilvis0-boundary-adapter-qualification-20261016','ilvis0-boundary-native-qualification-20261016'))
VERSION='ilvis0-all-six-boundary-diagnostic-v1'
_engine=None


def load(path):return json.loads(Path(path).read_text())


def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


def make_plan(parent,clock,summary):
    endpoints=copy.deepcopy(parent['tasks'])
    if (len(endpoints)!=22 or len({t['identity'] for t in endpoints})!=22
            or len({t['task']['segment_id'] for t in endpoints})!=6):raise ValueError('fixed six-stretch population required')
    unfinished=[t for t in endpoints if not t['fit']['converged']]
    untouched=[t for t in endpoints if t['fit']['converged']]
    if (len(unfinished)!=19 or len(untouched)!=3 or any(t['identity'].rsplit('::',1)[-1]!='repeat' for t in untouched)
            or sum(t['identity'].rsplit('::',1)[-1]=='primary' for t in unfinished)!=11):raise ValueError('fixed unfinished endpoint population required')
    tasks=[]
    for item in unfinished:
        item['source_identity']=item['identity'];item['identity']+='::boundary_diagnostic';item['kind']='time_only';tasks.append(item)
    controls=[t for t in clock['plan']['tasks'] if t['role']=='control']
    if len(controls)!=2:raise ValueError('exact two controls required')
    for task in controls:
        fit=copy.deepcopy(summary['results'][task['identity']])
        if not fit['converged']:raise ValueError('passing original controls required')
        tasks.append(dict(identity=task['identity']+'::boundary_diagnostic',source_identity=task['identity'],kind='control',
                          task=copy.deepcopy(task),fit=fit,stage=CLOCK.name,time_scale_s=.15))
    tasks.sort(key=lambda t:t['kind']!='control')
    return dict(version=VERSION,tasks=tasks,untouched_passing_repeats=untouched,
        maximum_starts=21,maximum_time_only_starts=19,maximum_joint_nuisance_fit_starts=0,
        maximum_native_evaluations=546,maximum_evaluations_per_identity=26,
        maximum_clock_queries_per_identity=201024,numerical_threads=4,retries=0)


def engine():
    global _engine
    if _engine is not None:return _engine
    sys.path.insert(0,str(ROOT/'analysis'));sys.path.insert(0,str(ROOT/'analysis/tests'))
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    spec=importlib.util.spec_from_file_location('_boundary_diagnostic_engine',ROOT/'analysis/tests/ilvis0_precision_continuation_worker.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);_engine=value;return value


def seal(directory,artifact,key):
    complete=load(directory/'completion.json');receipt=load(directory/'evidence-receipt.json')
    if (complete['state']!='complete' or complete['manifest_sha256']!=sha(directory/'manifest.json')
            or complete[key]!=sha(directory/artifact)):raise ValueError('sealed dependency mismatch')
    for name,digest in receipt['artifacts'].items():
        if Path(name).name!=name or sha(directory/name)!=digest:raise ValueError('published dependency mismatch')


def prepare():
    if (OUTPUT/'manifest.json').exists():return verify()
    OUTPUT.mkdir(exist_ok=True);e=engine()
    seal(PREPARATION,'summary.json','summary_sha256');seal(CLOCK,'summary.json','summary_sha256')
    sources={};inputs={}
    for directory,count in zip(QUALIFICATIONS,(30,2)):
        seal(directory,'result.json','result_sha256');r=load(directory/'result.json')
        if not r['passed'] or r['tests']!=count or r['errors'] or r['failures'] or r['skipped']:raise ValueError('complete adapter qualifications required')
        sources.update(load(directory/'manifest.json')['sources'])
    parent=load(PREPARATION/'manifest.json');clock=load(CLOCK/'manifest.json')
    plan=make_plan(parent,clock,load(CLOCK/'summary.json'))
    inputs.update(parent['inputs'])
    for directory,names in ((PREPARATION,('manifest.json','summary.json','completion.json','evidence-receipt.json')),
                            (CLOCK,('manifest.json','summary.json','completion.json','evidence-receipt.json')),
                            *((q,('manifest.json','result.json','completion.json','evidence-receipt.json','tests.xml')) for q in QUALIFICATIONS),
                            (GUIDE,('PLAN.md',))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    for path in (Path(__file__),ROOT/'analysis/tests/test_ilvis0_boundary_diagnostic_worker.py'):
        sources[str(path)]=sha(path)
    known={}
    for directory in {ROOT/'docs'/t['stage'] for t in plan['tasks']}:
        known.update(load(directory/'manifest.json')['originals'])
    originals={t['task']['selected']['source_path']:known[t['task']['selected']['source_path']] for t in plan['tasks']}
    _,meta=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if meta!=clock['extended_kernel']:raise ValueError('qualified native integration changed')
    snapshots={n:str(Path(n).relative_to(ROOT)) for n in sources}
    for name,digest in sources.items():
        if sha(name)!=digest:raise ValueError('qualified source changed: '+name)
        target=OUTPUT/'source-freeze'/snapshots[name];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(name,target)
    shutil.copyfile(OUTPUT/'kernel'/meta['source_file'],OUTPUT/'source-freeze'/meta['source_file'])
    value=dict(version=VERSION,plan=plan,sources=sources,source_snapshots=snapshots,inputs=inputs,originals=originals,
        extended_kernel=meta,ordinary_value_kernel=clock['ordinary_value_kernel'],environment=e.base.runtime.numerical_environment(),
        numerical_threads=4,original_labels_changed=False,scientific_decision='abstain',production_promotion=False)
    e.base.follow.atomic_json(OUTPUT/'manifest.json',value)
    e.base.follow.atomic_json(OUTPUT/'authorization.json',dict(scope='approved bounded recovery diagnostic roadmap',
        maximum_starts=21,maximum_time_only_starts=19,maximum_native_evaluations=546,numerical_threads=4,retries=0,
        manifest_sha256=sha(OUTPUT/'manifest.json')))
    return value


def verify(*,originals=True):
    value=load(OUTPUT/'manifest.json');e=engine()
    if value['version']!=VERSION or value['plan']['maximum_native_evaluations']!=546 or value['plan']['maximum_starts']!=21:
        raise ValueError('finite diagnostic scope mismatch')
    for section in ('sources','inputs',*(['originals'] if originals else [])):e.prior.checks(value[section])
    e.base.runtime.check_environment(value['environment'])
    for name,digest in value['sources'].items():
        if sha(OUTPUT/'source-freeze'/value['source_snapshots'][name])!=digest:raise ValueError('source snapshot mismatch')
    if sha(OUTPUT/'source-freeze'/value['extended_kernel']['source_file'])!=value['extended_kernel']['source_sha256']:
        raise ValueError('generated native snapshot mismatch')
    authorization=load(OUTPUT/'authorization.json')
    if authorization['manifest_sha256']!=sha(OUTPUT/'manifest.json') or any(authorization[k]!=value['plan'][k] for k in (
        'maximum_starts','maximum_time_only_starts','maximum_native_evaluations','numerical_threads','retries')):
        raise ValueError('finite authorization mismatch')
    return value


def assert_launchable():
    if (OUTPUT/'completion.json').exists():raise ValueError('completed diagnostic cannot restart')


def publish():
    seal_runtime=load(OUTPUT/'completion.json')
    if seal_runtime['manifest_sha256']!=sha(OUTPUT/'manifest.json') or seal_runtime['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed diagnostic mismatch')
    summary=load(OUTPUT/'summary.json');names=['manifest.json','authorization.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl']
    for name,digest in seal_runtime['journal_hashes'].items():
        if Path(name).name!=name or sha(OUTPUT/name)!=digest:raise ValueError('completed journal artifact mismatch')
    for item in summary['results']:
        if item.get('linearization_file'):
            name=item['linearization_file']
            if Path(name).name!=name or sha(OUTPUT/name)!=item['linearization_sha256']:raise ValueError('native artifact mismatch')
            names.append(name)
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    text='# Timing-boundary diagnostic results\n\n'
    text+=f"Completed {len(summary['results'])} identities with {summary['native_evaluations']} native evaluations. "
    text+='These are local timing and stopping diagnostics, not new scientific model comparisons. Original labels remain unchanged.\n\n'
    text+='| Stretch | Endpoint | Kind | Diagnostic passed | Native calls | Outcome |\n|---|---|---|---|---:|---|\n'
    for item in summary['results']:
        text+=f"| `{item['segment_id']}` | {item['source_identity'].split('::',1)[1]} | {item['kind']} | {item.get('passed',False)} | {item['native_evaluations']} | {item.get('reason',item['status'])} |\n"
    text+='\nThe three already-passing smooth repeats remain untouched. Any recovered numerical comparison still requires all model/case companions and scheduled repeat checks.\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    engine().base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},
        native_evaluations=summary['native_evaluations'],original_labels_changed=False,scientific_decision='abstain'))


def run():
    from contextlib import ExitStack
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for path in (OUTPUT/'worker.lock',*(ROOT/'data'/p.name/'worker.lock' for p in (CLOCK,PREPARATION,*QUALIFICATIONS))):
            lock=stack.enter_context(path.open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert_launchable();manifest=prepare();verify();e=engine();base=e.base
        from lll import ilvis0_boundary_adapter as adapter,ilvis0_solver_position as position
        from lll.ilvis0_solver_refinement import projected_stationarity
        import numpy as np
        digest=sha(OUTPUT/'manifest.json');tasks=manifest['plan']['tasks']
        book=e.prior.journal.Ledger(OUTPUT,digest,[t['identity'] for t in tasks],fit_limit=1,diagnostic_limit=26)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tmeta=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=manifest['ordinary_value_kernel'] or tmeta!=manifest['extended_kernel']:raise ValueError('native binary/environment mismatch')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={c['case_id']:c for c in base.primary_cases()};assumptions={a.name:a for a in base.sensitivity.assumptions()}
        results=[]
        for item in tasks:
            verify(originals=False);identity=item['identity'];target=OUTPUT/(identity.replace('::','-')+'.json');began=time.monotonic()
            cached=base.cached(target,digest)
            if cached is not None:results.append(cached);continue
            result=dict(identity=identity,source_identity=item['source_identity'],segment_id=item['task']['segment_id'],kind=item['kind'],passed=False)
            if item['kind']=='time_only' and any(r['kind']=='control' and not r['passed'] for r in results):
                result.update(status='not_started',reason='control_failed_no_start')
            elif identity in {r['identity'] for r in book.read('starts')}:result.update(status='interrupted',reason='charged_start_no_retry')
            else:
                book.start(identity)
                base.follow.atomic_json(OUTPUT/'status.json',dict(state='diagnosing',pid=os.getpid(),identity=identity,
                    completed=len(results),total=21,allocated_numerical_threads=4,native_evaluations=len(book.read('sweeps'))))
                try:
                    task=item['task'];chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:raise ValueError('frozen extraction provenance mismatch')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                    covariance=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumptions['h1_v3_tau60'])
                    initial,_=base.corpus.initialize(times,gps,values,task['model'])
                    problem=base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,initial,
                        base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
                        gravity_mps2=9.81,disc_radius_m=6371000.)
                    reference=item['fit'];point=np.asarray(reference['normalized_parameters']);cache={}
                    if list(problem.bounds.active)!=reference['active_parameters']:raise ValueError('frozen parameter order mismatch')
                    def evaluate(u,*,fresh=False):
                        if not fresh:raise ValueError('native callback must be fresh')
                        value=book.call(identity,'diagnostic','tangent',problem.residual_tangent,u,task['model'])
                        cache[tuple(u)]=value
                        if len(cache)==1:
                            cost=float(value[0]@value[0]);old=reference['residual_sum_squares']
                            if abs(cost-old)/max(old,cost,1.)>1e-8:raise ValueError('saved central objective failed reproduction')
                        return value
                    physical=lambda d:position.physical_residual_step(problem,d)
                    if item['kind']=='time_only':
                        result.update(adapter.diagnose(point,evaluate,physical,time_index=list(problem.bounds.active).index('time_offset'),
                            times=times,packet_count=len(values),scale=problem.bounds.limits['time_offset']))
                    else:
                        r,j,_=evaluate(point,fresh=True);repeated,_,_=evaluate(point,fresh=True)
                        repeat=adapter.displacement_metrics(r,repeated,physical)
                        gate=position.verify_stability(point,r,j,evaluate,physical)
                        result.update(passed=bool(repeat['passed'] and gate['passed']),reason=gate['reason'],
                            original_repeat=repeat,smooth_check=gate,normalized_parameters=point.tolist(),
                            stationarity=projected_stationarity(point,r,j)[0])
                    selected=np.asarray(result.get('normalized_parameters',point));r,j,edges=cache[tuple(selected)]
                    name=identity.replace('::','-')+'-linearization.json.gz'
                    local=dict(normalized_parameters=selected.tolist(),active_parameters=list(problem.bounds.active),
                        residual=r.tolist(),jacobian=j.tolist(),times_s=times.tolist(),gps=gps.tolist(),
                        convention='whitened residual derivative by normalized parameter',packet_boundaries=edges)
                    e.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(local,sort_keys=True,allow_nan=False).encode(),mtime=0))
                    result.update(status='complete',linearization_file=name,linearization_sha256=sha(OUTPUT/name),
                        original_converged=reference['converged'],residual_sum_squares=float(r@r))
                except Exception as error:result.update(status='error',reason=type(error).__name__+': '+str(error),passed=False)
            result.update(native_evaluations=book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-began,
                scientific_eligible=False,scientific_decision='abstain',original_labels_changed=False)
            base.save(target,result,digest);results.append(result)
            print(json.dumps(dict(completed=len(results),identity=identity,passed=result['passed'],status=result['status'],
                native_evaluations=result['native_evaluations'],elapsed_s=result['elapsed_s'])),flush=True)
        verify(originals=False);starts=book.read('starts');sweeps=book.read('sweeps')
        if len(starts)>21 or len(sweeps)>546 or any(r['phase']!='diagnostic' for r in sweeps):raise ValueError('finite accounting mismatch')
        summary=dict(version=VERSION,state='complete',results=results,native_evaluations=len(sweeps),
            charged_time_only_starts=sum(r['identity'] in {t['identity'] for t in tasks if t['kind']=='time_only'} for r in starts),
            joint_nuisance_fit_starts=0,original_labels_changed=False,scientific_decision='abstain')
        base.follow.atomic_json(OUTPUT/'summary.json',summary)
        base.follow.atomic_json(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json'),
            journal_hashes={n:sha(OUTPUT/n) for n in ('starts.jsonl','sweeps.jsonl')}))
        base.follow.atomic_json(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(sweeps),allocated_numerical_threads=0))
        publish()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--detach',action='store_true');parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    if args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.package_only:publish()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX);assert_launchable()
            with (OUTPUT/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=546,numerical_threads=4)))
    else:run()


if __name__=='__main__':main()
