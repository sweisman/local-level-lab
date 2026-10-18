# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen interior timing profile; nuisance fits never qualify free-time fits."""
import argparse
import copy
from contextlib import ExitStack
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
import traceback
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_profile_verification_worker as previous
prior=previous.prior
load,sha,write=prior.load,prior.sha,prior.write
PARENT=previous.OUTPUT
OUTPUT=ROOT/'data/ilvis0-interior-timing-profile-20261017'
GUIDE=ROOT/'docs/ilvis0-interior-timing-profile-20261017'
QUALIFICATION=OUTPUT/'software-controls'
VERSION='ilvis0-interior-timing-profile-v1'
TESTS=11


def make_plan(manifest,summary):
    tasks=manifest['plan']['tasks'];results={r['identity']:r for r in summary['results']}
    if (len(tasks)!=4 or len(results)!=4 or len(summary['pair_repeatability'])!=2
            or {p['anchor_role'] for p in summary['pair_repeatability']}!={'primary','repeat'}
            or not all(p['both_conditional_verified'] and p['agreement_passed'] for p in summary['pair_repeatability'])):
        raise ValueError('four verified endpoints and both repeat checks required')
    names=tasks[0]['fit']['active_parameters']
    for task in tasks:
        row=results.get(task['identity'])
        if (row is None or row['status']!='complete' or not row['conditional_verified']
                or task['fit']['active_parameters']!=names
                or task['task']['segment_id']!='50f24131843071ae9312c082'
                or task['task']['case_id']!='bias1_unsubtracted' or task['task']['model']!='sphere_still'):
            raise ValueError('verified unchanged target, model and parameter layout required')
    if names.count('time_offset')!=1:raise ValueError('one active timing parameter required')
    index=names.index('time_offset')
    seeds={role:next(t for t in tasks if t['anchor_role']==role and t['start_role']==role)
           for role in ('primary','repeat')}
    a,b=(seeds[role]['anchor_normalized'] for role in ('primary','repeat'))
    if a==b or not all(-1<=x<=1 for x in (a,b)):raise ValueError('two distinct feasible time anchors required')
    output=[]
    for fraction in (.25,.5,.75):
        anchor=(1-fraction)*a+fraction*b
        for role in ('primary','repeat'):
            item=copy.deepcopy(seeds[role]);point=list(item['saved_result']['normalized_parameters'])
            point[index]=anchor
            item.update(identity='50f24131843071ae9312c082::bias1_unsubtracted::sphere_still::grid_'+str(int(fraction*100))+'::from_'+role,
                fraction=fraction,kind='profile',anchor_role='grid_'+str(int(fraction*100)),start_role=role,
                anchor_normalized=anchor,start_full=point,maximum_fit_calls=80,maximum_diagnostic_calls=1)
            output.append(item)
    return dict(version=VERSION,tasks=output,maximum_starts=6,maximum_native_evaluations=486,
        maximum_pair_comparisons=3,maximum_fitting_calls_per_identity=80,numerical_threads=4,retries=0,
        reuse_completed_controls=True,conditional_only=True)


