# SPDX-License-Identifier: AGPL-3.0-or-later
"""One finite saved-matrix review, using shared lifecycle and bounded algebra."""
import json
from pathlib import Path

IDENTITY='saved-timing-cell-proposals-20261027'
PARENT='docs/saved-timing-boundary'
PARENT_MANIFEST='0db90ad32975bd2636090c8dd810db1f4bf7f484199bb831ba8fce53c036225d'
PARENT_SUMMARY='7d9890d4a1384ca80bab3cafbc8582622ae70161f01e223dda9377de97090990'
PLAN='docs/TIMING_CELL_STEP_PLAN.md'
SCOPE='eighteen existing timing-branch linear proposals; no native calculations, forecasts or nonlinear fits'


def configuration():
    return dict(id=IDENTITY,scope=SCOPE,maximum_linear_solves=18,maximum_iterations=100,tolerance=1e-10,
                workers=1,threads=1,maximum_wall_s=600.,rate_hz=300)


def task(matrix_sha256):
    return dict(identity='all-saved-branches',input_key='matrices',native_kind='tangent',
        payload=dict(matrix_sha256=matrix_sha256),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))


def matrices(record,d,*,diagnostic_sha256):
    import numpy as np
    from lll.studies.artifacts import digest
    active=record['fit']['active_parameters'];scale=record['timing_scale'];rate=configuration()['rate_hz']
    if (len(active)!=27 or len(set(active))!=27 or d['active_parameters']!=active or d['columns']!=27
            or d['source_fit_sha256']!=record['artifact_sha256']['fit.json']
            or d['labels_changed'] or d['nonlinear_fit_starts'] or not np.isfinite(scale) or scale<=0):
        raise ValueError('unchanged full-column saved diagnostic required')
    column=active.index('time_offset');center=d['center']['normalized_time_offset']
    binding=record['artifacts']['input-binding.json'];n=binding['native_packets']
    if type(n) is not int or not 1<=n<=2000000:raise ValueError('bounded saved clock required')
    dt=np.diff(np.arange(n+1)/rate).astype('<f8')
    if digest(dt.tobytes())!=binding['full_array_sha256']['dt']:
        raise ValueError('uniform clock differs from its saved hash')
    times=np.asarray(record['artifacts']['training-observations.json']['times_s'],float)
    phase=(times+center*scale)*rate
    if (times.ndim!=1 or not len(times) or not np.all(np.isfinite(phase))
            or np.any(abs(phase-np.rint(phase))>128*np.finfo(float).eps*np.maximum(1.,abs(phase)))):
        raise ValueError('receiver queries do not share the declared integration boundary')
    expected=[(h,side) for h in (1e-5,1e-6,1e-7) for side in (-1,1)]
    if [(v['spacing_s'],v['side']) for v in d['branches']]!=expected:
        raise ValueError('every original spacing and side required')
    rows=[]
    for index,b in enumerate(d['branches']):
        side=b['side'];h=b['spacing_s']/scale;point=np.asarray(b['point'],float)
        if point.shape!=(27,) or not np.all(np.isfinite(point)):raise ValueError('full finite anchor required')
        feasible=bool(-1<=point[column]-h/4 and point[column]+h/4<=1)
        if b['feasible'] is not feasible:raise ValueError('saved feasibility differs from physical bounds')
        if not feasible:continue
        lower=-np.ones(27);upper=np.ones(27);period=1/(rate*scale)
        lower[column]=max(-1.,center-period if side<0 else center)
        upper[column]=min(1.,center if side<0 else center+period)
        if (np.any(lower>=upper) or np.any(point<lower) or np.any(point>upper)
                or abs(point[column]-(center+side*h))>1e-12):
            raise ValueError('anchor or proposed cell violates the original physical box')
        r=np.asarray(b['residual'],float);j=np.asarray(b['jacobian'],float)
        if r.ndim!=1 or not len(r) or j.shape!=(len(r),27) or not np.all(np.isfinite(j)) or not np.all(np.isfinite(r)):
            raise ValueError('complete finite residual and all Jacobian columns required')
        rows.append(dict(identity=record['identity'],branch_index=index,side=side,spacing_s=b['spacing_s'],
            original_fit_converged=record['saved_converged'],original_cost=record['fit']['residual_sum_squares'],
            source_fit_sha256=record['artifact_sha256']['fit.json'],source_diagnostic_sha256=diagnostic_sha256,
            active=list(active),point=point.tolist(),lower=lower.tolist(),upper=upper.tolist(),
            residual=r.tolist(),jacobian=j.tolist(),time_offset_scale=scale))
    return rows


