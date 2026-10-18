# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched two-case cluster checks from four completed free-time endpoints."""
import copy
from functools import partial
import math
from pathlib import Path
import shutil
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_clustered_boundary_worker as parent

TEMPLATE=parent.TEMPLATE
PARENT=ROOT/'data/ilvis0-remaining-free-time-v2-20261018'
PARENT_GUIDE=ROOT/'docs/ilvis0-remaining-free-time-v2-20261018'
AUDIT=ROOT/'data/ilvis0-remaining-free-time-audit-20261018'
OUTPUT=ROOT/'data/ilvis0-remaining-boundary-20261018'
GUIDE=ROOT/'docs/ilvis0-remaining-boundary-20261018'
SID='0e73879f98c3b701fd7c42df'
CASES=('bias1_unsubtracted','bias1_profiled_removal')
VERSION='ilvis0-remaining-two-case-cluster-diagnostic-v1'
load,sha,write=parent.parent.load,parent.parent.sha,parent.parent.write


def make_plan(manifest,summary,audit):
    tasks=manifest['plan']['tasks'];rows=summary['results']
    old={t['identity']:t for t in tasks};saved={r['identity']:r for r in rows}
    expected={f'{SID}::{case}::sphere_still::free_time_{role}' for case in CASES for role in ('primary','repeat')}
    audits={r['identity']:r for r in audit['targets']}
    if (summary['state']!='complete' or audit['state']!='complete' or len(tasks)!=6 or len(rows)!=6
            or len(old)!=6 or len(saved)!=6 or old.keys()!=saved.keys()
            or len(audit['targets'])!=4 or audits.keys()!=expected):
        raise ValueError('complete exact six-result source and four-endpoint audit required')
    controls=[r for r in rows if r['kind']=='control'];targets=[r for r in rows if r['kind']=='target']
    if (len(controls)!=2 or not all(r['status']=='complete' and r['converged'] for r in controls)
            or len(targets)!=4 or {r['identity'] for r in targets}!=expected
            or not all(r['status']=='complete' and not r['converged'] for r in targets)):
        raise ValueError('both passing controls and all four failed free-time endpoints required')
    result=[]
    for row in controls+targets:
        task=copy.deepcopy(old[row['identity']]);kind=row['kind'];names=task['fit']['active_parameters']
        point=row['normalized_parameters']
        if (names.count('time_offset')!=1 or len(point)!=len(names)
                or any(not math.isfinite(v) or abs(v)>1 for v in point)
                or not math.isfinite(row['residual_sum_squares']) or row['residual_sum_squares']<0):
            raise ValueError('full finite feasible source endpoint required')
        if kind=='target':
            geometry=audits[row['identity']]['clock_geometry'];context=task['task']
            if (context['segment_id']!=SID or context['case_id']!=row['identity'].split('::')[1]
                    or context['case_id'] not in CASES or context['model']!='sphere_still'
                    or row['active_parameters']!=names or geometry['original_point']!=point[names.index('time_offset')]):
                raise ValueError('unchanged case, model, layout and audited timing required')
        role='control' if kind=='control' else task['task']['case_id']+'/'+task['start_role']
        task.update(kind=kind,source_role=role,source_identity=row['identity'],
            identity=row['identity']+'::remaining_cluster_check',maximum_diagnostic_calls=3 if kind=='control' else 26,
            source_artifact=str(PARENT/row['linearization_file']),source_artifact_sha256=row['linearization_sha256'],
            fit=dict(active_parameters=list(names),normalized_parameters=list(point),residual_sum_squares=row['residual_sum_squares']))
        if kind=='target':task['exact_point']=list(point)
        result.append(task)
    return dict(version=VERSION,tasks=result,maximum_starts=6,maximum_optimizer_starts=0,
        maximum_native_evaluations=110,maximum_geometry_queries=804096,maximum_affine_solves=10,
        maximum_clock_window_s=1e-6,numerical_threads=4,retries=0,final_stopping_rule_changed=False)


def source_plan():return make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),load(AUDIT/'summary.json'))


def unique_directories(*directories):return list(dict.fromkeys(Path(p).resolve() for p in directories))


