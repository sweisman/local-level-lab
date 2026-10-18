# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate finite application of the qualified clock guard to one final pair."""
import copy
from functools import partial
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_representable_worker as parent

PARENT=parent.OUTPUT
PARENT_GUIDE=parent.GUIDE
ORIGINAL=ROOT/'data/ilvis0-boundary-diagnostic-20261016'
AUDIT=ROOT/'data/ilvis0-final-two-audit-20261018'
OUTPUT=ROOT/'data/ilvis0-final-pair-boundary-20261018'
GUIDE=ROOT/'docs/ilvis0-final-pair-boundary-20261018'
SID='370cec66878c4c1cf84b4ceb'
CASE='bias1_profiled_removal'
VERSION='ilvis0-final-profiled-pair-boundary-v1'
load,sha=parent.load,parent.sha


def make_plan(cm,cs,om,audit):
    old={t['identity']:t for t in cm['plan']['tasks']}
    rows=[r for r in cs['results'] if r['kind']=='control']
    if (cs['state']!='complete' or audit['state']!='complete' or len(rows)!=2
            or len({r['identity'] for r in rows})!=2 or not all(r['passed'] and r['status']=='complete' for r in rows)):
        raise ValueError('two complete passing control sources required')
    expected={f'{SID}::{CASE}::sphere_rotating::{role}' for role in ('primary','repeat')}
    targets=[t for t in om['plan']['tasks'] if t['source_identity'] in expected]
    reports=[r for r in audit['reports'] if r['source_identity']==f'{SID}::{CASE}::sphere_rotating::primary']
    if (len(targets)!=2 or {t['source_identity'] for t in targets}!=expected or len(reports)!=1
            or not reports[0]['needs_correction_investigation']):
        raise ValueError('exact original pair and audited correction failure required')
    result=[]
    for original,row in [(old[r['identity']],r) for r in rows]+[(t,t['fit']) for t in targets]:
        task=copy.deepcopy(original);control=task['kind']=='control';fit=task['fit'];names=fit['active_parameters']
        point=row['normalized_parameters'];cost=row['residual_sum_squares']
        if (len(point)!=len(names) or names.count('time_offset')!=1 or len(set(names))!=len(names)
                or any(not math.isfinite(v) or abs(v)>1 for v in point) or not math.isfinite(cost) or cost<0):
            raise ValueError('complete finite feasible source layout required')
        identity=row['identity'] if control else task['source_identity']
        if not control and (task['task']['segment_id']!=SID or task['task']['case_id']!=CASE
                or task['task']['model']!='sphere_rotating'):
            raise ValueError('fixed target, processing case and model required')
        role='control' if control else identity.rsplit('::',1)[1]
        directory=PARENT if control else ROOT/'docs'/task['stage']
        if not control:
            task['context_epoch']=dict(path=str(directory/fit['epoch_file']),sha256=fit['epoch_sha256']) if 'epoch_file' in fit else None
        task.update(identity=identity+'::final_pair_representable_check',source_identity=identity,kind='control' if control else 'target',
            start_role=role,source_role='control' if control else CASE+'/'+role,maximum_diagnostic_calls=3 if control else 26,
            source_artifact=str(directory/row['linearization_file']),source_artifact_sha256=row['linearization_sha256'],
            fit=dict(active_parameters=list(names),normalized_parameters=list(point),residual_sum_squares=cost))
        if not control:task['exact_point']=list(point)
        result.append(task)
    return dict(version=VERSION,tasks=result,maximum_starts=4,maximum_optimizer_starts=0,maximum_native_evaluations=58,
        maximum_geometry_queries=402048,maximum_affine_solves=6,maximum_clock_window_s=1e-6,numerical_threads=4,
        retries=0,scientific_stopping_limits_changed=False)


def context_bytes(saved,epochs,gps):
    times=epochs['times_s']
    if (len(times)!=len(gps) or len(saved['residual'])!=3*len(times)
            or ('times_s' in saved and saved['times_s']!=times) or ('gps' in saved and saved['gps']!=gps)):
        raise ValueError('exact saved epoch/receiver layout required')
    payload=dict(saved,times_s=times,gps=gps)
    return gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0)


def source_context(task):
    source=task['original_linearization'];epoch=task['context_epoch']
    if sha(Path(source['path']))!=source['sha256'] or sha(Path(epoch['path']))!=epoch['sha256']:
        raise ValueError('original endpoint context changed')
    with gzip.open(source['path'],'rt') as stream:saved=json.load(stream)
    with gzip.open(epoch['path'],'rt') as stream:epochs=json.load(stream)
    return context_bytes(saved,epochs,task['task']['selected']['segment']['receiver_fixes'])


