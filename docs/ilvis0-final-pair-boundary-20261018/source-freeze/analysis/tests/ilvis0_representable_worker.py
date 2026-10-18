# SPDX-License-Identifier: AGPL-3.0-or-later
"""New finite geometry candidate; previous studies and failed labels are sealed."""
import copy
import gzip
import json
import math
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_remaining_boundary_worker as parent

TEMPLATE=parent.TEMPLATE
PARENT=parent.OUTPUT
PARENT_GUIDE=parent.GUIDE
AUDIT=ROOT/'data/ilvis0-narrow-boundary-audit-v2-20261018'
OUTPUT=ROOT/'data/ilvis0-representable-boundary-20261018'
GUIDE=ROOT/'docs/ilvis0-representable-boundary-20261018'
VERSION='ilvis0-representable-boundary-observed-v1'
load,sha=parent.load,parent.sha


def make_plan(manifest,summary,audit):
    old={t['identity']:t for t in manifest['plan']['tasks']};rows=summary['results']
    if (summary['state']!='complete' or audit['state']!='complete' or len(rows)!=6 or len(old)!=6
            or len({r['identity'] for r in rows})!=6 or set(old)!={r['identity'] for r in rows}
            or any(r['status']!='complete' for r in rows)):
        raise ValueError('complete exact source diagnostic required')
    controls=[r for r in rows if r['kind']=='control']
    targets=[r for r in rows if r['kind']=='target' and not r['passed']]
    expected={f'{parent.SID}::bias1_unsubtracted::sphere_still::free_time_{role}::remaining_cluster_check'
              for role in ('primary','repeat')}
    audits={r['identity']:r for r in audit['targets']}
    paired=summary['repeatability']['cases']['bias1_profiled_removal']
    if (len(controls)!=2 or not all(r['passed'] for r in controls) or len(targets)!=2
            or {r['identity'] for r in targets}!=expected or len(audits)!=2 or set(audits)!=expected
            or not paired['agreement_passed'] or not paired['both_full_fits_passed']):
        raise ValueError('fresh-control sources, failed unsubtracted pair and passing profiled pair required')
    result=[]
    for row in controls+targets:
        task=copy.deepcopy(old[row['identity']]);point=row['normalized_parameters'];names=task['fit']['active_parameters']
        if (len(point)!=len(names) or names.count('time_offset')!=1
                or any(not math.isfinite(v) or abs(v)>1 for v in point)
                or not math.isfinite(row['residual_sum_squares']) or row['residual_sum_squares']<0):
            raise ValueError('unchanged finite feasible source point required')
        if row['kind']=='target':
            context=task['task'];evidence=audits[row['identity']]
            if (context['segment_id']!=parent.SID or context['case_id']!='bias1_unsubtracted'
                    or context['model']!='sphere_still' or row['reason']!='side_geometry_unsupported'
                    or evidence['probe_guard_passed'] or not evidence['probes_distinct']
                    or not evidence['adjacent_clock_states_distinct'] or evidence['clock_state_matches']!=[True]*4
                    or evidence['knot_normalized']!=row['search']['point']):
                raise ValueError('exact audited narrow-clock failure required')
        task.update(identity=row['identity']+'::representable_side_check',source_identity=row['identity'],
            maximum_diagnostic_calls=3 if row['kind']=='control' else 26,
            source_role='control' if row['kind']=='control' else task['task']['case_id']+'/'+task['start_role'],
            source_artifact=str(PARENT/row['linearization_file']),source_artifact_sha256=row['linearization_sha256'],
            fit=dict(active_parameters=list(names),normalized_parameters=list(point),residual_sum_squares=row['residual_sum_squares']))
        if row['kind']=='target':task['exact_point']=list(point)
        result.append(task)
    return dict(version=VERSION,tasks=result,maximum_starts=4,maximum_optimizer_starts=0,
        maximum_native_evaluations=58,maximum_geometry_queries=402048,maximum_affine_solves=6,
        maximum_clock_window_s=1e-6,numerical_threads=4,retries=0,geometry_guard_changed=True,
        scientific_stopping_limits_changed=False)


def source_plan():return make_plan(load(PARENT/'manifest.json'),load(PARENT/'summary.json'),load(AUDIT/'summary.json'))


