# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite two-case field-endpoint checks; zero-field timing work is separate."""
import copy
import gzip
import hashlib
import math
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_scaled_pair_worker as parent

PARENT=parent.OUTPUT
PARENT_GUIDE=parent.GUIDE
ORIGINAL=parent.parent.parent.ORIGINAL
OUTPUT=ROOT/'data/ilvis0-last-field-boundary-20261018'
GUIDE=ROOT/'docs/ilvis0-last-field-boundary-20261018'
SID='b4e44ddc0f130ecd45674c78'
CASES=('bias1_unsubtracted','bias1_profiled_removal')
VERSION='ilvis0-last-two-case-field-boundary-v1'
load,sha=parent.parent.parent.load,parent.parent.parent.sha


def make_plan(cm,cs,om):
    controls={t['identity']:t for t in cm['plan']['tasks'] if t['kind']=='control'}
    rows=[r for r in cs['results'] if r['kind']=='control']
    if (cs['state']!='complete' or len(controls)!=2 or len(rows)!=2
            or {r['identity'] for r in rows}!=set(controls)
            or not all(r['status']=='complete' and r['passed'] for r in rows)):
        raise ValueError('exact two passing control sources required')
    expected={f'{SID}::{case}::sphere_rotating::{role}' for case in CASES for role in ('primary','repeat')}
    targets=[t for t in om['plan']['tasks'] if t['source_identity'] in expected]
    if len(targets)!=4 or {t['source_identity'] for t in targets}!=expected:
        raise ValueError('exact four original field endpoints required')
    tasks=[]
    for original,row in [(controls[r['identity']],r) for r in rows]+[(t,t['fit']) for t in targets]:
        item=copy.deepcopy(original);control=item['kind']=='control';old=item['fit'];names=old['active_parameters']
        point=row['normalized_parameters'];cost=row['residual_sum_squares']
        if (len(point)!=len(names) or len(set(names))!=len(names) or names.count('time_offset')!=1
                or any(not math.isfinite(v) or abs(v)>1 for v in point) or not math.isfinite(cost) or cost<0):
            raise ValueError('complete finite feasible endpoint layout required')
        identity=row['identity'] if control else item['source_identity'];role='control' if control else identity.rsplit('::',1)[1]
        context=item['task'];case=context['case_id']
        if not control and (context['segment_id']!=SID or case not in CASES or context['model']!='sphere_rotating'):
            raise ValueError('unchanged last-stretch field model and processing cases required')
        directory=PARENT if control else ROOT/'docs'/item['stage']
        if not control:
            item['context_epoch']=dict(path=str(directory/old['epoch_file']),sha256=old['epoch_sha256'])
        item.update(identity=identity+'::last_field_scaled_check',source_identity=identity,kind='control' if control else 'target',
            start_role=role,source_role='control' if control else case+'/'+role,
            maximum_diagnostic_calls=3 if control else 26,source_artifact=str(directory/row['linearization_file']),
            source_artifact_sha256=row['linearization_sha256'],fit=dict(active_parameters=list(names),
                normalized_parameters=list(point),residual_sum_squares=cost))
        if not control:item['exact_point']=list(point)
        tasks.append(item)
    return dict(version=VERSION,tasks=tasks,maximum_starts=6,maximum_optimizer_starts=0,
        maximum_native_evaluations=110,maximum_geometry_queries=804096,maximum_affine_solves=10,
        maximum_clock_window_s=1e-6,numerical_threads=4,retries=0,
        scientific_stopping_limits_changed=False,zero_field_timing_profile_included=False)


def source_plan():
    plan=make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),load(ORIGINAL/'manifest.json'))
    for t in plan['tasks']:
        if t['kind']=='control':continue
        t['original_linearization']=dict(path=t['source_artifact'],sha256=t['source_artifact_sha256'])
        data=parent.parent.source_context(t)
        name=t['task']['case_id']+'-'+t['start_role']+'.json.gz'
        t.update(source_artifact=str(OUTPUT/'saved-endpoints'/name),source_artifact_sha256=hashlib.sha256(data).hexdigest())
    return plan


def sources():
    values=parent.sources()
    for name in ('analysis/tests/ilvis0_last_field_worker.py','analysis/tests/test_ilvis0_last_field_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    for directory,names in ((PARENT,('manifest.json','summary.json')),(ORIGINAL,('manifest.json',))):
        for name in names:values[str(directory/name)]=sha(directory/name)
    plan=make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),load(ORIGINAL/'manifest.json'))
    for t in plan['tasks']:
        if t['kind']=='control':continue
        values[t['source_artifact']]=t['source_artifact_sha256']
        values[t['context_epoch']['path']]=t['context_epoch']['sha256']
    return values


def compare_cases(results,tasks,directory,base,assumption):
    comparisons={}
    for case in CASES:
        subset=[t for t in tasks if t['kind']=='control' or t['task']['case_id']==case]
        ids={t['identity'] for t in subset};rows=[r for r in results if r['identity'] in ids]
        metrics=parent.parent.parent.compare_cases(rows,subset,directory,base,assumption)
        metrics['case_id']=case;comparisons[case]=metrics
    return dict(cases=comparisons,agreement_passed=all(r['agreement_passed'] for r in comparisons.values()),
        both_cases_full_checks_passed=all(r['both_endpoints_passed'] for r in comparisons.values()),
        global_optimum_proven=False)


def executor_source(source):
    source=parent.executor_source(source)
    edits=[('maximum_starts=4','maximum_starts=6',2),('maximum_native_evaluations=58','maximum_native_evaluations=110',3),
        ("len(book.read('starts'))>4 or len(calls)>58","len(book.read('starts'))>6 or len(calls)>110",1),
        ('total=4','total=6',1),
        ("str(ROOT/'analysis/tests/test_ilvis0_scaled_pair_worker.py')","str(ROOT/'analysis/tests/test_ilvis0_last_field_worker.py')",1),
        ('# Scaled-affine pair results','# Final-stretch field-boundary results',1)]
    for old,new,count in edits:
        if source.count(old)!=count:raise ValueError('unrecognized frozen executor: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    module=types.ModuleType('_last_field_boundary_executor');module.__file__=str(Path(__file__).resolve())
    original=Path(parent.parent.parent.__file__)
    exec(compile(original.read_text(),str(original),'exec'),module.__dict__)
    for key,value in dict(PARENT=PARENT,PARENT_GUIDE=PARENT_GUIDE,OUTPUT=OUTPUT,GUIDE=GUIDE,VERSION=VERSION,
            source_context=parent.parent.source_context,source_plan=source_plan,make_plan=make_plan,
            compare_cases=compare_cases,sources=sources,executor_source=executor_source).items():
        setattr(module,key,value)
    executor=module.build_executor();executor.source_plan=source_plan;executor.compare_cases=compare_cases;executor.TESTS=34
    return executor


if __name__=='__main__':build_executor().main()
