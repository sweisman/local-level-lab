# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite two-sided timing checks for the last zero-field solution pairs."""
import copy
from functools import partial
import math
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_last_field_worker as parent

PARENT=parent.OUTPUT
PARENT_GUIDE=parent.GUIDE
FREE=ROOT/'data/ilvis0-last-free-time-20261018'
FREE_GUIDE=ROOT/'docs'/FREE.name
AUDIT=ROOT/'data/ilvis0-last-correction-audit-20261018'
OUTPUT=ROOT/'data/ilvis0-last-zero-boundary-20261018'
GUIDE=ROOT/'docs'/OUTPUT.name
SID=parent.SID
CASES=parent.CASES
VERSION='ilvis0-last-two-case-zero-field-boundary-v1'
load,sha=parent.load,parent.sha


def make_plan(cm,cs,fm,fs):
    controls={t['identity']:t for t in cm['plan']['tasks'] if t['kind']=='control'}
    checks=[r for r in cs['results'] if r['kind']=='control']
    if (cs['state']!='complete' or len(controls)!=2 or len(checks)!=2
            or set(controls)!={r['identity'] for r in checks}
            or not all(r['status']=='complete' and r['passed'] for r in checks)):
        raise ValueError('two complete passing control sources required')
    originals={t['identity']:t for t in fm['plan']['tasks']};targets=[r for r in fs['results'] if r['kind']=='target']
    expected={f'{SID}::{case}::sphere_still::free_time_{role}' for case in CASES for role in ('primary','repeat')}
    if (fs['state']!='complete' or len(fs['results'])!=6 or len(originals)!=6 or len(targets)!=4
            or {r['identity'] for r in targets}!=expected
            or any(r['status']!='complete' or r['converged'] for r in targets)):
        raise ValueError('exact four completed failed free-timing endpoints required')
    tasks=[]
    for original,row,control in ([(controls[r['identity']],r,True) for r in checks]
                                +[(originals[r['identity']],r,False) for r in targets]):
        item=copy.deepcopy(original);names=original['fit']['active_parameters'];point=row['normalized_parameters']
        cost=row['residual_sum_squares'];context=item['task']
        if (row.get('active_parameters',names)!=names or len(names)!=len(point) or len(set(names))!=len(names) or names.count('time_offset')!=1
                or any(not math.isfinite(v) or abs(v)>1 for v in point) or not math.isfinite(cost) or cost<0):
            raise ValueError('finite feasible complete endpoint required')
        if not control and (context['segment_id']!=SID or context['case_id'] not in CASES
                or context['model']!='sphere_still' or context['case_id']!=row['identity'].split('::')[1]):
            raise ValueError('unchanged target, zero-field model and processing case required')
        directory=PARENT if control else FREE_GUIDE
        role='control' if control else row['start_role']
        item.update(identity=row['identity']+'::zero_boundary_v1',source_identity=row['identity'],
            kind='control' if control else 'target',start_role=role,
            source_role='control' if control else context['case_id']+'/'+role,
            maximum_diagnostic_calls=3 if control else 26,
            source_artifact=str(directory/row['linearization_file']),source_artifact_sha256=row['linearization_sha256'],
            fit=dict(active_parameters=list(names),normalized_parameters=list(point),residual_sum_squares=cost))
        if not control:item['exact_point']=list(point)
        tasks.append(item)
    return dict(version=VERSION,tasks=tasks,maximum_starts=6,maximum_optimizer_starts=0,
        maximum_native_evaluations=110,maximum_geometry_queries=804096,maximum_affine_solves=10,
        maximum_clock_window_s=1e-6,numerical_threads=4,retries=0,scientific_stopping_limits_changed=False)


def source_plan():
    return make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),load(FREE/'manifest.json'),load(FREE/'summary.json'))