def sources():
    values=dict(load(PARENT/'manifest.json')['sources'])
    for name in ('analysis/lll/ilvis0_representable_boundary.py','analysis/tests/test_ilvis0_representable_boundary.py',
                 'analysis/tests/ilvis0_representable_worker.py','analysis/tests/test_ilvis0_representable_worker.py',
                 'analysis/tests/ilvis0_clock_reference.cpp','analysis/tests/test_ilvis0_boundary_adapter.py'):
        values[str(ROOT/name)]=sha(ROOT/name)
    parent.parent.parent.prior.check_hashes(values);return values


def compare_cases(results,tasks,directory,base,assumption):
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_solver_position as position
    from ilvis0_profile_seeded_worker import repeat_metrics
    rows=[r for r in results if r['kind']=='target'];expected={t['identity'] for t in tasks if t['kind']=='target'}
    if len(rows)!=2 or {r['identity'] for r in rows}!=expected:raise ValueError('exact primary/repeat pair required')
    result=dict(agreement_passed=False,both_endpoints_passed=all(r['passed'] for r in rows),case_id='bias1_unsubtracted')
    if all(r.get('linearization_file') for r in rows):
        local=[]
        for row in rows:
            path=directory/row['linearization_file']
            if path.name!=row['linearization_file'] or sha(path)!=row['linearization_sha256']:raise ValueError('repeat evidence changed')
            with gzip.open(path,'rt') as stream:local.append(json.load(stream))
        gps=np.array(local[0]['gps']);times=np.array(local[0]['times_s'])
        blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
        cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
        conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov))
        result.update(repeat_metrics(*local,lambda d:position.physical_residual_step(conversion,d)))
        result['prediction_agreement_passed']=result['agreement_passed']
        result['agreement_passed']=bool(result['agreement_passed'] and result['both_endpoints_passed'])
    return result


def executor_source(source):
    source=parent.executor_source(source)
    edits=[('from lll.ilvis0_clustered_boundary import check_endpoint',
            'from lll.ilvis0_representable_boundary import check_endpoint',1),
        ('maximum_starts=6','maximum_starts=4',2),
        ('maximum_native_evaluations=110','maximum_native_evaluations=58',3),
        ("len(book.read('starts'))>6 or len(calls)>110","len(book.read('starts'))>4 or len(calls)>58",1),
        ('total=6','total=4',1),('maximum_software_callbacks=512',
         'maximum_software_callbacks=1024,maximum_compiled_motion_calls=81,maximum_compiled_clock_queries=6',1),
        ("str(ROOT/'analysis/tests/test_ilvis0_clustered_boundary.py')",
         "str(ROOT/'analysis/tests/test_ilvis0_representable_boundary.py')",1),
        ("str(ROOT/'analysis/tests/test_ilvis0_remaining_boundary_worker.py')",
         "str(ROOT/'analysis/tests/test_ilvis0_representable_worker.py')",1),
        ('# Matched two-case boundary results','# Representable side-probe results',1)]
    for old,new,count in edits:
        if source.count(old)!=count:raise ValueError('unrecognized frozen executor layout: '+old)
        source=source.replace(old,new)
    marker="        prior.check_hashes(values);write(QUALIFICATION/'result.json',result)"
    if source.count(marker)!=1:raise ValueError('unrecognized qualification result check')
    checks="""        properties=[p.attrib for case in cases for p in case.findall('./properties/property')]
        motion=[int(p['value']) for p in properties if p['name']=='native_evaluations']
        clock_calls=[int(p['value']) for p in properties if p['name']=='compiled_clock_queries']
        result.update(compiled_motion_calls=sum(motion),compiled_clock_queries=sum(clock_calls))
        result['passed']=bool(result['passed'] and len(motion)==3 and sum(motion)<=81 and clock_calls==[6])
"""
    source=source.replace(marker,checks+marker)
    return source


def build_executor():
    module=types.ModuleType('_representable_source_executor');module.__file__=str(Path(__file__).resolve())
    exec(compile(Path(parent.__file__).read_text(),str(Path(parent.__file__)),'exec'),module.__dict__)
    for name,value in dict(PARENT=PARENT,PARENT_GUIDE=PARENT_GUIDE,AUDIT=AUDIT,OUTPUT=OUTPUT,GUIDE=GUIDE,VERSION=VERSION,
            make_plan=make_plan,source_plan=source_plan,sources=sources,executor_source=executor_source,compare_cases=compare_cases).items():
        setattr(module,name,value)
    executor=module.build_executor();executor.TESTS=31
    return executor


if __name__=='__main__':build_executor().main()
