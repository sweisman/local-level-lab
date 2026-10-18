# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite profile-seeded free-time trial; all original gates remain necessary."""
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
import ilvis0_timing_profile_worker as grid
prior=grid.prior
load,sha,write=prior.load,prior.sha,prior.write
PARENT=grid.OUTPUT
ENDPOINTS=grid.PARENT
CONTROLS=grid.previous.profile.OUTPUT
OUTPUT=ROOT/'data/ilvis0-profile-seeded-trial-20261017'
GUIDE=ROOT/'docs/ilvis0-profile-seeded-trial-20261017'
QUALIFICATION=OUTPUT/'software-controls'
VERSION='ilvis0-profile-seeded-free-time-trial-v1'
TESTS=24


def make_plan(gm,gs,vm,vs,controls):
    # Validate all ten profile fits, including both starting solutions and pairs.
    grid.make_plan(vm,vs)
    if (len(gs['results'])!=6 or len(gs['pair_repeatability'])!=3
            or {r['fraction'] for r in gs['pair_repeatability']}!={.25,.5,.75}
            or not all(r['both_conditional_fits_passed'] and r['agreement_passed'] for r in gs['pair_repeatability'])):
        raise ValueError('all interior profile pairs must pass')
    gt={t['identity']:t for t in gm['plan']['tasks']};vt={t['identity']:t for t in vm['plan']['tasks']}
    groups={role:[] for role in ('primary','repeat')}
    for directory,rows,tasks,conditional in ((PARENT,gs['results'],gt,'conditional_converged'),
                                            (ENDPOINTS,vs['results'],vt,'conditional_verified')):
        for result in rows:
            item=tasks[result['identity']];role=item['start_role']
            if result['status']!='complete' or not result[conditional]:raise ValueError('every saved profile must pass')
            point=(result['normalized_parameters'] if directory==PARENT else item['saved_result']['normalized_parameters'])
            names=(result['active_parameters'] if directory==PARENT else item['fit']['active_parameters'])
            groups[role].append(dict(anchor_normalized=item['anchor_normalized'],normalized_parameters=list(point),
                active_parameters=list(names),cost=result['residual_sum_squares'],conditional_passed=True,
                source_identity=result['identity'],evidence_file=str(directory/result['linearization_file']),
                evidence_sha256=result['linearization_sha256']))
    from lll.ilvis0_profile_seeded import select_seed
    tasks=[copy.deepcopy(t) for t in controls['plan']['tasks'] if t['kind']=='control']
    if len(tasks)!=2:raise ValueError('both fresh controls required')
    for task in tasks:
        task.update(identity=task['source_identity']+'::profile_seeded_control',maximum_fit_calls=0,maximum_diagnostic_calls=3)
    for role in ('primary','repeat'):
        source=next(t for t in vm['plan']['tasks'] if t['start_role']==role and t['anchor_role']==role)
        profiles=sorted(groups[role],key=lambda r:r['anchor_normalized']);anchors=[r['anchor_normalized'] for r in profiles]
        if len(profiles)!=5:raise ValueError('exact five-point coverage required per starting solution')
        select_seed(profiles,anchors,source['fit']['active_parameters'])
        task=copy.deepcopy(source)
        task.update(kind='target',start_role=role,identity='50f24131843071ae9312c082::bias1_unsubtracted::sphere_still::profile_seeded_'+role,
            profiles=profiles,anchors=anchors,maximum_fit_calls=81,maximum_diagnostic_calls=3)
        tasks.append(task)
    return dict(version=VERSION,tasks=tasks,maximum_starts=4,maximum_optimizer_starts=2,
        maximum_native_evaluations=174,numerical_threads=4,retries=0)


def check_full(book,identity,problem,model,point,physical_step):
    import numpy as np
    from lll.ilvis0_boundary_adapter import displacement_metrics
    from lll.ilvis0_solver_position import verify_stability
    def fresh(u,**kwargs):return book.call(identity,'diagnostic','tangent',problem.residual_tangent,np.array(u,float),model)
    point=np.array(point,float);r,j,edges=fresh(point);repeated,_,_=fresh(point)
    if (not np.all(np.isfinite(r)) or not np.all(np.isfinite(j)) or j.shape!=(len(r),len(point))):
        raise ValueError('finite compatible full native tangent required')
    repeat=displacement_metrics(r,repeated,physical_step)
    gate=verify_stability(point,r,j,fresh,physical_step)
    return dict(full_gate_verified=bool(repeat['passed'] and gate['passed']),full_repeat=repeat,
        full_stability=gate,center_native=(r,j,edges))


