# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-boundary diagnostics from preserved endpoints; no optimizer starts."""
import argparse
import copy
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import json
import math
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
import ilvis0_profile_seeded_worker as previous
prior=previous.prior
load,sha,write=prior.load,prior.sha,prior.write
STOPPED=previous.OUTPUT
VERIFIED=previous.ENDPOINTS
AUDIT=ROOT/'data/ilvis0-profile-seeded-audit-20261017'
OUTPUT=ROOT/'data/ilvis0-profile-boundary-20261017'
GUIDE=ROOT/'docs/ilvis0-profile-boundary-20261017'
QUALIFICATION=OUTPUT/'software-controls'
VERSION='ilvis0-profile-exact-boundary-diagnostic-v1'
TESTS=11


class CallScope:
    def __init__(self,book,identity,limit):self.book,self.identity,self.limit=book,identity,limit
    def call(self,identity,phase,kind,function,*args):
        if (identity!=self.identity or phase!='diagnostic' or kind!='tangent'
                or self.book.count(identity,'diagnostic')>=self.limit):
            raise ValueError('finite diagnostic-only scope exceeded')
        return self.book.call(identity,phase,kind,function,*args)


def make_plan(manifest,saved,vm,vs,audit):
    original={t['identity']:t for t in manifest['plan']['tasks']}
    controls=[r for r in saved if r['kind']=='control']
    primary=[r for r in saved if r['identity']==audit['target']['identity']]
    geometry=audit['clock_geometry']
    if (len(controls)!=2 or not all(r['status']=='complete' and r['converged'] for r in controls)
            or len(primary)!=1 or primary[0]['status']!='complete' or primary[0]['converged']
            or not geometry['side_geometry_supported'] or not math.isfinite(geometry['point'])
            or abs(geometry['point'])>1 or abs(geometry['center_relocation_s'])>1e-8):
        raise ValueError('both passing controls, failed primary and supported local knot required')
    choices=[t for t in vm['plan']['tasks'] if t['anchor_role']=='primary' and t['start_role']=='repeat']
    if len(choices)!=1:raise ValueError('exact verified profile companion required')
    companion=choices[0];rows=[r for r in vs['results'] if r['identity']==companion['identity']]
    if len(rows)!=1 or rows[0]['status']!='complete' or not rows[0]['conditional_verified']:
        raise ValueError('profile companion must be verified')
    tasks=[]
    def reference(item,row,directory,role,kind,limit):
        item=copy.deepcopy(item);names=list(item['fit']['active_parameters'])
        point=list(row.get('normalized_parameters',item.get('saved_result',{}).get('normalized_parameters',[])))
        if len(point)!=len(names) or names.count('time_offset')!=1:raise ValueError('full source layout required')
        item.update(kind=kind,source_role=role,source_identity=row['identity'],
            identity=row['identity']+'::exact_boundary_diagnostic',maximum_diagnostic_calls=limit,
            source_artifact=str(directory/row['linearization_file']),source_artifact_sha256=row['linearization_sha256'],
            fit=dict(active_parameters=names,normalized_parameters=point,residual_sum_squares=row['residual_sum_squares']))
        if kind=='target':
            task=item['task'];index=names.index('time_offset')
            if (task['segment_id']!='50f24131843071ae9312c082' or task['case_id']!='bias1_unsubtracted'
                    or task['model']!='sphere_still' or point[index]!=geometry['original_point']):
                raise ValueError('unchanged target and original timing anchor required')
            item['exact_point']=point.copy();item['exact_point'][index]=geometry['point']
        return item
    for row in controls:tasks.append(reference(original[row['identity']],row,STOPPED,'control','control',3))
    row=primary[0]
    tasks.append(reference(original[row['identity']],row,STOPPED,'completed_primary','target',30))
    tasks.append(reference(companion,rows[0],VERIFIED,'verified_profile_companion','target',30))
    return dict(version=VERSION,tasks=tasks,maximum_starts=4,maximum_optimizer_starts=0,
        maximum_native_evaluations=66,maximum_geometry_queries=6144,maximum_affine_solves=14,
        numerical_threads=4,retries=0)


def stopped_results():
    m=load(STOPPED/'manifest.json');digest=sha(STOPPED/'manifest.json');rows=[];paths=[]
    for task in m['plan']['tasks']:
        path=STOPPED/(task['identity'].replace('::','-')+'.json')
        if not path.exists():continue
        value=load(path);row=value['result']
        h=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if value['manifest_sha256']!=digest or value['result_sha256']!=h:raise ValueError('stopped result changed')
        rows.append(row);paths.append(path)
    if len(rows)!=3:raise ValueError('preserve exactly three stopped-trial results')
    return m,rows,paths


