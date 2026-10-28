# SPDX-License-Identifier: AGPL-3.0-or-later
"""All saved timing-cell proposals through shared finite physical reconstruction."""
import json
from pathlib import Path

IDENTITY='saved-timing-cell-native-20261027'
PARENT='docs/saved-timing-boundary'
PROPOSALS='docs/saved-timing-cell-proposals'
PROPOSAL_MANIFEST='a14ad653e8de9d172f96d90def1a3f14d7a40bac027f17856d375bd84dc39d06'
PROPOSAL_SUMMARY='48811676da7b7fd8d50fb7b66b0e4e992259e8f1b0af4c43a452160b2b3f1408'
PLAN='docs/TIMING_CELL_NATIVE_PLAN.md'
SCOPE='all eighteen saved timing-cell proposals at four exposed points; physical evaluation only, no fits or forecasts'


def identities():
    from lll.timing_boundary_study import identities as old
    return old()


def configuration():
    return dict(id=IDENTITY,scope=SCOPE,workers=4,threads=1,maximum_evaluations=8,
        maximum_wall_s=3600.,nonlinear_fit_starts=0,expected_proposals=18,expected_evaluations=26)


def work_allowance(seed):
    from lll.timing_boundary_study import SEEDS
    from lll.compensated_prediction_release import case_recipe
    from lll.saved_point_runtime import allowance
    if type(seed) is not int or seed not in SEEDS:raise ValueError('existing exposed seed required')
    return allowance(case_recipe(seed),8)


def parent_changes(parent,current):
    allowed={'analysis/lll/stopping_consistency_study.py','analysis/lll/timing_arithmetic_study.py',
        'analysis/lll/timing_boundary_study.py','analysis/lll/timing_boundary_report.py',
        'analysis/tests/test_timing_boundary_report.py'}
    changes={k:dict(original_sha256=v,current_sha256=current.get(k)) for k,v in parent.items() if current.get(k)!=v}
    if not set(changes)<=allowed:raise ValueError('physical, noise or other frozen source changed')
    return changes


def bind_proposals(points,selected,proposals):
    import numpy as np
    from lll.studies.artifacts import digest,encoded
    if ([p['identity'] for p in points]!=identities() or len(selected['rows'])!=18 or len(proposals)!=18
            or selected['sha256']!=digest(encoded(selected['rows']))
            or [p['index'] for p in proposals]!=list(range(18))):
        raise ValueError('exact four points and all eighteen ordered proposals required')
    grouped={p['identity']:[] for p in points};lookup={p['identity']:p for p in points}
    for matrix,result in zip(selected['rows'],proposals):
        if matrix['identity'] not in lookup:raise ValueError('unselected proposal identity')
        record=lookup[matrix['identity']];proposal=result['proposal'];p=np.asarray(proposal['point'],float)
        lo,hi=(np.asarray(matrix[k],float) for k in ('lower','upper'))
        if (result['matrix_sha256']!=digest(encoded(matrix)) or proposal['linear_success'] is not True
                or matrix['source_fit_sha256']!=record['artifact_sha256']['fit.json']
                or matrix['active']!=record['fit']['active_parameters'] or len(matrix['active'])!=27
                or any(v.shape!=(27,) or not np.all(np.isfinite(v)) for v in (p,lo,hi))
                or np.any(lo>=hi) or np.any(lo< -1) or np.any(hi>1) or np.any(p<lo) or np.any(p>hi)):
            raise ValueError('source-bound complete feasible proposal required')
        grouped[record['identity']].append(dict(index=result['index'],matrix_sha256=result['matrix_sha256'],
            active=matrix['active'],point=p.tolist(),lower=lo.tolist(),upper=hi.tolist(),
            predicted_cost=proposal['predicted_cost'],predicted_residual=proposal['predicted_residual'],
            branch_index=matrix['branch_index'],side=matrix['side'],spacing_s=matrix['spacing_s']))
    if [len(grouped[k]) for k in identities()]!=[3,3,6,6]:raise ValueError('every feasible side and spacing required')
    result=[]
    for point in points:
        value=dict(point,proposals=grouped[point['identity']]);value['parent_selection_sha256']=value.pop('selection_sha256')
        value['selection_sha256']=digest(encoded(value));result.append(value)
    return result


