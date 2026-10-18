# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched fixed-time profiles; conditional results never relabel free-time fits."""
import argparse
import copy
from contextlib import ExitStack
import fcntl
import gzip
import importlib.metadata
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
import ilvis0_boundary_followup_worker as prior

OUTPUT=ROOT/'data/ilvis0-fixed-time-profile-20261017'
GUIDE=ROOT/'docs/ilvis0-fixed-time-profile-20261017'
PARENT=prior.OUTPUT
OLD=prior.PARENT
QUALIFICATION=ROOT/'data/ilvis0-fixed-time-controls-20261017'
QUALIFICATION_GUIDE=ROOT/'docs/ilvis0-fixed-time-controls-20261017'
VERSION='ilvis0-matched-fixed-time-profile-v1'
TESTS=21
load,sha,write=prior.load,prior.sha,prior.write


def make_plan(parent,old):
    controls=[copy.deepcopy(t) for t in parent['plan']['tasks'] if t['kind']=='control']
    target_id='50f24131843071ae9312c082::bias1_unsubtracted::sphere_still'
    selected=[t for t in old['plan']['tasks'] if t['source_identity'].rsplit('::',1)[0]==target_id]
    roles={t['source_identity'].split('::')[-1]:t for t in selected}
    if len(controls)!=2 or len(selected)!=2 or set(roles)!={'primary','repeat'}:
        raise ValueError('exact controls and predeclared target endpoints required')
    names=roles['primary']['fit']['active_parameters']
    if names!=roles['repeat']['fit']['active_parameters'] or names.count('time_offset')!=1:
        raise ValueError('common full parameter order required')
    index=names.index('time_offset')
    anchors={role:t['fit']['normalized_parameters'][index] for role,t in roles.items()}
    if anchors['primary']==anchors['repeat'] or any(not -1<=t<=1 for t in anchors.values()):
        raise ValueError('two distinct feasible timing anchors required')
    for item in controls:
        item.update(identity=item['source_identity']+'::fixed_time_control',maximum_fit_calls=3,maximum_diagnostic_calls=0)
        i=item['fit']['active_parameters'].index('time_offset')
        item['anchor_normalized']=item['fit']['normalized_parameters'][i]
    tasks=controls
    for anchor_role in ('primary','repeat'):
        for start_role in ('primary','repeat'):
            item=copy.deepcopy(roles[start_role]);item['kind']='profile'
            point=list(item['fit']['normalized_parameters']);point[index]=anchors[anchor_role]
            item.update(identity=target_id+'::anchor_'+anchor_role+'::from_'+start_role,
                anchor_role=anchor_role,start_role=start_role,anchor_normalized=anchors[anchor_role],
                start_full=point,maximum_fit_calls=80,maximum_diagnostic_calls=1)
            tasks.append(item)
    return dict(version=VERSION,tasks=tasks,maximum_starts=6,maximum_profile_starts=4,
        maximum_native_evaluations=330,maximum_saved_pair_comparisons=2,numerical_threads=4,retries=0)


def controls_passed(results):
    rows=[r for r in results if r['kind']=='control']
    return len(rows)==2 and all(r['status']=='complete' and r['conditional_converged'] for r in rows)


