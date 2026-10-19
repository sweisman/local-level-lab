# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release timing in both processing cases without changing physical bounds."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_profile_seeded_worker as parent

TEMPLATE=Path(parent.__file__)
PARENT=ROOT/'data/ilvis0-remaining-time-profile-20261018'
PARENT_GUIDE=ROOT/'docs/ilvis0-remaining-time-profile-20261018'
OUTPUT=ROOT/'data/ilvis0-remaining-free-time-20261018'
GUIDE=ROOT/'docs/ilvis0-remaining-free-time-20261018'
VERSION='ilvis0-remaining-two-case-free-time-v1'
SID='0e73879f98c3b701fd7c42df'
CASES=('bias1_unsubtracted','bias1_profiled_removal')


def make_plan(manifest,summary):
    tasks=manifest['plan']['tasks'];rows=summary['results']
    by_task={t['identity']:t for t in tasks};by_row={r['identity']:r for r in rows}
    expected={(case,anchor,start) for case in CASES for anchor in ('primary','repeat') for start in ('primary','repeat')}
    if (summary['state']!='complete' or not summary['controls_passed'] or len(tasks)!=10 or len(rows)!=10
            or len(by_task)!=10 or len(by_row)!=10 or by_task.keys()!=by_row.keys()
            or not all(r['status']=='complete' and r['conditional_converged'] for r in rows)):
        raise ValueError('complete successful two-case profile required')
    pairs=summary['pair_repeatability']
    if (len(pairs)!=4 or {p['anchor_role'] for p in pairs}!={c+'__'+a for c in CASES for a in ('primary','repeat')}
            or not all(p['both_conditional_fits_passed'] and p['agreement_passed'] for p in pairs)):
        raise ValueError('all four conditional repeat comparisons required')
    profiles=[t for t in tasks if t['kind']=='profile']
    if (len(profiles)!=8 or {(t['task']['case_id'],t['anchor_origin'],t['start_role']) for t in profiles}!=expected
            or any(t['task']['segment_id']!=SID or t['task']['model']!='sphere_still' for t in profiles)):
        raise ValueError('exact unchanged target population required')
    targets=[copy.deepcopy(t) for t in tasks if t['kind']=='control']
    if len(targets)!=2:raise ValueError('both fresh controls required')
    for task in targets:
        task.update(identity=task['source_identity']+'::remaining_free_time_control',maximum_fit_calls=0,maximum_diagnostic_calls=3)
    from lll.ilvis0_profile_seeded import select_seed
    for case in CASES:
        case_tasks=[t for t in profiles if t['task']['case_id']==case]
        names=case_tasks[0]['fit']['active_parameters']
        if names.count('time_offset')!=1 or any(t['fit']['active_parameters']!=names for t in case_tasks):
            raise ValueError('unchanged full parameter layout required')
        for role in ('primary','repeat'):
            candidates=[]
            for t in case_tasks:
                if t['start_role']!=role:continue
                r=by_row[t['identity']]
                candidates.append(dict(anchor_normalized=t['anchor_normalized'],
                    normalized_parameters=list(r['normalized_parameters']),active_parameters=list(names),
                    cost=r['residual_sum_squares'],conditional_passed=True,source_identity=r['identity'],
                    evidence_file=str(PARENT/r['linearization_file']),evidence_sha256=r['linearization_sha256']))
            candidates.sort(key=lambda p:p['anchor_normalized']);anchors=[p['anchor_normalized'] for p in candidates]
            if len(candidates)!=2:raise ValueError('two verified offsets required per starting solution')
            select_seed(candidates,anchors,names)
            source=next(t for t in case_tasks if t['start_role']==role and t['anchor_origin']==role)
            task=copy.deepcopy(source)
            task.update(kind='target',identity=f'{SID}::{case}::sphere_still::free_time_{role}',
                profiles=candidates,anchors=anchors,maximum_fit_calls=81,maximum_diagnostic_calls=3)
            targets.append(task)
    return dict(version=VERSION,tasks=targets,maximum_starts=6,maximum_optimizer_starts=4,
        maximum_native_evaluations=342,numerical_threads=4,retries=0)


def source_plan():return make_plan(parent.load(PARENT/'manifest.json'),parent.load(PARENT/'summary.json'))


def case_groups(results):
    targets=[r for r in results if r['kind']=='target'];groups={}
    expected={f'{SID}::{case}::sphere_still::free_time_{role}' for case in CASES for role in ('primary','repeat')}
    if len(targets)!=4 or {r['identity'] for r in targets}!=expected:
        raise ValueError('one distinct primary and repeat required for each processing case')
    for case in CASES:
        groups[case]=[next(r for r in targets if r['identity']==f'{SID}::{case}::sphere_still::free_time_{role}')
                      for role in ('primary','repeat')]
    return groups


def compare_cases(results,directory,base,assumption):
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_solver_position as position
    comparisons={}
    for case,rows in case_groups(results).items():
        comparison=dict(agreement_passed=False,both_full_fits_passed=all(r['converged'] for r in rows))
        if all(r.get('linearization_file') for r in rows):
            local=[]
            for row in rows:
                path=directory/row['linearization_file']
                if path.name!=row['linearization_file'] or parent.sha(path)!=row['linearization_sha256']:
                    raise ValueError('repeat artifact changed')
                with gzip.open(path,'rt') as stream:local.append(json.load(stream))
            gps=np.array(local[0]['gps']);times=np.array(local[0]['times_s'])
            blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            cov=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
            conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(cov))
            comparison.update(parent.repeat_metrics(*local,lambda d:position.physical_residual_step(conversion,d)))
        comparisons[case]=comparison
    return dict(cases=comparisons,agreement_passed=all(p['agreement_passed'] and p['both_full_fits_passed']
        for p in comparisons.values()),global_optimum_proven=False)