def fit_and_check(book,identity,problem,model,profiles,anchors,physical_step):
    from types import SimpleNamespace
    from lll import ilvis0_profile_seeded as candidate
    selected=candidate.select_seed(profiles,anchors,problem.bounds.active)
    native=problem.residual_tangent
    original,_,_=book.call(identity,'fit','tangent',native,selected['normalized_parameters'],model)
    cost=float(original@original)
    if abs(cost-selected['cost'])/max(cost,selected['cost'],1.)>1e-8:raise ValueError('saved selected profile cost changed')
    proxy=SimpleNamespace(bounds=problem.bounds,
        residual_tangent=lambda u,m:book.call(identity,'fit','tangent',native,u,m))
    result=candidate.fit_candidate(proxy,model,profiles=profiles,anchors=anchors,
        maximum_evaluations=80,physical_step=physical_step)
    result.pop('local_linearization',None)
    checked=check_full(book,identity,problem,model,result['normalized_parameters'],physical_step)
    r=checked['center_native'][0];final_cost=float(r@r)
    if (abs(final_cost-result['residual_sum_squares'])/max(final_cost,result['residual_sum_squares'],1.)>1e-8
            or (final_cost-cost)/max(final_cost,cost,1.)>1e-8):raise ValueError('fresh final objective failed reproduction or increased')
    result.update(checked)
    result['converged']=bool(result['converged'] and checked['full_gate_verified'])
    result.update(free_time_converged=result['converged'],residual_sum_squares=final_cost)
    return result


def repeat_metrics(a,b,physical_step):
    import numpy as np
    if any(a[k]!=b[k] for k in ('times_s','gps','active_parameters')):raise ValueError('common full observation layout required')
    x,y=np.array(a['residual']),np.array(b['residual']);delta=np.asarray(physical_step(y-x))
    if x.shape!=y.shape or delta.shape!=(len(a['gps']),3) or not np.all(np.isfinite(delta)):
        raise ValueError('finite common full prediction layout required')
    ca,cb=float(x@x),float(y@y);relative=abs(ca-cb)/max(ca,cb,1.);rms=np.sqrt(np.mean(delta**2,axis=0))
    return dict(relative_cost_difference=relative,track_rms_neu_m=rms.tolist(),
        agreement_passed=bool(relative<=1e-6 and np.max(rms)<=.01),global_optimum_proven=False)


