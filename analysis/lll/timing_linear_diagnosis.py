# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-baseline linear diagnostics; never reconstruct an unsaved anchor."""
import math
import sys

IDENTITY='timing-linear-anchor-check-20261027'
PARENT='docs/prediction-calibration-timing'
PLAN='docs/TIMING_LINEAR_ANCHOR_PLAN.md'
SCOPE='four matched saved linear checks with feasible initialization; no native calculations or nonlinear fits'
PARENT_MANIFEST='c790afcb47fd0d142ebb2006c0ff5e182458f7993eaef7a466c34a971947cb42'
PARENT_SUMMARY='1214749f96e6cd274670be1b636700878dd4f11d92cf82da18e10fac68a0d83e'


def baseline_matrix(fit,*,identity,fit_sha256):
    names=fit['active_parameters'];u=fit['normalized_parameters']
    r=fit['local_linearization']['residual'];j=fit['local_linearization']['jacobian'];n=len(names)
    if (fit['version']!='ilvis0-timing-cell-verification-v1' or n not in (26,27)
            or len(set(names))!=n or names.count('time_offset')!=1 or len(u)!=n
            or not 1<=len(r)<=3600 or len(j)!=len(r) or any(len(a)!=n for a in j)
            or any(not math.isfinite(x) for a in [u,r,*j] for x in a)
            or any(abs(x)>1 for x in u) or type(fit['converged']) is not bool
            or not isinstance(identity,str) or not identity or len(fit_sha256)!=64
            or any(c not in '0123456789abcdef' for c in fit_sha256)
            or not math.isclose(math.fsum(x*x for x in r),fit['residual_sum_squares'],rel_tol=1e-12,abs_tol=1e-12)
            or len(fit['timing_geometry'])!=1):
        raise ValueError('complete finite saved baseline and original fit binding required')
    column=names.index('time_offset');cells=fit['timing_geometry'][0]['cells']
    if not 1<=len(cells)<=17:raise ValueError('complete bounded timing geometry required')
    if any(not math.isfinite(v) for c in cells for v in (c['lower'],c['upper'])):
        raise ValueError('finite timing cells required')
    containing=[(i,c) for i,c in enumerate(cells) if -1<=c['lower']<=u[column]<=c['upper']<=1]
    if len(containing)!=1:raise ValueError('one unambiguous cell containing unchanged baseline required')
    index,cell=containing[0];lo=[-1.]*n;hi=[1.]*n
    lo[column]=cell['lower'];hi[column]=cell['upper']
    return dict(identity=identity,source_fit_sha256=fit_sha256,active=list(names),point=list(u),
        residual=list(r),jacobian=[list(a) for a in j],lower=lo,upper=hi,cell_index=index,
        original_fit_converged=fit['converged'],exact_saved_cell_anchor_replay=False)


def audit_proposal(matrix,proposal):
    n=len(matrix['active']);point=proposal['point'];u=matrix['point']
    if (len(point)!=n or proposal['active_parameters']!=matrix['active']
            or len(u)!=n or len(matrix['lower'])!=n or len(matrix['upper'])!=n
            or any(not math.isfinite(v) or not lo<=v<=hi
                   for v,lo,hi in zip(u,matrix['lower'],matrix['upper']))
            or any(not math.isfinite(x) or x<lo or x>hi
                   for x,lo,hi in zip(point,matrix['lower'],matrix['upper']))
            or proposal['linear_solves']!=1 or proposal['native_calls'] or proposal['nonlinear_fit_starts']):
        raise ValueError('complete feasible unchanged-column linear proposal required')
    residual=[r+math.fsum(a*(x-v) for a,x,v in zip(row,point,u))
              for row,r in zip(matrix['jacobian'],matrix['residual'])]
    cost=math.fsum(x*x for x in residual);anchor=math.fsum(x*x for x in matrix['residual'])
    if (len(proposal['predicted_residual'])!=len(residual)
            or any(not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
                   for a,b in zip(residual,proposal['predicted_residual']))
            or not math.isclose(cost,proposal['predicted_cost'],rel_tol=1e-12,abs_tol=1e-12)
            or not math.isclose(anchor,proposal['anchor_cost'],rel_tol=1e-12,abs_tol=1e-12)):
        raise ValueError('proposal differs from independent scalar arithmetic')
    allowance=64*sys.float_info.epsilon*max(1.,anchor,cost)
    return dict(identity=matrix['identity'],source_fit_sha256=matrix['source_fit_sha256'],
        columns=n,cell_index=matrix['cell_index'],linear_success=proposal['linear_success'],
        anchor_cost=anchor,predicted_cost=cost,cost_increase=cost-anchor,roundoff_allowance=allowance,
        nonworsening=cost<=anchor+allowance,zero_step_feasible=True,
        original_fit_converged=matrix['original_fit_converged'],labels_changed=False,
        exact_saved_cell_anchor_replay=False,native_calls=0,nonlinear_fit_starts=0,
        scientific_decision='abstain')


def evaluate_matrix(matrix,*,reserve):
    from lll.timing_cells import bounded_step
    p=bounded_step(matrix['residual'],matrix['jacobian'],matrix['point'],matrix['lower'],matrix['upper'],
                   active=matrix['active'],reserve=reserve)
    return dict(proposal=p,audit=audit_proposal(matrix,p))