def executor_source(source):
    start=source.index("        group=[r for r in results if r['kind']=='target']")
    end=source.index('        verify(originals=False);calls=',start)
    source=source[:start]+'        repeat=compare_cases(results,OUTPUT,base,assumption)\n'+source[end:]
    edits=[('maximum_starts=4','maximum_starts=6',2),
           ('maximum_optimizer_starts=2','maximum_optimizer_starts=4',2),
           ('maximum_native_evaluations=174','maximum_native_evaluations=342',3),
           ("len(book.read('starts'))>4 or len(calls)>174","len(book.read('starts'))>6 or len(calls)>342",1),
           ('total=4','total=6',1),
           ("'test_ilvis0_profile_verification.py'","'test_ilvis0_profile_verification.py','test_ilvis0_remaining_free_time_worker.py'",1),
           ('# Profile-seeded free-time results','# Matched two-case free-time results',1),
           ('All five timing candidates were retained for each starting solution.',
            'Both verified timing anchors were retained for each starting solution in each processing case.',1),
           ('../ilvis0-interior-timing-profile-20261017/RESULTS.md','../ilvis0-remaining-time-profile-20261018/RESULTS.md',1),
           ("row.get('start_role','control')","row['identity']",1)]
    for old,new,count in edits:
        if source.count(old)!=count:raise ValueError('unrecognized frozen executor layout: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    executor=types.ModuleType('_ilvis0_remaining_free_time_executor')
    executor.__file__=str(Path(__file__).resolve())
    exec(compile(executor_source(TEMPLATE.read_text()),str(TEMPLATE),'exec'),executor.__dict__)
    executor.OUTPUT=OUTPUT;executor.GUIDE=GUIDE;executor.PARENT=PARENT;executor.ENDPOINTS=PARENT
    executor.CONTROLS=PARENT;executor.VERSION=VERSION;executor.QUALIFICATION=OUTPUT/'software-controls';executor.TESTS=35
    executor.make_plan=make_plan;executor.source_plan=source_plan;executor.compare_cases=compare_cases

    def sources():
        values=dict(parent.load(PARENT/'manifest.json')['sources'])
        for name in ('analysis/lll/ilvis0_profile_seeded.py','analysis/tests/ilvis0_profile_seeded_worker.py',
                     'analysis/tests/test_ilvis0_profile_seeded.py','analysis/tests/test_ilvis0_profile_seeded_worker.py',
                     'analysis/tests/test_ilvis0_profile_verification.py','analysis/tests/ilvis0_remaining_free_time_worker.py',
                     'analysis/tests/test_ilvis0_remaining_free_time_worker.py'):
            values[str(ROOT/name)]=parent.sha(ROOT/name)
        executor.prior.check_hashes(values);return values

    def prepare():
        OUTPUT.mkdir(exist_ok=True)
        if (OUTPUT/'manifest.json').exists():return executor.verify()
        executor.prior.sealed(PARENT,published=PARENT_GUIDE)
        qualification=executor.QUALIFICATION
        q=parent.load(qualification/'result.json');c=parent.load(qualification/'completion.json')
        if (not q['passed'] or q['tests']!=executor.TESTS
                or c['manifest_sha256']!=parent.sha(qualification/'manifest.json')
                or c['result_sha256']!=parent.sha(qualification/'result.json')):
            raise ValueError('software qualification failed')
        m=parent.load(PARENT/'manifest.json');plan=source_plan();values=sources()
        if values!=parent.load(qualification/'manifest.json')['sources']:raise ValueError('qualified sources changed')
        inputs=executor.prior.scientific_inputs(m['inputs'])
        for directory,names in ((PARENT,('manifest.json','summary.json','completion.json')),
                (PARENT_GUIDE,('evidence-receipt.json',)),(GUIDE,('PLAN.md',)),
                (qualification,('manifest.json','result.json','completion.json','tests.xml'))):
            for name in names:inputs[str(directory/name)]=parent.sha(directory/name)
        originals={}
        for task in plan['tasks']:
            path=task['task']['selected']['source_path'];originals[path]=m['originals'][path]
            for row in task.get('profiles',[]):inputs[row['evidence_file']]=row['evidence_sha256']
        executor.prior.check_hashes(inputs);executor.prior.check_hashes(originals)
        e=executor.prior.engine();_,extended=e.arithmetic.load_tangent(OUTPUT/'kernel')
        if extended!=m['extended_kernel']:raise ValueError('native integration changed')
        executor.prior.snapshot(OUTPUT,values)
        shutil.copyfile(OUTPUT/'kernel'/extended['source_file'],OUTPUT/'source-freeze'/extended['source_file'])
        parent.write(OUTPUT/'manifest.json',dict(version=VERSION,plan=plan,sources=values,inputs=inputs,originals=originals,
            environment=e.base.runtime.numerical_environment(),extended_kernel=extended,ordinary_value_kernel=m['ordinary_value_kernel'],
            scientific_decision='abstain',original_labels_changed=False))
        parent.write(OUTPUT/'authorization.json',executor.allowance());return executor.verify()

    executor.sources=sources;executor.prepare=prepare
    return executor


if __name__=='__main__':build_executor().main()