def source_plan():
    m,rows,_=stopped_results()
    return make_plan(m,rows,load(VERIFIED/'manifest.json'),load(VERIFIED/'summary.json'),load(AUDIT/'summary.json'))


def sources():
    values=dict(load(STOPPED/'manifest.json')['sources'])
    for name in ('analysis/lll/ilvis0_exact_boundary.py','analysis/tests/ilvis0_profile_boundary_worker.py',
                 'analysis/tests/test_ilvis0_exact_boundary.py','analysis/tests/test_ilvis0_profile_boundary_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    prior.check_hashes(values);return values


def qualify():
    QUALIFICATION.mkdir(parents=True,exist_ok=True)
    with (QUALIFICATION/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (QUALIFICATION/'start.json').exists():raise ValueError('charged software batch cannot restart')
        values=sources();prior.snapshot(QUALIFICATION,values)
        write(QUALIFICATION/'manifest.json',dict(sources=values,tests=TESTS,maximum_batches=1,timeout_s=120,
            maximum_software_callbacks=512,numerical_threads=4,original_reads=0,observed_calls=0))
        write(QUALIFICATION/'start.json',dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
        command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',sys.executable,'-m','pytest','-q','--tb=short',
            str(ROOT/'analysis/tests/test_ilvis0_exact_boundary.py'),str(ROOT/'analysis/tests/test_ilvis0_profile_boundary_worker.py'),
            '--junitxml='+str(QUALIFICATION/'tests.xml')]
        with (QUALIFICATION/'pytest.log').open('w') as log:
            from ilvis0_receipt_qualification_worker import run_batch
            code=run_batch(command,log,120)
        cases=list(ET.parse(QUALIFICATION/'tests.xml').iter('testcase'))
        result=dict(passed=code==0 and len(cases)==TESTS and not any(c.find(tag) is not None
            for c in cases for tag in ('failure','error','skipped')),tests=len(cases),returncode=code,original_reads=0,observed_calls=0)
        prior.check_hashes(values);write(QUALIFICATION/'result.json',result)
        write(QUALIFICATION/'completion.json',dict(state='complete',manifest_sha256=sha(QUALIFICATION/'manifest.json'),result_sha256=sha(QUALIFICATION/'result.json')))
        print(json.dumps(result))


def allowance():
    return dict(scope='approved exact-boundary diagnostic roadmap',manifest_sha256=sha(OUTPUT/'manifest.json'),
        maximum_starts=4,maximum_optimizer_starts=0,maximum_native_evaluations=66,numerical_threads=4,retries=0)


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    prior.sealed(AUDIT,published=ROOT/'docs'/AUDIT.name)
    prior.sealed(VERIFIED,published=previous.grid.previous.GUIDE)
    q=load(QUALIFICATION/'result.json');c=load(QUALIFICATION/'completion.json')
    if (not q['passed'] or q['tests']!=TESTS or c['manifest_sha256']!=sha(QUALIFICATION/'manifest.json')
            or c['result_sha256']!=sha(QUALIFICATION/'result.json')):raise ValueError('software gate failed')
    parent,_,paths=stopped_results();plan=source_plan();values=sources()
    if values!=load(QUALIFICATION/'manifest.json')['sources']:raise ValueError('qualified source changed')
    inputs=prior.scientific_inputs(parent['inputs'])
    for directory,names in ((STOPPED,('manifest.json','authorization.json')),
        (AUDIT,('manifest.json','summary.json','completion.json')),
        (ROOT/'docs'/AUDIT.name,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
        (QUALIFICATION,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    for path in paths:inputs[str(path)]=sha(path)
    for task in plan['tasks']:inputs[task['source_artifact']]=task['source_artifact_sha256']
    originals={t['task']['selected']['source_path']:parent['originals'][t['task']['selected']['source_path']] for t in plan['tasks']}
    prior.check_hashes(inputs);prior.check_hashes(originals)
    if shutil.disk_usage(OUTPUT).free<1024**3:raise ValueError('one GiB free storage required before launch')
    e=prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=parent['extended_kernel']:raise ValueError('native integration changed')
    prior.snapshot(OUTPUT,values);shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),extended_kernel=extended,ordinary_value_kernel=parent['ordinary_value_kernel'],
        scientific_decision='abstain',original_labels_changed=False))
    write(OUTPUT/'authorization.json',allowance());return verify()


def verify(*,originals=True):
    m=load(OUTPUT/'manifest.json')
    if m['version']!=VERSION or m['plan']!=source_plan():raise ValueError('finite diagnostic plan changed')
    for key in ('sources','inputs',*(['originals'] if originals else [])):prior.check_hashes(m[key])
    for path,h in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(path).relative_to(ROOT))!=h:raise ValueError('source snapshot changed')
    if sha(OUTPUT/'source-freeze'/m['extended_kernel']['source_file'])!=m['extended_kernel']['source_sha256']:raise ValueError('kernel snapshot changed')
    prior.engine().base.runtime.check_environment(m['environment'])
    if load(OUTPUT/'authorization.json')!=allowance():raise ValueError('allowance changed')
    return m


def publish():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('completion changed')
    summary=load(OUTPUT/'summary.json');names=['manifest.json','authorization.json','completion.json','summary.json','starts.jsonl','sweeps.jsonl','charges-index.json']
    for row in summary['results']:
        if row.get('linearization_file'):
            name=row['linearization_file']
            if Path(name).name!=name or sha(OUTPUT/name)!=row['linearization_sha256']:raise ValueError('native artifact changed')
            names.append(name)
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    for name,h in load(OUTPUT/'charges-index.json').items():
        if '..' in Path(name).parts or Path(name).parts[0]!='charges' or sha(OUTPUT/name)!=h:raise ValueError('receipt changed')
    shutil.copytree(OUTPUT/'charges',GUIDE/'charges',dirs_exist_ok=True);shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    for name in ('manifest.json','result.json','completion.json','tests.xml','pytest.log'):
        target=GUIDE/'software-controls'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(QUALIFICATION/name,target);names.append('software-controls/'+name)
    text='# Exact-boundary diagnostic results\n\n'
    text+=f"{len(summary['results'])} diagnostic identities / {summary['native_evaluations']} native calls / zero optimizer starts. Full qualification passed: {summary['qualification_passed']}.\n\n"
    text+='| Source | Passed | Calls | Outcome |\n|---|---|---:|---|\n'
    for row in summary['results']:text+=f"| {row['source_role']} | {row['passed']} | {row['native_evaluations']} | {row.get('reason',row['status'])} |\n"
    text+='\nThe interrupted trial and original fit labels remain unchanged. Passing boundaries still require companion/model review before changing a stretch disposition.\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (OUTPUT,STOPPED,VERIFIED,AUDIT):
            lock=stack.enter_context((directory/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():raise ValueError('completed diagnostics cannot restart')
        m=prepare();e=prior.engine();base=e.base
        import numpy as np
        from types import SimpleNamespace
        from lll.ilvis0_receipt_journal import Ledger
        from lll import ilvis0_clock_brackets as clock,ilvis0_solver_position as position
        from lll.ilvis0_boundary_adapter import displacement_metrics
        from lll.ilvis0_exact_boundary import check_endpoint
        tasks=m['plan']['tasks'];digest=sha(OUTPUT/'manifest.json');results=[]
        book=Ledger(OUTPUT,digest,[t['identity'] for t in tasks],fit_limit=1,diagnostic_limit=30)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tmeta=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=m['ordinary_value_kernel'] or tmeta!=m['extended_kernel']:raise ValueError('kernel changed')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={r['case_id']:r for r in base.primary_cases()};assumption={a.name:a for a in base.sensitivity.assumptions()}['h1_v3_tau60']
        for item in tasks:
            verify(originals=False);identity=item['identity'];target=OUTPUT/(identity.replace('::','-')+'.json');cached=base.cached(target,digest)
            if cached is not None:results.append(cached);continue
            began=time.monotonic();row=dict(identity=identity,kind=item['kind'],source_role=item['source_role'],passed=False,scientific_decision='abstain',optimizer_starts=0,original_labels_changed=False)
            if item['kind']=='target' and not all(r['passed'] for r in results if r['kind']=='control'):row.update(status='not_started',reason='fresh_control_failed')
            elif identity in {s['identity'] for s in book.read('starts')}:row.update(status='interrupted',reason='charged_identity_no_retry')
            else:
                if shutil.disk_usage(OUTPUT).free<1024**3:raise ValueError('one GiB free storage required before each identity')
                book.start(identity);scope=CallScope(book,identity,item['maximum_diagnostic_calls'])
                write(OUTPUT/'status.json',dict(state='checking_exact_boundary',pid=os.getpid(),identity=identity,completed=len(results),total=4,allocated_numerical_threads=4))
                try:
                    task=item['task'];chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:raise ValueError('extraction changed')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1));cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
                    initial,_=base.corpus.initialize(times,gps,values,task['model'])
                    full=base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,cov,initial,
                        base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    if list(full.bounds.active)!=item['fit']['active_parameters']:raise ValueError('full parameter layout changed')
                    with gzip.open(item['source_artifact'],'rt') as stream:source= json.load(stream)
                    if source['times_s']!=times.tolist() or source['gps']!=gps.tolist():raise ValueError('saved source observation layout changed')
                    saved_residual=np.array(source['residual']);physical=lambda d:position.physical_residual_step(full,d)
                    if item['kind']=='control':
                        checked=previous.check_full(scope,identity,full,task['model'],item['fit']['normalized_parameters'],physical)
                        native=checked.pop('center_native');movement=displacement_metrics(saved_residual,native[0],physical)
                        checked.update(passed=bool(checked['full_gate_verified'] and movement['passed']),source_relocation=movement,normalized_parameters=item['fit']['normalized_parameters'])
                    else:
                        geometry_queries=0;geometry_calls=0
                        def geometry_at(t):
                            nonlocal geometry_queries,geometry_calls
                            if geometry_calls>=3:raise ValueError('finite geometry allowance exceeded')
                            geometry_calls+=1;g=clock.bracket(times,len(values),full.bounds.limits['time_offset'],t,maximum_queries=1024);geometry_queries+=g['queries'];return g
                        checked=check_endpoint(scope,identity,full.residual_tangent,task['model'],item['exact_point'],saved_residual,physical,
                            time_index=list(full.bounds.active).index('time_offset'),geometry_at=geometry_at)
                        native=checked.pop('center_native');checked.update(geometry_queries=geometry_queries,geometry_checks=geometry_calls)
                    row.update(checked,status='complete')
                    if native is not None:
                        r,j,edges=native;name=identity.replace('::','-')+'-linearization.json.gz'
                        payload=dict(active_parameters=list(full.bounds.active),normalized_parameters=row['normalized_parameters'],residual=r.tolist(),jacobian=j.tolist(),packet_boundaries=edges,times_s=times.tolist(),gps=gps.tolist())
                        e.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
                        row.update(linearization_file=name,linearization_sha256=sha(OUTPUT/name),residual_sum_squares=float(r@r))
                except Exception as error:
                    row.update(status='error',passed=False,reason=repr(error));write(OUTPUT/'last-error.json',dict(identity=identity,error=repr(error),traceback=traceback.format_exc()))
            row.update(native_evaluations=book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-began);base.save(target,row,digest);results.append(row)
            print(json.dumps({k:row[k] for k in ('identity','passed','status','native_evaluations')}),flush=True)
        targets=[r for r in results if r['kind']=='target'];repeat=dict(agreement_passed=False)
        if len(targets)==2 and all(r.get('linearization_file') for r in targets):
            local=[]
            for row in targets:
                if sha(OUTPUT/row['linearization_file'])!=row['linearization_sha256']:raise ValueError('repeat artifact changed')
                with gzip.open(OUTPUT/row['linearization_file'],'rt') as stream:local.append(json.load(stream))
            gps=np.array(local[0]['gps']);times=np.array(local[0]['times_s']);blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption);conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov))
            repeat=previous.repeat_metrics(*local,lambda d:position.physical_residual_step(conversion,d))
        verify(originals=False);calls=book.read('sweeps')
        if len(book.read('starts'))>4 or len(calls)>66 or any(c['phase']!='diagnostic' for c in calls):raise ValueError('finite diagnostic accounting failed')
        write(OUTPUT/'summary.json',dict(version=VERSION,state='complete',results=results,native_evaluations=len(calls),optimizer_starts=0,
            repeatability=repeat,qualification_passed=all(r['passed'] for r in results) and repeat['agreement_passed'],scientific_decision='abstain',original_labels_changed=False))
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
            if (OUTPUT/'completion.json').exists():raise ValueError('completed boundary diagnostics cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=66,numerical_threads=4)))
    else:
        try:run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc()));write(OUTPUT/'status.json',dict(state='stopped',error=repr(error),allocated_numerical_threads=0));raise


if __name__=='__main__':main()