def source_plan():
    return make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),
        load(ENDPOINTS/'manifest.json'),load(ENDPOINTS/'summary.json'),load(CONTROLS/'manifest.json'))


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name in ('analysis/lll/ilvis0_profile_seeded.py','analysis/tests/test_ilvis0_profile_seeded.py',
                 'analysis/tests/ilvis0_profile_seeded_worker.py','analysis/tests/test_ilvis0_profile_seeded_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    prior.check_hashes(values);return values


def qualify():
    QUALIFICATION.mkdir(parents=True,exist_ok=True)
    with (QUALIFICATION/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (QUALIFICATION/'start.json').exists():raise ValueError('charged software qualification cannot restart')
        values=sources();prior.snapshot(QUALIFICATION,values)
        write(QUALIFICATION/'manifest.json',dict(sources=values,tests=TESTS,maximum_batches=1,timeout_s=120,
            maximum_software_callbacks=4096,numerical_threads=4,original_reads=0,observed_calls=0))
        write(QUALIFICATION/'start.json',dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
        command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',sys.executable,'-m','pytest','-q','--tb=short']
        command.extend(str(ROOT/'analysis/tests'/name) for name in ('test_ilvis0_profile_seeded.py',
            'test_ilvis0_profile_seeded_worker.py','test_ilvis0_profile_verification.py'))
        command.append('--junitxml='+str(QUALIFICATION/'tests.xml'))
        with (QUALIFICATION/'pytest.log').open('w') as log:
            from ilvis0_receipt_qualification_worker import run_batch
            code=run_batch(command,log,120)
        cases=list(ET.parse(QUALIFICATION/'tests.xml').iter('testcase'))
        result=dict(passed=code==0 and len(cases)==TESTS and not any(c.find(tag) is not None
            for c in cases for tag in ('failure','error','skipped')),tests=len(cases),returncode=code,original_reads=0,observed_calls=0)
        prior.check_hashes(values);write(QUALIFICATION/'result.json',result)
        write(QUALIFICATION/'completion.json',dict(state='complete',manifest_sha256=sha(QUALIFICATION/'manifest.json'),
            result_sha256=sha(QUALIFICATION/'result.json')))
        print(json.dumps(result))


def allowance():
    return dict(scope='approved finite profile-seeded solver trial',manifest_sha256=sha(OUTPUT/'manifest.json'),
        maximum_starts=4,maximum_optimizer_starts=2,maximum_native_evaluations=174,numerical_threads=4,retries=0)


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    for runtime,public in ((PARENT,grid.GUIDE),(ENDPOINTS,grid.previous.GUIDE),(CONTROLS,grid.previous.profile.GUIDE)):
        prior.sealed(runtime,published=public)
    if not load(CONTROLS/'summary.json')['controls_passed']:raise ValueError('original controls failed')
    q=load(QUALIFICATION/'result.json');c=load(QUALIFICATION/'completion.json')
    if (not q['passed'] or q['tests']!=TESTS or c['manifest_sha256']!=sha(QUALIFICATION/'manifest.json')
            or c['result_sha256']!=sha(QUALIFICATION/'result.json')):raise ValueError('software qualification failed')
    parent=load(PARENT/'manifest.json');plan=source_plan();values=sources()
    if values!=load(QUALIFICATION/'manifest.json')['sources']:raise ValueError('qualified sources changed')
    inputs=prior.scientific_inputs(parent['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
        (grid.GUIDE,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
        (QUALIFICATION,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={}
    for task in plan['tasks']:
        source=task['task']['selected']['source_path']
        originals[source]=load(CONTROLS/'manifest.json')['originals'][source] if task['kind']=='control' else parent['originals'][source]
        for row in task.get('profiles',[]):inputs[row['evidence_file']]=row['evidence_sha256']
    prior.check_hashes(inputs);prior.check_hashes(originals)
    e=prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=parent['extended_kernel']:raise ValueError('native integration changed')
    prior.snapshot(OUTPUT,values);shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),extended_kernel=extended,ordinary_value_kernel=parent['ordinary_value_kernel'],
        scientific_decision='abstain',original_labels_changed=False))
    write(OUTPUT/'authorization.json',allowance());return verify()


def verify(*,originals=True):
    m=load(OUTPUT/'manifest.json')
    if m['version']!=VERSION or m['plan']!=source_plan():raise ValueError('finite target plan changed')
    for key in ('sources','inputs',*(['originals'] if originals else [])):prior.check_hashes(m[key])
    for path,h in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(path).relative_to(ROOT))!=h:raise ValueError('source snapshot changed')
    if sha(OUTPUT/'source-freeze'/m['extended_kernel']['source_file'])!=m['extended_kernel']['source_sha256']:
        raise ValueError('generated kernel changed')
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
            if Path(name).name!=name or sha(OUTPUT/name)!=row['linearization_sha256']:raise ValueError('native artifact changed')
            names.append(name)
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    for name,h in load(OUTPUT/'charges-index.json').items():
        if '..' in Path(name).parts or Path(name).parts[0]!='charges' or sha(OUTPUT/name)!=h:raise ValueError('charge receipt changed')
    shutil.copytree(OUTPUT/'charges',GUIDE/'charges',dirs_exist_ok=True)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    for name in ('manifest.json','result.json','completion.json','tests.xml','pytest.log'):
        target=GUIDE/'software-controls'/name;target.parent.mkdir(exist_ok=True)
        shutil.copyfile(QUALIFICATION/name,target);names.append('software-controls/'+name)
    text='# Profile-seeded free-time results\n\n'
    text+=f"Completed {len(summary['results'])} identities / {summary['native_evaluations']} native calls. Full qualification passed: {summary['qualification_passed']}.\n\n"
    text+='| Kind / starting solution | Full checks passed | Cost | Calls |\n|---|---|---:|---:|\n'
    for row in summary['results']:
        text+=f"| {row['kind']} / {row.get('start_role','control')} | {row['converged']} | {row.get('residual_sum_squares','')} | {row['native_evaluations']} |\n"
    text+='\nAll five timing candidates were retained for each starting solution. Time was then released under its original bounds. '
    text+='A successful trial still requires saved companion/model review before changing a stretch disposition. No global optimum or statistical significance is established.\n'
    text+='\n[Finite plan](PLAN.md) · [Timing profile](../ilvis0-interior-timing-profile-20261017/RESULTS.md).\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (OUTPUT,PARENT,ENDPOINTS,CONTROLS):
            lock=stack.enter_context((directory/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed trial cannot restart')
        m=prepare();e=prior.engine();base=e.base
        import numpy as np
        from types import SimpleNamespace
        from lll.ilvis0_receipt_journal import Ledger
        from lll import ilvis0_solver_position as position
        tasks=m['plan']['tasks'];digest=sha(OUTPUT/'manifest.json');results=[]
        book=Ledger(OUTPUT,digest,[t['identity'] for t in tasks],fit_limit=81,diagnostic_limit=3)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tmeta=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=m['ordinary_value_kernel'] or tmeta!=m['extended_kernel']:raise ValueError('kernel changed')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={r['case_id']:r for r in base.primary_cases()}
        assumption={a.name:a for a in base.sensitivity.assumptions()}['h1_v3_tau60']
        for item in tasks:
            verify(originals=False);identity=item['identity'];target=OUTPUT/(identity.replace('::','-')+'.json')
            cached=base.cached(target,digest)
            if cached is not None:results.append(cached);continue
            began=time.monotonic();row=dict(identity=identity,kind=item['kind'],start_role=item.get('start_role','control'),
                converged=False,scientific_decision='abstain',original_labels_changed=False)
            if item['kind']=='target' and not all(r['converged'] for r in results if r['kind']=='control'):
                row.update(status='not_started',reason='fresh_control_failed')
            elif identity in {s['identity'] for s in book.read('starts')}:row.update(status='interrupted',reason='charged_identity_no_retry')
            else:
                book.start(identity)
                write(OUTPUT/'status.json',dict(state='checking_free_time',pid=os.getpid(),identity=identity,
                    completed=len(results),total=4,allocated_numerical_threads=4))
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
                    if list(full.bounds.active)!=item['fit']['active_parameters']:raise ValueError('full parameter layout changed')
                    physical=lambda d:position.physical_residual_step(full,d)
                    if item['kind']=='target':checked=fit_and_check(book,identity,full,task['model'],item['profiles'],item['anchors'],physical)
                    else:
                        checked=check_full(book,identity,full,task['model'],item['fit']['normalized_parameters'],physical)
                        r=checked['center_native'][0];cost=float(r@r);old=item['fit']['residual_sum_squares']
                        if abs(cost-old)/max(cost,old,1.)>1e-8:raise ValueError('control objective changed')
                        checked.update(converged=checked['full_gate_verified'],normalized_parameters=item['fit']['normalized_parameters'],residual_sum_squares=cost)
                    r,j,edges=checked.pop('center_native');row.update(checked,status='complete')
                    name=identity.replace('::','-')+'-linearization.json.gz'
                    payload=dict(active_parameters=list(full.bounds.active),normalized_parameters=row['normalized_parameters'],
                        residual=r.tolist(),jacobian=j.tolist(),packet_boundaries=edges,times_s=times.tolist(),gps=gps.tolist())
                    e.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
                    row.update(linearization_file=name,linearization_sha256=sha(OUTPUT/name))
                except Exception as error:
                    row.update(status='error',converged=False,reason=repr(error))
                    write(OUTPUT/'last-error.json',dict(identity=identity,error=repr(error),traceback=traceback.format_exc()))
            row.update(native_evaluations=book.count(identity,'fit')+book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-began)
            base.save(target,row,digest);results.append(row)
            print(json.dumps({k:row[k] for k in ('identity','converged','status','native_evaluations')}),flush=True)
        group=[r for r in results if r['kind']=='target'];repeat=dict(agreement_passed=False)
        if len(group)==2 and all(r.get('linearization_file') for r in group):
            local=[]
            for row in group:
                if sha(OUTPUT/row['linearization_file'])!=row['linearization_sha256']:raise ValueError('repeat artifact changed')
                with gzip.open(OUTPUT/row['linearization_file'],'rt') as stream:local.append(json.load(stream))
            gps=np.array(local[0]['gps']);times=np.array(local[0]['times_s'])
            blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
            conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov))
            repeat=repeat_metrics(*local,lambda d:position.physical_residual_step(conversion,d))
        verify(originals=False);calls=book.read('sweeps')
        if len(book.read('starts'))>4 or len(calls)>174:raise ValueError('finite accounting failed')
        write(OUTPUT/'summary.json',dict(version=VERSION,state='complete',results=results,native_evaluations=len(calls),
            repeatability=repeat,qualification_passed=all(r['converged'] for r in results) and repeat['agreement_passed'],
            scientific_decision='abstain',original_labels_changed=False))
        book.export();write(OUTPUT/'charges-index.json',{str(p.relative_to(OUTPUT)):sha(p) for p in (OUTPUT/'charges').glob('*.json')})
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json')))
        write(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(calls),allocated_numerical_threads=0));publish()


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
            if (OUTPUT/'completion.json').exists():raise ValueError('completed free-time trial cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=174,numerical_threads=4)))
    else:
        try:run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc()))
            write(OUTPUT/'status.json',dict(state='stopped',error=repr(error),allocated_numerical_threads=0));raise


if __name__=='__main__':main()
