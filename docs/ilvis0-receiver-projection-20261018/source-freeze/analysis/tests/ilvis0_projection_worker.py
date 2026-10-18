# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded saved-parameter receiver-coordinate audit; no native integration."""
import argparse
import copy
import csv
import fcntl
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_artifact_inventory as inv,ilvis0_projection_audit as audit
from lll.ilvis0_receipt_journal import durable_write,encoded

PARENT=ROOT/'docs/ilvis0-contribution-inventory-20261018'
SELECTION=ROOT/'docs/ilvis0-highspeed-segments-20261008/selection.json.gz'
OUTPUT=ROOT/'data/ilvis0-receiver-projection-20261018'
GUIDE=ROOT/'docs'/OUTPUT.name
QUALIFICATION=OUTPUT/'software-controls'
MAXIMUM_WALL_S=1200
SOFTWARE_TESTS=31
load,sha=inv.load,inv.sha


def write(path,value):durable_write(path,encoded(value),replace=True)


def environment():
    return dict(python=platform.python_version(),numpy=importlib.metadata.version('numpy'),scipy=importlib.metadata.version('scipy'))


def allowance(plan):
    return dict(scope='approved saved-parameter contribution diagnostic',manifest_sha256=sha(OUTPUT/'manifest.json'),
                **{k:v for k,v in plan.items() if k!='tasks'})


def check_hashes(values):
    for name,digest in values.items():
        if sha(ROOT/name)!=digest:raise ValueError('frozen dependency changed: '+name)


def make_plan(rows,source_tasks,*,expected_total=53,expected_complete=18):
    groups=audit.complete_groups(rows)
    if len({r['segment_id'] for r in rows})!=expected_total or len(groups)!=expected_complete:
        raise ValueError('exact frozen total and complete population required')
    fits={(t['segment_id'],t['case_id'],t['model']):t['fit'] for t in source_tasks}
    if len(fits)!=len(source_tasks):raise ValueError('unique authoritative primary metadata required')
    tasks=[]
    for sid,items in groups.items():
        saved=[]
        for item in items:
            key=(sid,item['case_id'],item['model'])
            if key not in fits or fits[key].get('converged') is not True:raise ValueError('all six passing current primary companions required')
            saved.append(dict(copy.deepcopy(item),fit=copy.deepcopy(fits[key])))
        tasks.append(dict(identity=sid,segment_id=sid,primaries=saved))
    count=len(tasks)
    return dict(version=audit.VERSION,tasks=tasks,maximum_groups=count,maximum_primary_reads=6*count,
        maximum_epoch_reads=6*count,maximum_covariance_constructions=count,
        maximum_batched_formal_eigenvalue_checks=count,maximum_dense_factorizations=7*count,
        maximum_projections=18*count,maximum_svd=18*count,maximum_native_evaluations=0,
        maximum_optimizer_starts=0,numerical_threads=4,maximum_wall_s=MAXIMUM_WALL_S,retries=0,
        original_files_read=0,native_predictions=0,not_reoptimized=True)


def sources():
    names=('analysis/tests/ilvis0_projection_worker.py','analysis/tests/test_ilvis0_projection_worker.py',
        'analysis/lll/ilvis0_projection_audit.py','analysis/tests/test_ilvis0_projection_audit.py',
        'analysis/lll/ilvis0_observation_projection.py','analysis/tests/test_ilvis0_observation_projection.py',
        'analysis/lll/ilvis0_artifact_inventory.py','analysis/lll/ilvis0_gps_sensitivity.py',
        'analysis/lll/ilvis0_solver_position.py','analysis/lll/compute_budget.py',
        'analysis/lll/ilvis0_receipt_journal.py')
    return {name:sha(ROOT/name) for name in names}