def selection(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    from lll.timing_cell_study import PARENT_MANIFEST,PARENT_SUMMARY,matrices
    s=ClosedStudy(root,PARENT)
    try:
        if (s.completion['manifest_sha256']!=PARENT_MANIFEST or s.completion['summary_sha256']!=PARENT_SUMMARY
                or s.summary['completed']!=4):raise ValueError('original complete four-point diagnostic required')
        points=s.input('points');rows=[]
        for record in points:
            identity=record['identity'];d=s.artifact(identity,'diagnostic.json')
            sha=s.envelope(identity)['artifacts']['artifacts/'+identity+'/diagnostic.json']
            rows.extend(matrices(record,d,diagnostic_sha256=sha))
        p=ClosedStudy(root,PROPOSALS,store=s.store)
        try:
            if (p.completion['manifest_sha256']!=PROPOSAL_MANIFEST or p.completion['summary_sha256']!=PROPOSAL_SUMMARY
                    or p.summary['completed']!=1):raise ValueError('exact complete saved proposal study required')
            selected=p.input('matrices')
            if encoded(rows)!=encoded(selected['rows']):raise ValueError('proposal anchors differ from original branches')
            proposals=p.artifact('all-saved-branches','proposals.json')
            return bind_proposals(points,selected,proposals)
        finally:p.close()
    finally:s.close()


def sources(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    s=ClosedStudy(root,PARENT)
    try:old=set(s.manifest['sources'])
    finally:s.close()
    own=['analysis/lll/timing_cell_native_study.py','analysis/lll/timing_cell_native_probe.py',
        'analysis/lll/timing_cell_native_report.py','analysis/tests/test_timing_cell_native_study.py',
        'analysis/tests/test_timing_cell_native_probe.py','analysis/tests/test_timing_cell_native_report.py',
        'analysis/tests/test_saved_point_runtime.py',PLAN]
    return sorted(old|set(source_closure(root,own)))


def prepare(root,*,qualification):
    if qualification is None:raise ValueError('source-bound software qualification required')
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded,atomic
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();env=environment();names=sources(root)
    request,tests=checked(root,qualification,sources=names,environment=env,minimum_tests=50,
        required_tests=['test_native_proposals_charge_before_every_call_keep_columns_and_convert_actual_difference',
            'test_native_proposals_cooperative_stop_precedes_charge_and_evaluation',
            'test_native_cell_selection_includes_all_eighteen_without_best_spacing_selection',
            'test_capture_binding_exits_before_any_fit_or_forecast'])
    s=ClosedStudy(root,PARENT)
    try:
        if s.input('environment')!=env:raise ValueError('original numerical environment changed')
        changes=parent_changes(s.manifest['sources'],{n:digest((root/n).read_bytes()) for n in names})
    finally:s.close()
    points=selection(root);base=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if base.exists() or (root/'data'/IDENTITY).exists():raise ValueError('fresh finite diagnostic required')
    base.mkdir(parents=True);inputs={}
    values=dict(points=encoded(points),configuration=encoded(configuration()),environment=encoded(env),
        **{'qualification-request':request,'qualification-report':tests,'parent-source-updates':encoded(changes)})
    for i,(name,raw) in enumerate(values.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    tasks=[dict(identity=p['identity'],input_key='points',native_kind='tangent',
        payload=dict(point_index=i,selection_sha256=p['selection_sha256']),
        limits=work_allowance(p['payload']['draw_seed'])) for i,p in enumerate(points)]
    definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/timing_cell_native_study.py',sources=names,
        inputs=inputs,tasks=tasks,workers=4,threads=1,maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+IDENTITY,allocation=m['allocation'],limits=m['limits'])


def evaluate(task,context):
    if context.manifest['scope']!=SCOPE:raise ValueError('exact physical proposal scope required')
    from lll.studies.artifacts import digest,encoded
    from lll.studies.source_binding import verify
    from lll.airquantumgrav_inventory import environment
    from lll.compensated_prediction_release import case_recipe
    from lll.saved_point_runtime import run_point
    from lll.timing_cell_native_probe import probe
    cfg=json.loads(context.input_path('configuration').read_bytes());env=json.loads(context.input_path('environment').read_bytes())
    declared=json.loads(context.input_path('qualification-request').read_bytes())['sources']
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    if cfg!=configuration() or env!=environment():raise ValueError('frozen configuration and environment required')
    points=json.loads(context.input_path('points').read_bytes());index=task['payload']['point_index']
    if type(index) is not int or not 0<=index<4 or len(points)!=4:raise ValueError('existing selected point required')
    record=points[index];raw=dict(record);sha=raw.pop('selection_sha256');seed=record['payload']['draw_seed']
    if (record['identity']!=identities()[index] or task['identity']!=record['identity']
            or digest(encoded(raw))!=sha or task['payload']['selection_sha256']!=sha
            or task['limits']!=work_allowance(seed) or len(record['proposals'])!=(3 if index<2 else 6)):
        raise ValueError('unchanged full proposal coverage and separate allowance required')
    def provider(evaluate,point,**options):
        return probe(evaluate,point,active=record['fit']['active_parameters'],proposals=record['proposals'],
            expected_cost=record['fit']['residual_sum_squares'],expected_linearization=record['fit']['local_linearization'],
            bounds=options['bounds'],physical_step=options['physical_step'],reserve=options['reserve'],
            check_continue=options['check_continue'],maximum_evaluations=8)
    return run_point(task,context,record,case_recipe(seed),maximum_evaluations=8,provider=provider,
        provider_source='analysis/lll/timing_cell_native_study.py',physical_conversion=True)