def sources():
    values=parent.sources();values.update(load(FREE/'manifest.json')['sources'])
    for name in ('analysis/tests/ilvis0_last_zero_boundary_worker.py','analysis/tests/test_ilvis0_last_zero_boundary_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    for directory in (FREE,FREE_GUIDE,AUDIT,ROOT/'docs'/AUDIT.name):
        names=('manifest.json','summary.json','completion.json')
        if directory.parent.name=='docs':names+=('evidence-receipt.json',)
        for name in names:values[str(directory/name)]=sha(directory/name)
    for task in source_plan()['tasks']:values[task['source_artifact']]=task['source_artifact_sha256']
    return values


def executor_source(source):
    source=parent.executor_source(source)
    old="str(ROOT/'analysis/tests/test_ilvis0_last_field_worker.py')"
    if source.count(old)!=1:raise ValueError('unrecognized qualification list')
    return source.replace(old,"str(ROOT/'analysis/tests/test_ilvis0_last_zero_boundary_worker.py')").replace(
        '# Final-stretch field-boundary results','# Final-stretch zero-field boundary results')


def prepare(executor):
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return executor.verify()
    for runtime,public in ((PARENT,PARENT_GUIDE),(FREE,FREE_GUIDE),(AUDIT,ROOT/'docs'/AUDIT.name)):
        executor.prior.sealed(runtime,published=public)
    q=executor.QUALIFICATION;result=load(q/'result.json');completion=load(q/'completion.json')
    if (not result['passed'] or result['tests']!=executor.TESTS
            or completion['manifest_sha256']!=sha(q/'manifest.json')
            or completion['result_sha256']!=sha(q/'result.json')):raise ValueError('software qualification failed')
    values=sources();old=load(PARENT/'manifest.json');free=load(FREE/'manifest.json')
    if values!=load(q/'manifest.json')['sources']:raise ValueError('qualified sources changed')
    if any(old[k]!=free[k] for k in ('environment','extended_kernel','ordinary_value_kernel')):
        raise ValueError('source environment or numerical kernel mismatch')
    plan=source_plan();inputs=executor.prior.scientific_inputs(old['inputs'])
    inputs.update(executor.prior.scientific_inputs(free['inputs']))
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
            (PARENT_GUIDE,('evidence-receipt.json',)),(FREE,('manifest.json','summary.json','completion.json')),
            (FREE_GUIDE,('evidence-receipt.json',)),(AUDIT,('manifest.json','summary.json','completion.json')),
            (ROOT/'docs'/AUDIT.name,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
            (q,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={}
    for task in plan['tasks']:
        path=task['task']['selected']['source_path']
        originals[path]=(old if task['kind']=='control' else free)['originals'][path]
        inputs[task['source_artifact']]=task['source_artifact_sha256']
    executor.prior.check_hashes({**values,**inputs,**originals})
    if shutil.disk_usage(OUTPUT).free<1024**3:raise ValueError('one GiB free storage required')
    engine=executor.prior.engine();_,extended=engine.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=old['extended_kernel']:raise ValueError('native integration changed')
    executor.prior.snapshot(OUTPUT,values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    executor.write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=engine.base.runtime.numerical_environment(),extended_kernel=extended,ordinary_value_kernel=old['ordinary_value_kernel'],
        scientific_decision='abstain',original_labels_changed=False))
    executor.write(OUTPUT/'authorization.json',executor.allowance());return executor.verify()


def build_executor():
    # Rebuild the checked source with the qualification test path for this scope.
    original=Path(parent.parent.parent.parent.__file__)
    import types
    module=types.ModuleType('_last_zero_boundary_source');module.__file__=str(Path(__file__).resolve())
    exec(compile(original.read_text(),str(original),'exec'),module.__dict__)
    for name,value in dict(PARENT=PARENT,PARENT_GUIDE=PARENT_GUIDE,OUTPUT=OUTPUT,GUIDE=GUIDE,VERSION=VERSION,
            AUDIT=AUDIT,source_plan=source_plan,sources=sources,executor_source=executor_source,
            compare_cases=parent.compare_cases).items():setattr(module,name,value)
    executor=module.build_executor()
    executor.__file__=str(Path(__file__).resolve());executor.TESTS=40;executor.VERIFIED=FREE;executor.AUDIT=AUDIT
    executor.prepare=partial(prepare,executor)
    return executor


if __name__=='__main__':build_executor().main()
