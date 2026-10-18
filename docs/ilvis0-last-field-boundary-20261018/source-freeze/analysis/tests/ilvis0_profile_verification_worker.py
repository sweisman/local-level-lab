# SPDX-License-Identifier: AGPL-3.0-or-later
"""Twelve-call saved-profile verification; no optimizer starts or retries."""
import argparse
import copy
from contextlib import ExitStack
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_fixed_time_worker as profile
prior=profile.prior
load,sha,write=prior.load,prior.sha,prior.write
PARENT=profile.OUTPUT
OUTPUT=ROOT/'data/ilvis0-profile-verification-20261017'
GUIDE=ROOT/'docs/ilvis0-profile-verification-20261017'
QUALIFICATION=OUTPUT/'software-controls'
VERSION='ilvis0-saved-profile-verification-v1'
TESTS=8


def make_plan(manifest,summary):
    if not summary['controls_passed']:raise ValueError('both completed controls must pass')
    results={r['identity']:r for r in summary['results']}
    tasks=[]
    for source in manifest['plan']['tasks']:
        if source['kind']!='profile':continue
        result=results.get(source['identity'])
        if (result is None or result['status']!='error'
                or result['reason']!='ValueError: invalid native charge'
                or not result.get('conditional_stability',{}).get('passed')
                or not result.get('normalized_parameters')
                or 'residual_sum_squares' not in result):
            raise ValueError('saved passing conditional endpoint with exact accounting failure required')
        item=copy.deepcopy(source)
        item.update(identity=source['identity']+'::verify_saved_endpoint',
                    saved_result=copy.deepcopy(result))
        item.pop('maximum_fit_calls',None);item.pop('maximum_diagnostic_calls',None)
        tasks.append(item)
    if len(tasks)!=4 or {(t['anchor_role'],t['start_role']) for t in tasks}!={
        (a,b) for a in ('primary','repeat') for b in ('primary','repeat')}:
        raise ValueError('all four crossed endpoints required')
    return dict(version=VERSION,tasks=tasks,maximum_diagnostic_identities=4,
        maximum_native_evaluations=12,maximum_optimizer_starts=0,numerical_threads=4,retries=0)


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name in ('analysis/lll/ilvis0_profile_verification.py',
                 'analysis/tests/ilvis0_profile_verification_worker.py',
                 'analysis/tests/test_ilvis0_profile_verification.py',
                 'analysis/tests/test_ilvis0_profile_verification_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    prior.check_hashes(values)
    return values


def qualify():
    QUALIFICATION.mkdir(parents=True,exist_ok=True)
    with (QUALIFICATION/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (QUALIFICATION/'start.json').exists():raise ValueError('software batch cannot restart')
        values=sources();prior.snapshot(QUALIFICATION,values)
        write(QUALIFICATION/'manifest.json',dict(sources=values,tests=TESTS,maximum_batches=1,
            maximum_test_callbacks=32,timeout_s=120,original_reads=0,observed_calls=0))
        write(QUALIFICATION/'start.json',dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
        command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',
            sys.executable,'-m','pytest','-q','--tb=short',
            str(ROOT/'analysis/tests/test_ilvis0_profile_verification.py'),
            str(ROOT/'analysis/tests/test_ilvis0_profile_verification_worker.py'),
            '--junitxml='+str(QUALIFICATION/'tests.xml')]
        with (QUALIFICATION/'pytest.log').open('w') as log:
            from ilvis0_receipt_qualification_worker import run_batch
            code=run_batch(command,log,120)
        cases=list(ET.parse(QUALIFICATION/'tests.xml').iter('testcase'))
        result=dict(passed=code==0 and len(cases)==TESTS and not any(c.find(tag) is not None
            for c in cases for tag in ('failure','error','skipped')),tests=len(cases),returncode=code,
            observed_calls=0,original_reads=0)
        prior.check_hashes(values);write(QUALIFICATION/'result.json',result)
        write(QUALIFICATION/'completion.json',dict(state='complete',manifest_sha256=sha(QUALIFICATION/'manifest.json'),
            result_sha256=sha(QUALIFICATION/'result.json')))
        print(json.dumps(result))


def allowance():
    return dict(scope='approved finite diagnostic roadmap; saved endpoints only',
        manifest_sha256=sha(OUTPUT/'manifest.json'),maximum_diagnostic_identities=4,
        maximum_native_evaluations=12,maximum_optimizer_starts=0,numerical_threads=4,retries=0)


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    prior.sealed(PARENT,published=profile.GUIDE)
    q=load(QUALIFICATION/'result.json');c=load(QUALIFICATION/'completion.json')
    if (not q['passed'] or q['tests']!=TESTS or c['result_sha256']!=sha(QUALIFICATION/'result.json')
            or c['manifest_sha256']!=sha(QUALIFICATION/'manifest.json')):raise ValueError('software gate failed')
    parent=load(PARENT/'manifest.json');summary=load(PARENT/'summary.json');plan=make_plan(parent,summary)
    values=sources()
    if values!=load(QUALIFICATION/'manifest.json')['sources']:raise ValueError('qualified sources changed')
    inputs=prior.scientific_inputs(parent['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
        (profile.GUIDE,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
        (QUALIFICATION,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={t['task']['selected']['source_path']:parent['originals'][t['task']['selected']['source_path']]
               for t in plan['tasks']}
    prior.check_hashes(inputs);prior.check_hashes(originals)
    engine=prior.engine();_,extended=engine.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=parent['extended_kernel']:raise ValueError('integration source changed')
    prior.snapshot(OUTPUT,values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=engine.base.runtime.numerical_environment(),extended_kernel=extended,
        ordinary_value_kernel=parent['ordinary_value_kernel'],scientific_decision='abstain',
        original_labels_changed=False))
    write(OUTPUT/'authorization.json',allowance())
    return verify()


def verify(*,originals=True):
    m=load(OUTPUT/'manifest.json')
    if m['version']!=VERSION or m['plan']!=make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json')):
        raise ValueError('frozen verification scope changed')
    for key in ('sources','inputs',*(['originals'] if originals else [])):prior.check_hashes(m[key])
    for path,h in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(path).relative_to(ROOT))!=h:raise ValueError('source copy changed')
    if sha(OUTPUT/'source-freeze'/m['extended_kernel']['source_file'])!=m['extended_kernel']['source_sha256']:
        raise ValueError('kernel snapshot changed')
    prior.engine().base.runtime.check_environment(m['environment'])
    if load(OUTPUT/'authorization.json')!=allowance():raise ValueError('allowance changed')
    return m


def publish():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completion changed')
    summary=load(OUTPUT/'summary.json')
    names=['manifest.json','authorization.json','completion.json','summary.json','starts.jsonl','sweeps.jsonl','charges-index.json']
    for row in summary['results']:
        if row.get('linearization_file'):
            name=row['linearization_file']
            if Path(name).name!=name or sha(OUTPUT/name)!=row['linearization_sha256']:raise ValueError('artifact changed')
            names.append(name)
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    for name,h in load(OUTPUT/'charges-index.json').items():
        if '..' in Path(name).parts or Path(name).parts[0]!='charges' or sha(OUTPUT/name)!=h:
            raise ValueError('invalid charge receipt')
    shutil.copytree(OUTPUT/'charges',GUIDE/'charges',dirs_exist_ok=True)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    for name in ('manifest.json','result.json','completion.json','tests.xml','pytest.log'):
        destination=GUIDE/'software-controls'/name;destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(QUALIFICATION/name,destination);names.append('software-controls/'+name)
    text='# Saved fixed-time endpoint checks\n\n'
    text+=f"{len(summary['results'])} endpoints checked using {summary['native_evaluations']} native calls and no refits. "
    text+='Earlier accounting failures remain recorded; these are separate fresh diagnostics.\n\n'
    text+='| Fixed time / starting solution | Conditional checks passed | Cost | Timing gradient |\n|---|---|---:|---:|\n'
    for row in summary['results']:
        text+=f"| {row['anchor_role']} / {row['start_role']} | {row['conditional_verified']} | {row.get('residual_sum_squares','')} | {row.get('full_timing_gradient','')} |\n"
    text+='\n| Fixed time | Both endpoints verified | Within-anchor repeat agreement |\n|---|---|---|\n'
    for row in summary['pair_repeatability']:
        text+=f"| {row['anchor_role']} | {row['both_conditional_verified']} | {row.get('agreement_passed',False)} |\n"
    text+='\nFixed-time completion does not establish full free-time convergence or change the 49/0/4 disposition.\n'
    (GUIDE/'RESULTS.md').write_text(text)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in (*names,'RESULTS.md')},scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (OUTPUT,PARENT):
            lock=stack.enter_context((directory/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed verification cannot restart')
        m=prepare();engine=prior.engine();base=engine.base
        import numpy as np
        from types import SimpleNamespace
        from lll.ilvis0_profile_verification import verify_endpoint
        from lll.ilvis0_receipt_journal import Ledger
        from lll import ilvis0_solver_position as position
        tasks=m['plan']['tasks'];digest=sha(OUTPUT/'manifest.json')
        book=Ledger(OUTPUT,digest,[t['identity'] for t in tasks],fit_limit=1,diagnostic_limit=3)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tmeta=engine.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=m['ordinary_value_kernel'] or tmeta!=m['extended_kernel']:raise ValueError('kernel changed')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={r['case_id']:r for r in base.primary_cases()}
        assumption={a.name:a for a in base.sensitivity.assumptions()}['h1_v3_tau60']
        results=[]
        for item in tasks:
            verify(originals=False);identity=item['identity'];began=time.monotonic()
            target=OUTPUT/(identity.replace('::','-')+'.json');cached=base.cached(target,digest)
            if cached is not None:results.append(cached);continue
            row=dict(identity=identity,anchor_role=item['anchor_role'],start_role=item['start_role'],
                conditional_verified=False,free_time_converged=False,original_labels_changed=False)
            if identity in {s['identity'] for s in book.read('starts')}:
                row.update(status='interrupted',reason='charged_identity_no_retry')
            else:
                book.start(identity)
                write(OUTPUT/'status.json',dict(state='verifying_saved_endpoints',pid=os.getpid(),completed=len(results),
                    total=4,allocated_numerical_threads=4,identity=identity))
                try:
                    task=item['task'];chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:raise ValueError('extraction changed')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                    cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
                    initial,_=base.corpus.initialize(times,gps,values,task['model'])
                    full=base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,cov,initial,
                        base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    if list(full.bounds.active)!=item['fit']['active_parameters']:raise ValueError('parameter layout changed')
                    physical=lambda d:position.physical_residual_step(full,d)
                    checked=verify_endpoint(book,identity,full.residual_tangent,task['model'],full.bounds,
                        item['saved_result']['normalized_parameters'],item['anchor_normalized'],physical)
                    r,j,edges=checked.pop('center_native');cost=float(r@r);saved=item['saved_result']['residual_sum_squares']
                    if abs(cost-saved)/max(cost,saved,1.)>1e-8:raise ValueError('saved endpoint objective changed')
                    row.update(checked,status='complete',residual_sum_squares=cost)
                    name=identity.replace('::','-')+'-linearization.json.gz'
                    payload=dict(active_parameters=list(full.bounds.active),normalized_parameters=item['saved_result']['normalized_parameters'],
                        fixed_time_normalized=item['anchor_normalized'],residual=r.tolist(),jacobian=j.tolist(),
                        packet_boundaries=edges,times_s=times.tolist(),gps=gps.tolist())
                    engine.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
                    row.update(linearization_file=name,linearization_sha256=sha(OUTPUT/name))
                except Exception as error:
                    row.update(status='error',conditional_verified=False,reason=repr(error))
                    write(OUTPUT/'last-error.json',dict(identity=identity,error=repr(error),traceback=traceback.format_exc()))
            row.update(native_evaluations=book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-began)
            base.save(target,row,digest);results.append(row)
            print(json.dumps({k:row[k] for k in ('identity','status','conditional_verified','native_evaluations')}),flush=True)
        pairs=[]
        for anchor in ('primary','repeat'):
            group=[r for r in results if r['anchor_role']==anchor]
            pair=dict(anchor_role=anchor,both_conditional_verified=all(r['conditional_verified'] for r in group),agreement_passed=False)
            if all(r.get('linearization_file') for r in group):
                local=[]
                for row in group:
                    if sha(OUTPUT/row['linearization_file'])!=row['linearization_sha256']:raise ValueError('comparison artifact changed')
                    with gzip.open(OUTPUT/row['linearization_file'],'rt') as stream:local.append(json.load(stream))
                gps=np.array(local[0]['gps']);times=np.array(local[0]['times_s'])
                blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
                conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov))
                pair.update(profile.pair_metrics(*local,lambda d:position.physical_residual_step(conversion,d)))
            pairs.append(pair)
        verify(originals=False);calls=book.read('sweeps')
        if len(calls)>12 or any(c['phase']!='diagnostic' or c['kind']!='tangent' for c in calls):
            raise ValueError('diagnostic-only accounting failed')
        write(OUTPUT/'summary.json',dict(version=VERSION,state='complete',results=results,native_evaluations=len(calls),
            optimizer_starts=0,pair_repeatability=pairs,full_free_time_qualification=False,original_labels_changed=False,
            scientific_decision='abstain'))
        book.export();write(OUTPUT/'charges-index.json',{str(p.relative_to(OUTPUT)):sha(p) for p in (OUTPUT/'charges').glob('*.json')})
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json')))
        write(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(calls),allocated_numerical_threads=0))
        publish()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('qualify','prepare-only','detach','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    if args.qualify:qualify()
    elif args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.package_only:publish()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with (OUTPUT/'worker.lock').open('a+') as worker:fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'completion.json').exists():raise ValueError('completed verification cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=12,optimizer_starts=0,numerical_threads=4)))
    else:
        try:run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc()))
            write(OUTPUT/'status.json',dict(state='stopped',error=repr(error),allocated_numerical_threads=0))
            raise


if __name__=='__main__':main()