def qualify():
    QUALIFICATION.mkdir(parents=True,exist_ok=True)
    if (QUALIFICATION/'start.json').exists():raise ValueError('completed or interrupted software batch cannot restart')
    values=sources();write(QUALIFICATION/'manifest.json',dict(sources=values,tests=SOFTWARE_TESTS,
        maximum_batches=1,maximum_wall_s=60,numerical_threads=4,native_predictions=0,original_files_read=0))
    write(QUALIFICATION/'start.json',dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
    command=[sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',sys.executable,'-m','pytest','-q','--tb=short']
    command.extend(str(ROOT/'analysis/tests'/name) for name in ('test_ilvis0_observation_projection.py','test_ilvis0_projection_audit.py','test_ilvis0_projection_worker.py'))
    command.append('--junitxml='+str(QUALIFICATION/'tests.xml'))
    with (QUALIFICATION/'pytest.log').open('w') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
    cases=list(ET.parse(QUALIFICATION/'tests.xml').iter('testcase'))
    passed=result.returncode==0 and len(cases)==SOFTWARE_TESTS and not any(c.find(t) is not None for c in cases for t in ('failure','error','skipped'))
    check_hashes(values);write(QUALIFICATION/'result.json',dict(passed=passed,tests=len(cases),original_files_read=0,native_predictions=0))
    write(QUALIFICATION/'completion.json',dict(state='complete',manifest_sha256=sha(QUALIFICATION/'manifest.json'),result_sha256=sha(QUALIFICATION/'result.json')))
    print(json.dumps(dict(passed=passed,tests=len(cases))))


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    complete=load(PARENT/'completion.json');receipt=load(PARENT/'evidence-receipt.json')
    if complete['manifest_sha256']!=sha(PARENT/'manifest.json') or complete['summary_sha256']!=sha(PARENT/'summary.json'):
        raise ValueError('completed inventory required')
    for name,digest in receipt['artifacts'].items():
        if Path(name).name!=name or sha(PARENT/name)!=digest:raise ValueError('inventory publication changed')
    parent=load(PARENT/'manifest.json');summary=load(PARENT/'summary.json')
    if summary['state']!='complete' or environment()!=parent['environment']:raise ValueError('inventory environment or completion changed')
    q=load(QUALIFICATION/'result.json');qc=load(QUALIFICATION/'completion.json');values=sources()
    if (not q['passed'] or q['tests']!=SOFTWARE_TESTS or qc['manifest_sha256']!=sha(QUALIFICATION/'manifest.json')
            or qc['result_sha256']!=sha(QUALIFICATION/'result.json') or values!=load(QUALIFICATION/'manifest.json')['sources']):
        raise ValueError('exact successful software qualification required')
    plan=make_plan(summary['rows'],parent['tasks']);inputs={}
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json','evidence-receipt.json')),
        (GUIDE,('PLAN.md',)),(QUALIFICATION,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str((directory/name).relative_to(ROOT))]=sha(directory/name)
    selection_receipt=SELECTION.parent/'evidence-receipt.json'
    if sha(SELECTION)!=load(selection_receipt)['artifacts'][SELECTION.name]:raise ValueError('frozen selection changed')
    for path in (SELECTION,selection_receipt):inputs[str(path.relative_to(ROOT))]=sha(path)
    for group in plan['tasks']:
        for row in group['primaries']:
            for stem in ('linearization','epoch'):
                name=row.get(stem+'_file')
                if name:inputs[name]=row[stem+'_sha256']
    check_hashes({**inputs,**values})
    for name in values:
        target=OUTPUT/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    write(OUTPUT/'manifest.json',dict(version=audit.VERSION,plan=plan,inputs=inputs,sources=values,environment=environment(),
        covariance='h1_v3_tau60; formal NEU standard deviations 0.3,0.3,0.7 m',scientific_decision='abstain',labels_changed=False))
    write(OUTPUT/'authorization.json',allowance(plan))
    return verify()


def verify():
    m=load(OUTPUT/'manifest.json')
    if m['version']!=audit.VERSION or m['environment']!=environment():raise ValueError('frozen version/environment changed')
    if load(OUTPUT/'authorization.json')!=allowance(m['plan']):raise ValueError('frozen allowance changed')
    check_hashes({**m['sources'],**m['inputs']})
    for name,digest in m['sources'].items():
        if sha(OUTPUT/'source-freeze'/name)!=digest:raise ValueError('source snapshot changed')
    return m


def read_checked(name,digest):
    data=(ROOT/name).read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('saved array changed')
    return json.loads(gzip.decompress(data))


def run():
    from lll.compute_budget import environment as allocation
    os.environ.update(allocation(workers=1,threads=4,reserved=0))
    import numpy as np
    from lll.ilvis0_observation_projection import ReceiverProjection
    from lll import ilvis0_gps_sensitivity as sensitivity,ilvis0_solver_position as position
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists() or (OUTPUT/'completion.json').exists():raise ValueError('charged audit cannot restart')
        m=verify();plan=m['plan'];digest=sha(OUTPUT/'manifest.json');began=time.monotonic()
        write(OUTPUT/'start.json',dict(manifest_sha256=digest,pid=os.getpid()))
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('frozen wall limit reached')))
        signal.alarm(MAXIMUM_WALL_S)
        fixes={r['segment']['segment_id']:r['segment']['receiver_fixes'] for r in load(SELECTION)['selected']}
        assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
        counts=dict(covariance_constructions=0,dense_factorizations=0,projections=0,svd=0)
        results=[]
        for group in plan['tasks']:
            sid=group['identity'];write(OUTPUT/'status.json',dict(state='projecting_saved_fits',identity=sid,pid=os.getpid(),
                completed=len(results),total=len(plan['tasks']),allocated_numerical_threads=4,native_evaluations=0))
            with (OUTPUT/'starts.jsonl').open('ab') as stream:
                stream.write(encoded(dict(identity=sid,manifest_sha256=digest)));stream.flush();os.fsync(stream.fileno())
            result=dict(identity=sid,status='error',passed=False,projections=[])
            try:
                saved=[];times=None;gps=np.array([[f['latitude_rad'],f['longitude_rad'],f['height_m']] for f in fixes[sid]])
                for row in group['primaries']:
                    arrays=read_checked(row['linearization_file'],row['linearization_sha256'])
                    epochs=read_checked(row['epoch_file'],row['epoch_sha256']) if row.get('epoch_file') else None
                    inv.validate_payload(row['fit'],arrays,epochs,fixes[sid])
                    local_times=arrays.get('times_s',None if epochs is None else epochs['times_s'])
                    if times is None:times=local_times
                    elif times!=local_times:raise ValueError('matched models must share the exact receiver time layout')
                    saved.append((row,arrays))
                counts['covariance_constructions']+=1
                blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                covariance=sensitivity.coordinate_covariance(np.array(times),gps[:,0],gps[:,2],blocks,assumption)
                projections={}
                for view,axes in audit.VIEWS.items():
                    counts['dense_factorizations']+=2;projections[view]=ReceiverProjection(covariance,axes)
                counts['dense_factorizations']+=1;lower=np.linalg.cholesky(covariance)
                for row,arrays in saved:
                    r,j=np.array(arrays['residual']),np.array(arrays['jacobian'])
                    errors=(lower@r).reshape(len(gps),3)*position.physical_metric(gps)
                    for view,projection in projections.items():
                        counts['projections']+=1;counts['svd']+=1;measured=audit.assess(projection,r,j)
                        if measured['cost']>row['primary_cost']+1e-9*max(row['primary_cost'],1.):raise ValueError('marginal objective exceeds full objective')
                        result['projections'].append(dict(measured,case_id=row['case_id'],model=row['model'],view=view,
                            active_parameters=arrays['active_parameters'],full_cost=row['primary_cost'],
                            full_track_rms_neu_m=np.sqrt(np.mean(errors**2,axis=0)).tolist(),
                            full_track_maximum_neu_m=np.max(abs(errors),axis=0).tolist()))
                result.update(status='complete',passed=True,contrasts=audit.contrasts(result['projections']))
            except TimeoutError:raise
            except Exception as error:result.update(reason=repr(error),traceback=traceback.format_exc())
            result.update(elapsed_s=time.monotonic()-began)
            payload=dict(manifest_sha256=digest,result=result,result_sha256=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest())
            write(OUTPUT/(sid+'.json'),payload);results.append(result)
            print(json.dumps(dict(identity=sid,passed=result['passed'],completed=len(results))),flush=True)
            for key in counts:
                if counts[key]>plan['maximum_'+key]:raise ValueError('finite operation allowance exceeded')
        verify();signal.alarm(0)
        write(OUTPUT/'summary.json',dict(state='complete',results=results,operations=counts,native_evaluations=0,
            original_files_read=0,observed_starts=0,elapsed_s=time.monotonic()-began,labels_changed=False,scientific_decision='abstain'))
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json')))
        write(OUTPUT/'status.json',dict(state='complete',allocated_numerical_threads=0,native_evaluations=0));publish()