def fit_profile(book,identity,problem,model,start_full,anchor,physical_step):
    from types import SimpleNamespace
    from lll.ilvis0_fixed_time_profile import FixedTimeProblem
    from lll import ilvis0_solver_trust_v2 as solver
    native=problem.residual_tangent
    view=FixedTimeProblem(SimpleNamespace(bounds=problem.bounds,
        residual_tangent=lambda u,m:book.call(identity,'fit','tangent',native,u,m)),anchor)
    fitted=solver.fit_candidate(view,model,start=view.reduce(start_full),maximum_evaluations=80,physical_step=physical_step)
    final=view.lift(fitted['normalized_parameters'])
    r,j,edges=book.call(identity,'diagnostic','tangent',native,final,model)
    cost=float(r@r)
    if abs(cost-fitted['residual_sum_squares'])/max(cost,fitted['residual_sum_squares'],1.)>1e-8:
        raise ValueError('fresh final profile objective changed')
    fitted.pop('local_linearization',None)
    fitted.update(conditional_converged=bool(fitted.pop('converged')),free_time_converged=False,
        normalized_parameters=final.tolist(),active_parameters=list(problem.bounds.active),
        free_active_parameters=list(view.bounds.active),residual_sum_squares=cost,
        full_timing_gradient=float(j[:,view.index]@r),center_native=(r,j,edges))
    return fitted


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name in ('analysis/tests/ilvis0_timing_profile_worker.py','analysis/tests/test_ilvis0_timing_profile_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    prior.check_hashes(values);return values


def qualify():
    QUALIFICATION.mkdir(parents=True,exist_ok=True)
    with (QUALIFICATION/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (QUALIFICATION/'start.json').exists():raise ValueError('completed/charged software batch cannot restart')
        values=sources();prior.snapshot(QUALIFICATION,values)
        write(QUALIFICATION/'manifest.json',dict(sources=values,tests=TESTS,maximum_batches=1,
            maximum_software_callbacks=256,numerical_threads=4,timeout_s=120,original_reads=0,observed_calls=0))
        write(QUALIFICATION/'start.json',dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
        command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',sys.executable,
            '-m','pytest','-q','--tb=short',str(ROOT/'analysis/tests/test_ilvis0_timing_profile_worker.py'),
            str(ROOT/'analysis/tests/test_ilvis0_profile_verification.py'),'--junitxml='+str(QUALIFICATION/'tests.xml')]
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
    return dict(scope='approved bounded timing-profile roadmap',manifest_sha256=sha(OUTPUT/'manifest.json'),
        maximum_starts=6,maximum_native_evaluations=486,numerical_threads=4,retries=0)


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    prior.sealed(PARENT,published=previous.GUIDE)
    # Both fresh smooth controls were completed in the original profile study.
    prior.sealed(previous.profile.OUTPUT,published=previous.profile.GUIDE)
    if not load(previous.profile.OUTPUT/'summary.json')['controls_passed']:raise ValueError('source controls failed')
    c=load(QUALIFICATION/'completion.json');q=load(QUALIFICATION/'result.json')
    if (not q['passed'] or q['tests']!=TESTS or c['manifest_sha256']!=sha(QUALIFICATION/'manifest.json')
            or c['result_sha256']!=sha(QUALIFICATION/'result.json')):raise ValueError('software gate failed')
    parent=load(PARENT/'manifest.json');plan=make_plan(parent,load(PARENT/'summary.json'));values=sources()
    if values!=load(QUALIFICATION/'manifest.json')['sources']:raise ValueError('qualified sources changed')
    inputs=prior.scientific_inputs(parent['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
        (previous.GUIDE,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
        (QUALIFICATION,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={t['task']['selected']['source_path']:parent['originals'][t['task']['selected']['source_path']] for t in plan['tasks']}
    prior.check_hashes(inputs);prior.check_hashes(originals)
    e=prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=parent['extended_kernel']:raise ValueError('native integration changed')
    prior.snapshot(OUTPUT,values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),extended_kernel=extended,
        ordinary_value_kernel=parent['ordinary_value_kernel'],scientific_decision='abstain',original_labels_changed=False))
    write(OUTPUT/'authorization.json',allowance());return verify()


def verify(*,originals=True):
    m=load(OUTPUT/'manifest.json')
    if m['version']!=VERSION or m['plan']!=make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json')):
        raise ValueError('finite profile plan changed')
    for key in ('sources','inputs',*(['originals'] if originals else [])):prior.check_hashes(m[key])
    for path,h in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(path).relative_to(ROOT))!=h:raise ValueError('source snapshot changed')
    if sha(OUTPUT/'source-freeze'/m['extended_kernel']['source_file'])!=m['extended_kernel']['source_sha256']:
        raise ValueError('generated native source changed')
    prior.engine().base.runtime.check_environment(m['environment'])
    if load(OUTPUT/'authorization.json')!=allowance():raise ValueError('allowance changed')
    return m


def publish():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completion changed')
    summary=load(OUTPUT/'summary.json');names=['manifest.json','authorization.json','completion.json',
        'summary.json','starts.jsonl','sweeps.jsonl','charges-index.json']
    for row in summary['results']:
        if row.get('linearization_file'):
            name=row['linearization_file']
            if Path(name).name!=name or sha(OUTPUT/name)!=row['linearization_sha256']:raise ValueError('profile artifact changed')
            names.append(name)
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    for name,h in load(OUTPUT/'charges-index.json').items():
        if '..' in Path(name).parts or Path(name).parts[0]!='charges' or sha(OUTPUT/name)!=h:raise ValueError('charge receipt changed')
    shutil.copytree(OUTPUT/'charges',GUIDE/'charges',dirs_exist_ok=True)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    for name in ('manifest.json','result.json','completion.json','tests.xml','pytest.log'):
        destination=GUIDE/'software-controls'/name;destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(QUALIFICATION/name,destination);names.append('software-controls/'+name)
    rows=summary['profile_points']
    fields=['fraction','start_role','time_offset_ms','cost','conditional_passed','full_timing_gradient','origin']
    with (GUIDE/'timing-profile.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    names.append('timing-profile.csv')
    text='# Timing-profile results\n\n'
    text+=f"Six interior fits used {summary['native_evaluations']} native calls. "
    text+='The two endpoint pairs and passing controls are reused from sealed studies.\n\n'
    text+='| Time offset (ms) | Starting solution | Cost | Conditional checks passed |\n|---:|---|---:|---|\n'
    for row in rows:text+=f"| {row['time_offset_ms']:.9f} | {row['start_role']} | {row['cost']} | {row['conditional_passed']} |\n"
    text+='\nAll grid points, both starts and failures are retained. A five-point profile is not a global optimization proof. '
    text+='Fixed-time fits do not establish free-time convergence or change the 49/0/4 findings.\n\n'
    text+='[Profile data](timing-profile.csv) · [Finite plan](PLAN.md) · [Verified endpoints](../ilvis0-profile-verification-20261017/RESULTS.md).\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (OUTPUT,PARENT,previous.profile.OUTPUT):
            lock=stack.enter_context((directory/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed timing profile cannot restart')
        m=prepare();e=prior.engine();base=e.base
        import numpy as np
        from types import SimpleNamespace
        from lll.ilvis0_receipt_journal import Ledger
        from lll import ilvis0_solver_position as position
        tasks=m['plan']['tasks'];digest=sha(OUTPUT/'manifest.json')
        book=Ledger(OUTPUT,digest,[t['identity'] for t in tasks],fit_limit=80,diagnostic_limit=1)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tmeta=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=m['ordinary_value_kernel'] or tmeta!=m['extended_kernel']:raise ValueError('kernel changed')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={r['case_id']:r for r in base.primary_cases()}
        assumption={a.name:a for a in base.sensitivity.assumptions()}['h1_v3_tau60']
        results=[]
        for item in tasks:
            verify(originals=False);identity=item['identity'];target=OUTPUT/(identity.replace('::','-')+'.json')
            cached=base.cached(target,digest)
            if cached is not None:results.append(cached);continue
            began=time.monotonic();row=dict(identity=identity,kind='profile',fraction=item['fraction'],start_role=item['start_role'],
                anchor_normalized=item['anchor_normalized'],conditional_converged=False,free_time_converged=False,
                scientific_decision='abstain',original_labels_changed=False)
            if identity in {s['identity'] for s in book.read('starts')}:row.update(status='interrupted',reason='charged_identity_no_retry')
            else:
                book.start(identity)
                write(OUTPUT/'status.json',dict(state='profiling_interior_times',pid=os.getpid(),identity=identity,
                    completed=len(results),total=6,allocated_numerical_threads=4))
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
                    checked=fit_profile(book,identity,full,task['model'],item['start_full'],item['anchor_normalized'],
                        lambda d:position.physical_residual_step(full,d))
                    r,j,edges=checked.pop('center_native');row.update(checked,status='complete')
                    name=identity.replace('::','-')+'-linearization.json.gz'
                    payload=dict(active_parameters=list(full.bounds.active),normalized_parameters=row['normalized_parameters'],
                        fixed_time_normalized=item['anchor_normalized'],residual=r.tolist(),jacobian=j.tolist(),
                        packet_boundaries=edges,times_s=times.tolist(),gps=gps.tolist())
                    e.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
                    row.update(linearization_file=name,linearization_sha256=sha(OUTPUT/name))
                except Exception as error:
                    row.update(status='error',conditional_converged=False,reason=repr(error))
                    write(OUTPUT/'last-error.json',dict(identity=identity,error=repr(error),traceback=traceback.format_exc()))
            row.update(native_evaluations=book.count(identity,'fit')+book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-began)
            base.save(target,row,digest);results.append(row)
            print(json.dumps({k:row[k] for k in ('identity','status','conditional_converged','native_evaluations','elapsed_s')}),flush=True)
        pairs=[]
        for fraction in (.25,.5,.75):
            group=[r for r in results if r['fraction']==fraction]
            pair=dict(fraction=fraction,both_conditional_fits_passed=all(r['conditional_converged'] for r in group),agreement_passed=False)
            if all(r.get('linearization_file') for r in group):
                local=[]
                for row in group:
                    if sha(OUTPUT/row['linearization_file'])!=row['linearization_sha256']:raise ValueError('comparison artifact changed')
                    with gzip.open(OUTPUT/row['linearization_file'],'rt') as stream:local.append(json.load(stream))
                gps=np.array(local[0]['gps']);times=np.array(local[0]['times_s'])
                blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
                conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov))
                pair.update(previous.profile.pair_metrics(*local,lambda d:position.physical_residual_step(conversion,d)))
            pairs.append(pair)
        verify(originals=False);calls=book.read('sweeps')
        if len(book.read('starts'))>6 or len(calls)>486:raise ValueError('finite accounting failed')
        points=[]
        parent_tasks={t['identity']:t for t in load(PARENT/'manifest.json')['plan']['tasks']}
        for row in load(PARENT/'summary.json')['results']:
            task=parent_tasks[row['identity']]
            points.append(dict(fraction=0. if row['anchor_role']=='primary' else 1.,start_role=row['start_role'],
                time_offset_ms=task['anchor_normalized']*.15*1000,cost=row['residual_sum_squares'],
                conditional_passed=row['conditional_verified'],full_timing_gradient=row['full_timing_gradient'],origin='verified_endpoint'))
        for row in results:
            points.append(dict(fraction=row['fraction'],start_role=row['start_role'],time_offset_ms=row['anchor_normalized']*.15*1000,
                cost=row.get('residual_sum_squares'),conditional_passed=row['conditional_converged'],
                full_timing_gradient=row.get('full_timing_gradient'),origin='interior_fit'))
        points.sort(key=lambda row:(row['fraction'],row['start_role']))
        write(OUTPUT/'summary.json',dict(version=VERSION,state='complete',results=results,native_evaluations=len(calls),
            pair_repeatability=pairs,profile_points=points,full_free_time_qualification=False,scientific_decision='abstain',original_labels_changed=False))
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
            if (OUTPUT/'completion.json').exists():raise ValueError('completed profile cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=486,numerical_threads=4)))
    else:
        try:run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc()))
            write(OUTPUT/'status.json',dict(state='stopped',error=repr(error),allocated_numerical_threads=0))
            raise


if __name__=='__main__':main()