def selection(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    s=ClosedStudy(root,PARENT)
    try:
        if (s.completion['manifest_sha256']!=PARENT_MANIFEST or s.completion['summary_sha256']!=PARENT_SUMMARY
                or s.summary['completed']!=4 or len(s.tasks)!=4):
            raise ValueError('exact closed four-point timing diagnostic required')
        rows=[]
        for point in s.input('points'):
            identity=point['identity'];d=s.artifact(identity,'diagnostic.json')
            sha=s.envelope(identity)['artifacts']['artifacts/'+identity+'/diagnostic.json']
            rows.extend(matrices(point,d,diagnostic_sha256=sha))
        if len(rows)!=18:raise ValueError('all eighteen feasible saved branch matrices required')
        return dict(rows=rows,sha256=digest(encoded(rows)),parent_completion=s.completion)
    finally:s.close()


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/timing_cells.py','analysis/lll/timing_cell_study.py',
        'analysis/lll/timing_cell_report.py','analysis/tests/test_timing_cells.py',
        'analysis/tests/test_timing_cell_study.py','analysis/tests/test_timing_cell_report.py',PLAN])


def prepare(root,*,qualification):
    if qualification is None:raise ValueError('source-bound step qualification required')
    from lll.studies.artifacts import atomic,encoded
    from lll.studies.runtime import Definition
    from lll.studies.qualification import checked
    from lll.studies.closed import ClosedStudy
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();env=environment()
    request,tests=checked(root,qualification,sources=sources(root),environment=env,minimum_tests=20,
        required_tests=['test_cell_step_matches_independent_face_enumeration[a0-b0]',
            'test_cell_step_recovers_kink_minimum_from_both_sides_without_crossing',
            'test_cell_step_retains_all_27_columns_in_rank_deficient_problem',
            'test_cell_step_charges_before_solve_and_honors_exhaustion'])
    parent=ClosedStudy(root,PARENT)
    try:
        if parent.input('environment')!=env:raise ValueError('parent numerical environment changed')
    finally:parent.close()
    selected=selection(root);cfg=configuration();base=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if base.exists() or (root/'data'/IDENTITY).exists():raise ValueError('fresh finite matrix review required')
    base.mkdir(parents=True);inputs={}
    values=dict(matrices=encoded(selected),configuration=encoded(cfg),environment=encoded(env),
                **{'qualification-request':request,'qualification-report':tests})
    for index,(name,raw) in enumerate(values.items()):
        path=base/f'input-{index:03d}';atomic(path,raw);inputs[name]=str(path.relative_to(root))
    definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/timing_cell_study.py',sources=sources(root),
        inputs=inputs,tasks=[task(selected['sha256'])],workers=1,threads=1,maximum_wall_s=600.)
    atomic(base/'definition.json',encoded(definition));m=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+IDENTITY,allocation=m['allocation'],limits=m['limits'])


def evaluate(work,context):
    if context.manifest['scope']!=SCOPE:raise ValueError('exact saved matrix review scope required')
    from lll.studies.artifacts import digest,encoded
    from lll.studies.source_binding import verify
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.airquantumgrav_inventory import environment
    from lll.timing_cells import bounded_step
    cfg=json.loads(context.input_path('configuration').read_bytes());env=json.loads(context.input_path('environment').read_bytes())
    selected=json.loads(context.input_path('matrices').read_bytes());declared=json.loads(context.input_path('qualification-request').read_bytes())['sources']
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    if (cfg!=configuration() or env!=environment() or digest(encoded(selected['rows']))!=selected['sha256']
            or {k:v for k,v in work.items() if k not in ('index','shard')}!=task(selected['sha256'])
            or len(selected['rows'])!=18):raise ValueError('unchanged finite matrices, environment and task required')
    identity=work['identity'];journal=Journal(context.directory/'linear-solves.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={identity:dict(linear_solves=18)});journal.start(identity)
    results=[]
    def reserve():
        _check_continue(context.root,context.manifest);journal.reserve(identity,'linear_solves')
    try:
        for index,matrix in enumerate(selected['rows']):
            _check_continue(context.root,context.manifest)
            result=bounded_step(matrix['residual'],matrix['jacobian'],matrix['point'],matrix['lower'],matrix['upper'],
                active=matrix['active'],reserve=reserve)
            row=dict(index=index,matrix_sha256=digest(encoded(matrix)),proposal=result)
            context.save(f'proposal-{index:03d}.json',row);results.append(row)
        journal.verify()
        if journal.count(identity,'linear_solves')!=18:raise ValueError('linear solve charges differ')
        context.save('proposals.json',results)
        return dict(passed=all(v['proposal']['linear_success'] for v in results),completed_proposals=len(results),
            linear_solves=18,nonlinear_fit_starts=0,native_calls=0,labels_changed=False,scientific_decision='abstain')
    finally:context.note_file(journal.path)