def compare_cases(results,tasks,directory,base,assumption):
    from ilvis0_remaining_free_time_worker import compare_cases as compare_free_time
    sources={t['identity']:t['source_identity'] for t in tasks}
    adapted=[dict(row,identity=sources[row['identity']],converged=row['passed']) for row in results]
    return compare_free_time(adapted,directory,base,assumption)


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name,h in load(parent.OUTPUT/'manifest.json')['sources'].items():
        if name in values and values[name]!=h:raise ValueError('frozen dependency versions disagree')
        values[name]=h
    for name in ('analysis/tests/ilvis0_remaining_boundary_worker.py','analysis/tests/test_ilvis0_remaining_boundary_worker.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    parent.parent.prior.check_hashes(values);return values


def executor_source(source):
    source=parent.executor_source(source)
    start=source.index("        targets=[r for r in results if r['kind']=='target'];repeat=")
    end=source.index('        verify(originals=False);calls=',start)
    source=source[:start]+"        repeat=compare_cases(results,m['plan']['tasks'],OUTPUT,base,assumption)\n"+source[end:]
    edits=[('maximum_starts=4','maximum_starts=6',2),
        ('maximum_native_evaluations=58','maximum_native_evaluations=110',3),
        ("len(book.read('starts'))>4 or len(calls)>58","len(book.read('starts'))>6 or len(calls)>110",1),
        ('total=4','total=6',1),
        ('for directory in (OUTPUT,STOPPED,VERIFIED,AUDIT,CLUSTER_PARENT,LEFT_AUDIT):',
         'for directory in unique_directories(OUTPUT,STOPPED,AUDIT):',1),
        ("str(ROOT/'analysis/tests/test_ilvis0_clustered_boundary_worker.py')",
         "str(ROOT/'analysis/tests/test_ilvis0_remaining_boundary_worker.py')",1),
        ('# Exact-boundary diagnostic results','# Matched two-case boundary results',1),
        ('The interrupted trial and original fit labels remain unchanged.',
         'All original free-time failures and fit labels remain unchanged.',1),
        ("if source['times_s']!=times.tolist() or source['gps']!=gps.tolist():",
         "if (source['times_s']!=times.tolist() or source['gps']!=gps.tolist() or source['active_parameters']!=item['fit']['active_parameters'] or source['normalized_parameters']!=item['fit']['normalized_parameters']):",1)]
    for old,new,count in edits:
        if source.count(old)!=count:raise ValueError('unrecognized frozen executor layout: '+old)
        source=source.replace(old,new)
    return source


def prepare(executor):
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return executor.verify()
    executor.prior.sealed(PARENT,published=PARENT_GUIDE)
    executor.prior.sealed(AUDIT,published=ROOT/'docs'/AUDIT.name)
    qualification=executor.QUALIFICATION;q=load(qualification/'result.json');c=load(qualification/'completion.json')
    if (not q['passed'] or q['tests']!=executor.TESTS or c['manifest_sha256']!=sha(qualification/'manifest.json')
            or c['result_sha256']!=sha(qualification/'result.json')):raise ValueError('software qualification failed')
    old=load(PARENT/'manifest.json');plan=executor.source_plan();values=executor.sources()
    if values!=load(qualification/'manifest.json')['sources']:raise ValueError('qualified sources changed')
    inputs=executor.prior.scientific_inputs(old['inputs'])
    for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
            (PARENT_GUIDE,('evidence-receipt.json',)),(AUDIT,('manifest.json','summary.json','completion.json')),
            (ROOT/'docs'/AUDIT.name,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
            (qualification,('manifest.json','result.json','completion.json','tests.xml'))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    originals={}
    for task in plan['tasks']:
        path=task['task']['selected']['source_path'];originals[path]=old['originals'][path]
        inputs[task['source_artifact']]=task['source_artifact_sha256']
    executor.prior.check_hashes(inputs);executor.prior.check_hashes(originals)
    if shutil.disk_usage(OUTPUT).free<1024**3:raise ValueError('one GiB free storage required')
    e=executor.prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended!=old['extended_kernel']:raise ValueError('native integration changed')
    executor.prior.snapshot(OUTPUT,values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
    write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
        environment=e.base.runtime.numerical_environment(),extended_kernel=extended,ordinary_value_kernel=old['ordinary_value_kernel'],
        scientific_decision='abstain',original_labels_changed=False))
    write(OUTPUT/'authorization.json',executor.allowance());return executor.verify()


def build_executor():
    executor=types.ModuleType('_ilvis0_remaining_cluster_executor')
    executor.__file__=str(Path(__file__).resolve())
    exec(compile(executor_source(TEMPLATE.read_text()),str(TEMPLATE),'exec'),executor.__dict__)
    executor.OUTPUT=OUTPUT;executor.GUIDE=GUIDE;executor.STOPPED=PARENT;executor.VERIFIED=PARENT;executor.AUDIT=AUDIT
    executor.QUALIFICATION=OUTPUT/'software-controls';executor.VERSION=VERSION;executor.TESTS=18
    executor.make_plan=make_plan;executor.source_plan=source_plan;executor.sources=sources
    executor.unique_directories=unique_directories;executor.compare_cases=compare_cases
    executor.prepare=partial(prepare,executor)
    return executor


if __name__=='__main__':build_executor().main()