def choose_identities(rows):
    seed=281474977210667;groups={}
    for r in rows:
        if (r['law'],r['model'],r['profile'])!=('increment','sphere_rotating',False):continue
        if r['draw_seed']>seed:continue
        group=groups.setdefault(r['draw_seed'],{})
        if r['start'] in group:raise ValueError('duplicate prescribed start')
        group[r['start']]=r
    failed=groups.get(seed,{})
    if set(failed)!={0,1} or any(not r['complete'] or r['converged'] for r in failed.values()):
        raise ValueError('both original complete failed starts required')
    controls=[s for s,g in groups.items() if s<seed and set(g)=={0,1}
              and all(r['complete'] and r['converged'] for r in g.values())]
    if not controls:raise ValueError('prior matched complete control pair required')
    return [groups[s][k]['identity'] for s in (max(controls),seed) for k in (0,1)]


def configuration():
    return dict(id=IDENTITY,scope=SCOPE,records=4,maximum_linear_solves=4,
        workers=1,threads=1,maximum_wall_s=600.,native_calls=0,nonlinear_fit_starts=0,
        exact_saved_cell_anchor_replay=False)


def selection(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    s=ClosedStudy(root,PARENT)
    try:
        if (s.completion['manifest_sha256']!=PARENT_MANIFEST
                or s.completion['summary_sha256']!=PARENT_SUMMARY):
            raise ValueError('exact closed calibration required')
        name='artifacts/publication/verified-report.json';receipt=s.read('evidence-receipt.json')
        report=s.read(name,receipt['artifacts'][name]);ids=choose_identities(report['rows']);rows=[]
        for identity in ids:
            raw=s.artifact(identity,'fit.json',raw=True)
            import json
            rows.append(baseline_matrix(json.loads(raw),identity=identity,fit_sha256=digest(raw)))
        return dict(rows=rows,sha256=digest(encoded(rows)),parent_completion=s.completion)
    finally:s.close()


def tasks(selected):
    from lll.studies.artifacts import digest,encoded
    if len(selected['rows'])!=4:raise ValueError('four fixed saved baselines required')
    return [dict(identity=r['identity'],input_key='selection',native_kind='tangent',
        payload=dict(matrix_sha256=digest(encoded(r))),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)) for r in selected['rows']]


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/timing_linear_diagnosis.py',
        'analysis/tests/test_timing_linear_diagnosis.py','analysis/tests/test_timing_cells.py',
        'analysis/tests/test_timing_cells_known_optimum.py',PLAN])


def _qualified(root,path):
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    return checked(root,path,sources=sources(root),environment=environment(),minimum_tests=52,
        required_tests=['test_audit_requires_a_feasible_zero_step_benchmark',
            'test_exhausted_allowance_prevents_the_linear_calculation',
            'test_adapter_result_passes_shared_finish_schema_without_repeating_a_study',
            'test_cell_step_moves_from_nonoptimal_anchor_with_all_26_columns',
            'test_cell_step_rejects_worsening_even_when_solver_claims_success',
            'test_selects_both_failed_starts_and_nearest_prior_complete_pair_without_future_scores'])


def prepare(root,*,qualification):
    from pathlib import Path
    from lll.studies.artifacts import atomic,encoded
    from lll.studies.runtime import Definition
    from lll.airquantumgrav_inventory import environment
    root=Path(root).resolve();request,tests=_qualified(root,qualification)
    selected=selection(root);base=root/'data/ilvis0-source-point-development'/f'{IDENTITY}-inputs'
    if base.exists() or (root/'data'/IDENTITY).exists():raise ValueError('fresh finite diagnosis required')
    base.mkdir(parents=True);inputs={}
    values=dict(selection=encoded(selected),configuration=encoded(configuration()),environment=encoded(environment()),
                **{'qualification-request':request,'qualification-report':tests})
    for i,(key,raw) in enumerate(values.items()):
        p=base/f'input-{i:03d}';atomic(p,raw);inputs[key]=str(p.relative_to(root))
    definition=dict(id=IDENTITY,scope=SCOPE,adapter='analysis/lll/timing_linear_diagnosis.py',
        sources=sources(root),inputs=inputs,tasks=tasks(selected),workers=1,threads=1,maximum_wall_s=600.)
    atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+IDENTITY,allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(work,context):
    import json
    from lll.studies.artifacts import digest,encoded
    from lll.studies.source_binding import verify
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.airquantumgrav_inventory import environment
    selected=json.loads(context.input_path('selection').read_bytes())
    declared=json.loads(context.input_path('qualification-request').read_bytes())['sources']
    verify(context.root/'source-freeze',declared=declared,manifest=context.manifest['sources'])
    identity=work['identity'];expected={t['identity']:t for t in tasks(selected)}
    if (context.manifest['scope']!=SCOPE or digest(encoded(selected['rows']))!=selected['sha256']
            or json.loads(context.input_path('configuration').read_bytes())!=configuration()
            or json.loads(context.input_path('environment').read_bytes())!=environment()
            or {k:v for k,v in work.items() if k not in ('index','shard')}!=expected.get(identity)):
        raise ValueError('unchanged finite baseline diagnosis required')
    matrix=next(r for r in selected['rows'] if r['identity']==identity)
    journal=Journal(context.directory/'linear-solves.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={identity:dict(linear_solves=1)})
    journal.start(identity)
    def reserve():
        _check_continue(context.root,context.manifest);journal.reserve(identity,'linear_solves')
    try:
        out=evaluate_matrix(matrix,reserve=reserve);context.save('diagnosis.json',out);journal.verify()
        if journal.count(identity,'linear_solves')!=1:raise ValueError('linear charge differs')
        return dict(passed=bool(out['proposal']['linear_success'] and out['audit']['nonworsening']),
            diagnosis_complete=True,nonworsening=out['audit']['nonworsening'],
            linear_solves=1,native_calls=0,nonlinear_fit_starts=0,labels_changed=False,
            scientific_decision='abstain')
    finally:context.note_file(journal.path)