def publish():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed projection audit changed')
    summary=load(OUTPUT/'summary.json');rows=[dict(segment_id=r['identity'],**p) for r in summary['results'] for p in r['projections']]
    fields=('segment_id','case_id','model','view','cost','full_cost','observations','columns','numerical_rank','minimum_singular_value','normalized_residual_rms','reoptimized','scientific_decision')
    with (GUIDE/'projections.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(rows)
    matched=[dict(segment_id=r['identity'],**v) for r in summary['results'] if r['passed'] for v in r['contrasts']]
    with (GUIDE/'comparisons.csv').open('w',newline='') as stream:
        fields=list(matched[0]) if matched else ['segment_id'];writer=csv.DictWriter(stream,fields,lineterminator='\n');writer.writeheader();writer.writerows(matched)
    text='# Receiver-coordinate sensitivity at the saved fit parameters\n\n'
    text+=f"Completed {len(summary['results'])} groups: {sum(r['passed'] for r in summary['results'])} passed the saved-data checks. "
    text+='This calculation made no native predictions, original-recording reads or model refits.\n\n'
    text+='| Retained receiver objective | Globe / flat / tie at saved parameters |\n|---|---:|\n'
    for view in audit.VIEWS:
        own=[r for r in matched if r['view']==view]
        counts=[sum(r['fixed_parameter_shape_preference']==name for r in own) for name in ('globe','flat','tie')]
        text+=f"| {view} | {' / '.join(map(str,counts))} |\n"
    text+='\nCounts are processing-case comparisons, not independent flights. Parameters were fitted using full 3D receiver positions '
    text+='and remain unchanged here. Horizontal-only or height-only model optima have not been estimated. '
    text+='Both gyroscope and accelerometer increments, initialization and original selection remain in use. '
    text+='Numerical ranks retain every nuisance column and are diagnostic, not a new scientific eligibility gate. '
    text+='Published findings remain **53 globe / 0 flat / 0 unresolved**.\n\n'
    text+='[Projection CSV](projections.csv) · [Comparison CSV](comparisons.csv) · [Finite plan](PLAN.md) · '
    text+='[Measurement-contribution scope](../ilvis0-measurement-contribution/README.md).\n'
    (GUIDE/'README.md').write_text(text)
    names=['manifest.json','authorization.json','summary.json','completion.json','starts.jsonl']
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    for name in ('manifest.json','result.json','completion.json','tests.xml','pytest.log'):
        target=GUIDE/'software-controls'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(QUALIFICATION/name,target)
        names.append('software-controls/'+name)
    names+=['README.md','PLAN.md','projections.csv','comparisons.csv']
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},native_predictions=0,observed_starts=0))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('qualify','prepare-only','detach','package-only'):parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args();OUTPUT.mkdir(exist_ok=True)
    if args.qualify:qualify()
    elif args.package_only:publish()
    elif args.prepare_only:prepare()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with (OUTPUT/'worker.lock').open('a+') as worker:fcntl.flock(worker,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'start.json').exists() or (OUTPUT/'completion.json').exists():raise ValueError('charged audit cannot restart')
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,numerical_threads=4)))
    else:
        try:run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(error=repr(error),traceback=traceback.format_exc()))
            write(OUTPUT/'status.json',dict(state='stopped',allocated_numerical_threads=0,native_evaluations=0));raise


if __name__=='__main__':main()