def source_plan():
    plan=make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),load(ORIGINAL/'manifest.json'),load(AUDIT/'summary.json'))
    for task in plan['tasks']:
        if task['kind']=='control':continue
        if task['context_epoch'] is None:raise ValueError('original saved epochs required')
        task['original_linearization']=dict(path=task['source_artifact'],sha256=task['source_artifact_sha256'])
        data=source_context(task)
        task.update(source_artifact=str(OUTPUT/'saved-endpoints'/(task['start_role']+'.json.gz')),
            source_artifact_sha256=hashlib.sha256(data).hexdigest())
    return plan


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name in ('analysis/tests/ilvis0_final_pair_worker.py','analysis/tests/test_ilvis0_final_pair_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    parent.parent.parent.parent.prior.check_hashes(values)
    return values


def compare_cases(results,tasks,directory,base,assumption):
    result=parent.compare_cases(results,tasks,directory,base,assumption)
    result['case_id']=CASE
    return result


def executor_source(source):
    source=parent.executor_source(source)
    old="str(ROOT/'analysis/tests/test_ilvis0_representable_worker.py')"
    if source.count(old)!=1:raise ValueError('unrecognized qualified executor tests')
    return source.replace(old,"str(ROOT/'analysis/tests/test_ilvis0_final_pair_worker.py')").replace(
        '# Representable side-probe results','# Final profiled-pair boundary results')


def prepare(executor):
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return executor.verify()
    executor.prior.sealed(PARENT,published=PARENT_GUIDE)
    executor.prior.sealed(AUDIT,published=ROOT/'docs'/AUDIT.name)
    qualification=executor.QUALIFICATION;q=load(qualification/'result.json');c=load(qualification/'completion.json')
    if (not q['passed'] or q['tests']!=executor.TESTS or c['manifest_sha256']!=sha(qualification/'manifest.json')
            or c['result_sha256']!=sha(qualification/'result.json')):raise ValueError('software qualification failed')
    old=load(PARENT/'manifest.json');original=load(ORIGINAL/'manifest.json');plan=source_plan();values=sources()
    if values!=load(qualification/'manifest.json')['sources']:raise ValueError('qualified sources changed')
    if any(old[k]!=original[k] for k in ('extended_kernel','ordinary_value_kernel','environment')):
        raise ValueError('source numerical engine/environment mismatch')
    inputs=executor.prior.scientific_inputs(old['inputs'])
    inputs[str(ORIGINAL/'manifest.json')]=sha(ORIGINAL/'manifest.json')
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
        (PARENT_GUIDE,('evidence-receipt.json',)),(AUDIT,('manifest.json','summary.json','completion.json')),
        (ROOT/'docs'/AUDIT.name,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
        (qualification,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={}
    for task in plan['tasks']:
        path=task['task']['selected']['source_path'];originals[path]=original['originals'][path]
        if task['kind']=='target':
            source=task['original_linearization'];epoch=task['context_epoch']
            directory=ROOT/'docs'/task['stage'];receipt=load(directory/'evidence-receipt.json')
            for artifact in (source,epoch):
                if receipt['artifacts'].get(Path(artifact['path']).name)!=artifact['sha256']:
                    raise ValueError('unsealed original endpoint/epochs')
                inputs[artifact['path']]=artifact['sha256']
            inputs[str(directory/'evidence-receipt.json')]=sha(directory/'evidence-receipt.json')
            destination=Path(task['source_artifact']);destination.parent.mkdir(exist_ok=True)
            from lll.ilvis0_receipt_journal import durable_write
            durable_write(destination,source_context(task),replace=False)
        inputs[task['source_artifact']]=task['source_artifact_sha256']
    executor.prior.check_hashes(inputs);executor.prior.check_hashes(originals)
    if shutil.disk_usage(OUTPUT).free<1024**3:raise ValueError('one GiB free storage required')
    e=executor.prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=old['extended_kernel']:raise ValueError('native integration changed')
    executor.prior.snapshot(OUTPUT,values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    executor.write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),extended_kernel=extended,ordinary_value_kernel=old['ordinary_value_kernel'],
        scientific_decision='abstain',original_labels_changed=False))
    executor.write(OUTPUT/'authorization.json',executor.allowance())
    return executor.verify()


def build_executor():
    executor=types.ModuleType('_final_pair_boundary_executor');executor.__file__=str(Path(__file__).resolve())
    exec(compile(executor_source(parent.TEMPLATE.read_text()),str(parent.TEMPLATE),'exec'),executor.__dict__)
    executor.__file__=str(Path(__file__).resolve());executor.OUTPUT=OUTPUT;executor.GUIDE=GUIDE;executor.VERSION=VERSION
    executor.STOPPED=PARENT;executor.AUDIT=AUDIT;executor.QUALIFICATION=OUTPUT/'software-controls';executor.TESTS=33
    executor.source_plan=source_plan;executor.sources=sources;executor.compare_cases=compare_cases
    executor.unique_directories=parent.parent.unique_directories
    executor.prepare=partial(prepare,executor)
    return executor


if __name__=='__main__':build_executor().main()