def pair_metrics(a,b,physical_step):
    import numpy as np
    if any(a[k]!=b[k] for k in ('fixed_time_normalized','times_s','gps')):
        raise ValueError('same fixed time and observation geometry required')
    x,y=np.asarray(a['residual']),np.asarray(b['residual'])
    change=np.asarray(physical_step(y-x),float)
    if x.shape!=y.shape or change.shape!=(len(a['gps']),3) or not np.all(np.isfinite(change)):
        raise ValueError('finite compatible saved profile residuals required')
    ca,cb=float(x@x),float(y@y);relative=abs(ca-cb)/max(ca,cb,1.)
    rms=np.sqrt(np.mean(change**2,axis=0))
    return dict(relative_cost_difference=relative,track_rms_neu_m=rms.tolist(),
        agreement_passed=bool(relative<=1e-6 and np.max(rms)<=.01),conditional_only=True)


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name in ('analysis/lll/ilvis0_fixed_time_profile.py','analysis/tests/ilvis0_fixed_time_worker.py',
                 'analysis/tests/test_ilvis0_fixed_time_profile.py','analysis/tests/test_ilvis0_fixed_time_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    prior.check_hashes(values)
    return values


def qualify():
    QUALIFICATION.mkdir(exist_ok=True);QUALIFICATION_GUIDE.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (QUALIFICATION,PARENT):
            f=stack.enter_context((directory/'worker.lock').open('a+'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((QUALIFICATION/n).exists() for n in ('start.json','completion.json')):
            raise ValueError('charged controls cannot restart')
        values=sources();prior.snapshot(QUALIFICATION,values)
        manifest=dict(sources=values,inputs={str(GUIDE/'PLAN.md'):sha(GUIDE/'PLAN.md')},tests=TESTS,
            maximum_batches=1,retries=0,numerical_threads=4,maximum_software_callbacks=1024,
            observed_starts=0,original_files_read=0,timeout_s=120,python=sys.version,
            environment={k:importlib.metadata.version(k) for k in ('numpy','scipy','pytest')})
        write(QUALIFICATION/'manifest.json',manifest)
        write(QUALIFICATION/'start.json',dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
        command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',sys.executable,
            '-m','pytest','-q','--tb=short',str(ROOT/'analysis/tests/test_ilvis0_fixed_time_profile.py'),
            str(ROOT/'analysis/tests/test_ilvis0_fixed_time_worker.py'),'--junitxml='+str(QUALIFICATION/'tests.xml')]
        with (QUALIFICATION/'pytest.log').open('w') as log:
            from ilvis0_receipt_qualification_worker import run_batch
            rc=run_batch(command,log,120)
        cases=list(ET.parse(QUALIFICATION/'tests.xml').iter('testcase'))
        result=dict(passed=rc==0 and len(cases)==TESTS and not any(c.find(tag) is not None
            for c in cases for tag in ('failure','error','skipped')),tests=len(cases),returncode=rc,
            observed_starts=0,original_files_read=0,compiled_motion_cases=3)
        prior.check_hashes(values);write(QUALIFICATION/'result.json',result)
        write(QUALIFICATION/'completion.json',dict(state='complete',manifest_sha256=sha(QUALIFICATION/'manifest.json'),
                                                  result_sha256=sha(QUALIFICATION/'result.json')))
        names=['manifest.json','start.json','result.json','completion.json','tests.xml','pytest.log']
        for name in names:shutil.copyfile(QUALIFICATION/name,QUALIFICATION_GUIDE/name)
        shutil.copytree(QUALIFICATION/'source-freeze',QUALIFICATION_GUIDE/'source-freeze',dirs_exist_ok=True)
        (QUALIFICATION_GUIDE/'README.md').write_text('# Fixed-time adapter controls\n\n'
            +f"Passed: {result['passed']}; {result['tests']} checks, including three compiled-motion cases with known answers. "
            +'No archival originals were read or fitted. Conditional completion does not qualify the full free-time fit.\n')
        write(QUALIFICATION_GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(QUALIFICATION_GUIDE/n) for n in (*names,'README.md')}))
        print(json.dumps(result))


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    prior.sealed(PARENT,published=prior.GUIDE)
    prior.sealed(QUALIFICATION_GUIDE,'result.json','result_sha256')
    q=load(QUALIFICATION_GUIDE/'result.json')
    if not q['passed'] or q['tests']!=TESTS:raise ValueError('adapter controls did not qualify')
    parent=load(PARENT/'manifest.json');old=load(OLD/'manifest.json');plan=make_plan(parent,old)
    values=sources();inputs=prior.scientific_inputs(parent['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
        (prior.GUIDE,('evidence-receipt.json',)),(OLD,('manifest.json',)),
        (QUALIFICATION_GUIDE,('manifest.json','result.json','completion.json','evidence-receipt.json')),
        (GUIDE,('PLAN.md',))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={t['task']['selected']['source_path']:old['originals'][t['task']['selected']['source_path']]
        if t['kind']=='profile' else parent['originals'][t['task']['selected']['source_path']] for t in plan['tasks']}
    prior.check_hashes(inputs);prior.check_hashes(originals)
    e=prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=parent['extended_kernel']:raise ValueError('native integration changed')
    prior.snapshot(OUTPUT,values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    manifest=dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),extended_kernel=extended,
        ordinary_value_kernel=parent['ordinary_value_kernel'],conditional_profile_only=True,
        scientific_decision='abstain',original_labels_changed=False)
    write(OUTPUT/'manifest.json',manifest)
    write(OUTPUT/'authorization.json',dict(scope='approved finite timing-profile roadmap',maximum_starts=6,
        maximum_native_evaluations=330,numerical_threads=4,retries=0,manifest_sha256=sha(OUTPUT/'manifest.json')))
    return verify()


def verify(*,originals=True):
    m=load(OUTPUT/'manifest.json')
    if m['version']!=VERSION or m['plan']!=make_plan(load(PARENT/'manifest.json'),load(OLD/'manifest.json')):
        raise ValueError('fixed finite plan changed')
    for section in ('sources','inputs',*(['originals'] if originals else [])):prior.check_hashes(m[section])
    for name,h in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(name).relative_to(ROOT))!=h:raise ValueError('frozen source copy changed')
    if sha(OUTPUT/'source-freeze'/m['extended_kernel']['source_file'])!=m['extended_kernel']['source_sha256']:
        raise ValueError('generated source copy changed')
    prior.engine().base.runtime.check_environment(m['environment'])
    expected=dict(scope='approved finite timing-profile roadmap',maximum_starts=6,maximum_native_evaluations=330,
                  numerical_threads=4,retries=0,manifest_sha256=sha(OUTPUT/'manifest.json'))
    if load(OUTPUT/'authorization.json')!=expected:raise ValueError('profile allowance changed')
    return m


def publish():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed profile changed')
    summary=load(OUTPUT/'summary.json')
    names=['manifest.json','authorization.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl','charges-index.json']
    for r in summary['results']:
        if r.get('linearization_file'):
            n=r['linearization_file']
            if Path(n).name!=n or sha(OUTPUT/n)!=r['linearization_sha256']:raise ValueError('native artifact mismatch')
            names.append(n)
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    for name,h in load(OUTPUT/'charges-index.json').items():
        if '..' in Path(name).parts or Path(name).parts[0]!='charges' or sha(OUTPUT/name)!=h:raise ValueError('charge receipt mismatch')
    shutil.copytree(OUTPUT/'charges',GUIDE/'charges',dirs_exist_ok=True)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    text='# Matched fixed-time profile results\n\n'
    text+=f"Completed {len(summary['results'])} identities / {summary['native_evaluations']} native calls. "
    text+='These restricted fits do not establish free-time convergence or change the shape tally.\n\n'
    text+='| Kind / anchor / starting solution | Conditional completion | Cost | Native calls |\n|---|---|---:|---:|\n'
    for r in summary['results']:
        text+=f"| {r['kind']} / {r.get('anchor_role','control')} / {r.get('start_role','control')} | {r['conditional_converged']} | {r.get('residual_sum_squares','')} | {r['native_evaluations']} |\n"
    text+='\n| Fixed anchor | Both conditional fits passed | Within-anchor repeat agreement |\n|---|---|---|\n'
    for pair in summary['pair_repeatability']:
        text+=f"| {pair['anchor_role']} | {pair['both_conditional_fits_passed']} | {pair.get('agreement_passed',False)} |\n"
    text+='\nBoth profile anchors and every failure are retained. The full timing derivative remains in each final artifact.\n'
    text+='[Current status](../CURRENT_STATUS.md) · [Finite plan](PLAN.md).\n'
    (GUIDE/'RESULTS.md').write_text(text)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in (*names,'RESULTS.md')},scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (OUTPUT,PARENT,OLD,QUALIFICATION):
            f=stack.enter_context((directory/'worker.lock').open('a+'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed profiles cannot restart')
        manifest=prepare();verify();e=prior.engine();base=e.base
        import numpy as np
        from lll import ilvis0_solver_trust_v2 as solver,ilvis0_solver_position as position
        from lll.ilvis0_fixed_time_profile import FixedTimeProblem
        from lll.ilvis0_receipt_journal import Ledger
        from lll.ilvis0_solver_refinement import projected_stationarity
        tasks=manifest['plan']['tasks'];digest=sha(OUTPUT/'manifest.json')
        ledger=Ledger(OUTPUT,digest,[t['identity'] for t in tasks],fit_limit=80,diagnostic_limit=1)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tmeta=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=manifest['ordinary_value_kernel'] or tmeta!=manifest['extended_kernel']:raise ValueError('native kernel changed')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={r['case_id']:r for r in base.primary_cases()}
        assumption={a.name:a for a in base.sensitivity.assumptions()}['h1_v3_tau60']
        results=[]
        for item in tasks:
            verify(originals=False);identity=item['identity'];target=OUTPUT/(identity.replace('::','-')+'.json');began=time.monotonic()
            cached=base.cached(target,digest)
            if cached is not None:results.append(cached);continue
            result=dict(identity=identity,kind=item['kind'],source_identity=item['source_identity'],
                conditional_converged=False,free_time_converged=False,anchor_normalized=item['anchor_normalized'],
                anchor_role=item.get('anchor_role','control'),start_role=item.get('start_role','control'))
            if item['kind']=='profile' and not controls_passed(results):result.update(status='not_started',reason='control_failed_no_start')
            elif identity in {r['identity'] for r in ledger.read('starts')}:result.update(status='interrupted',reason='charged_start_no_retry')
            else:
                ledger.start(identity)
                write(OUTPUT/'status.json',dict(state='profiling',pid=os.getpid(),identity=identity,completed=len(results),total=6,
                    allocated_numerical_threads=4,native_evaluations=len(ledger.read('sweeps'))))
                try:
                    task=item['task'];chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:raise ValueError('frozen original extraction changed')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                    covariance=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
                    initial,_=base.corpus.initialize(times,gps,values,task['model'])
                    full=base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,
                        initial,base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
                        gravity_mps2=9.81,disc_radius_m=6371000.)
                    if list(full.bounds.active)!=item['fit']['active_parameters']:raise ValueError('full parameter order changed')
                    native=full.residual_tangent;cache={}
                    def charged(u,model):
                        if ledger.count(identity,'fit')>=item['maximum_fit_calls']:raise ValueError('identity fitting allowance exceeded')
                        value=ledger.call(identity,'fit','tangent',native,u,model)
                        if not cache and (item['kind']=='control' or item['anchor_role']==item['start_role']):
                            cost=float(value[0]@value[0]);old=item['fit']['residual_sum_squares']
                            if abs(cost-old)/max(cost,old,1.)>1e-8:raise ValueError('saved same-anchor endpoint cost changed')
                        cache[tuple(u)]=value;return value
                    full.residual_tangent=charged
                    profile=FixedTimeProblem(full,item['anchor_normalized'])
                    start_full=np.array(item.get('start_full',item['fit']['normalized_parameters']))
                    start=profile.reduce(start_full)
                    physical=lambda d:position.physical_residual_step(full,d)
                    if item['kind']=='control':
                        r,j,_=profile.residual_tangent(start,task['model']);repeated,_,_=profile.residual_tangent(start,task['model'])
                        from lll.ilvis0_boundary_adapter import displacement_metrics
                        repeat=displacement_metrics(r,repeated,physical)
                        gate=position.verify_stability(start,r,j,lambda u,**kwargs:profile.residual_tangent(u,task['model']),physical)
                        result.update(conditional_converged=bool(repeat['passed'] and gate['passed']),reason=gate['reason'],
                            residual_sum_squares=float(r@r),conditional_stability=gate,normalized_parameters=start_full.tolist())
                    else:
                        fit=solver.fit_candidate(profile,task['model'],start=start,maximum_evaluations=80,physical_step=physical)
                        reduced=fit['normalized_parameters'];final=profile.lift(reduced)
                        result.update(conditional_converged=bool(fit['converged']),reason=fit['message'],
                            residual_sum_squares=fit['residual_sum_squares'],parameters=fit['parameters'],
                            conditional_stationarity=fit['exact_projected_gradient_relative'],conditional_stability=fit['stability_probe'],
                            free_active_parameters=list(profile.bounds.active),normalized_parameters=final.tolist(),
                            evaluation_trace=fit['evaluation_trace'],step_history=fit['step_history'])
                        r,j,edges=ledger.call(identity,'diagnostic','full_tangent',native,final,task['model'])
                        if abs(float(r@r)-fit['residual_sum_squares'])/max(float(r@r),1.)>1e-8:raise ValueError('final fresh objective changed')
                        result.update(full_projected_stationarity_diagnostic=projected_stationarity(final,r,j)[0],
                            full_timing_gradient=float(j[:,profile.index]@r))
                        name=identity.replace('::','-')+'-linearization.json.gz'
                        payload=dict(active_parameters=list(full.bounds.active),normalized_parameters=final.tolist(),
                            fixed_time_normalized=profile.anchor,free_active_parameters=list(profile.bounds.active),
                            residual=r.tolist(),jacobian=j.tolist(),times_s=times.tolist(),gps=gps.tolist(),packet_boundaries=edges)
                        e.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
                        result.update(linearization_file=name,linearization_sha256=sha(OUTPUT/name))
                    result['status']='complete'
                except Exception as error:
                    result.update(status='error',conditional_converged=False,reason=type(error).__name__+': '+str(error))
                    write(OUTPUT/'last-error.json',dict(identity=identity,reason=result['reason'],traceback=traceback.format_exc()))
            result.update(native_evaluations=ledger.count(identity,'fit')+ledger.count(identity,'diagnostic'),
                elapsed_s=time.monotonic()-began,scientific_decision='abstain',original_labels_changed=False)
            base.save(target,result,digest);results.append(result)
            print(json.dumps({k:result[k] for k in ('identity','conditional_converged','status','native_evaluations','elapsed_s')}),flush=True)
        verify(originals=False);starts=ledger.read('starts');calls=ledger.read('sweeps')
        if len(starts)>6 or len(calls)>330:raise ValueError('finite profile accounting mismatch')
        from types import SimpleNamespace
        pairs=[]
        for anchor in ('primary','repeat'):
            group=[r for r in results if r['kind']=='profile' and r['anchor_role']==anchor]
            pair=dict(anchor_role=anchor,both_conditional_fits_passed=all(r['conditional_converged'] for r in group),agreement_passed=False)
            if len(group)!=2:raise ValueError('both profile starting solutions required')
            if all(r.get('linearization_file') for r in group):
                local=[]
                for r in group:
                    if sha(OUTPUT/r['linearization_file'])!=r['linearization_sha256']:raise ValueError('profile comparison artifact changed')
                    with gzip.open(OUTPUT/r['linearization_file'],'rt') as stream:local.append(json.load(stream))
                x=local[0];saved_gps=np.array(x['gps']);saved_times=np.array(x['times_s'])
                blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(saved_gps),1,1))
                cov=base.sensitivity.coordinate_covariance(saved_times,saved_gps[:,0],saved_gps[:,2],blocks,assumption)
                conversion=SimpleNamespace(gps=saved_gps,cholesky=np.linalg.cholesky(cov))
                pair.update(pair_metrics(*local,lambda d:position.physical_residual_step(conversion,d)))
            pairs.append(pair)
        write(OUTPUT/'summary.json',dict(state='complete',version=VERSION,results=results,native_evaluations=len(calls),
            charged_profile_starts=sum(r['identity'] in {t['identity'] for t in tasks if t['kind']=='profile'} for r in starts),
            controls_passed=controls_passed(results),pair_repeatability=pairs,scientific_decision='abstain',full_free_time_qualification=False,original_labels_changed=False))
        ledger.export()
        write(OUTPUT/'charges-index.json',{str(p.relative_to(OUTPUT)):sha(p) for p in (OUTPUT/'charges').glob('*.json')})
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json')))
        write(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(calls),allocated_numerical_threads=0))
        publish()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('qualify','prepare-only','detach','package-only'):parser.add_argument('--'+name,action='store_true')
    args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    if args.qualify:qualify()
    elif args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.package_only:publish()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'completion.json').exists():raise ValueError('completed profile cannot restart')
            with (OUTPUT/'worker.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=330,numerical_threads=4)))
    else:
        try:run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc()))
            write(OUTPUT/'status.json',dict(state='stopped',allocated_numerical_threads=0,error=repr(error)))
            raise


if __name__=='__main__':main()
