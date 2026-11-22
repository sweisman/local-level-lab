# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search the ESA forecast contrast with one linked physical calibration."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_attitude_cover_score import INCREASE


ID = 'esa-linked-physical-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_PHYSICAL_SCORE_PLAN.md'
SCOPE = 'Bounded linked-calibration point search for the archived ESA shape score'
REPLAY_SHA = 'bd8331b8164bb0e8c9910b2037edcdb725d719f35decd15c2288a6177bbe26a6'
MODELS = ('sphere_still','flat_still')
SEEDS = ('nominal','linked_witness','relaxed_replay')
GAMMAS = (0.,.1)
ITERATIONS = 160
EVALUATIONS = 480
FRACTIONS = (1.,.999,.98,.8)
CHECKS = 2+2*len(FRACTIONS)


def tasks():
    return [dict(identity=f'{model}-{index}-{seed}',input_key=model,
                 payload=dict(model=model,seed=seed,gamma=gamma),
                 limits=dict(native_calls=0,packet_visits=0,bound_calls=1,
                             bound_steps=EVALUATIONS+CHECKS))
            for model in MODELS for index,gamma in enumerate(GAMMAS) for seed in SEEDS]


def evaluate(task, context):
    import numpy as np
    from .esa_calibration_witness import check_point
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_map import restore_static_reference
    from .ilvis0_coupled_map_controls import analytic_jacobian
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_physical_score import propose

    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if context.manifest['scope']!=SCOPE or declared not in tasks():
        raise ValueError('exact linked physical task required')
    model,seed,gamma = (task['payload'][k] for k in ('model','seed','gamma'))

    def read(suffix):
        return json.loads(context.input_path(model+suffix).read_bytes())

    residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context,model)
    force, sample = read('-force'),read('-first-sample')
    reference = restore_static_reference(force['configuration'],sample['dv'],sample['dt'],
        lower=force['lower'],upper=force['upper'],center=force['center'],expected_report=read('-reference'))
    seeds = read('-seeds')
    if list(sorted(seeds))!=list(sorted(SEEDS)) or seeds['nominal']!=force['center']:
        raise ValueError('three unchanged deterministic starts required')
    center = reference.parent.center
    objective = np.array([float((a+b)/2) for a,b in target])
    radius = sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))+gamma
    context.charge(bound_calls=1,bound_steps=EVALUATIONS+CHECKS)
    result = propose(design,residual,objective,center,reference.parent.lower,reference.parent.upper,seeds[seed],
        values=reference.normalized_values_at,derivative=lambda x:analytic_jacobian(reference,x),
        radius=radius,iterations=ITERATIONS,evaluations=EVALUATIONS)
    checks = []

    def verify(label, x, fraction):
        x = np.clip(center+fraction*(np.asarray(x)-center),reference.parent.lower,reference.parent.upper)
        values = reference.normalized_values_at(x)
        if np.any(abs(values)>1.) or not np.isfinite(values).all():
            raise ValueError('linked values left the original common-coefficient box')
        step = [F(v)-F(c) for v,c in zip(x,center,strict=True)]
        measured = check_point(earlier,raw,residual,target,[*step,*values],unshared=gamma)
        checks.append(dict(label=label,fraction=fraction,point=x.tolist(),**measured))

    verify('nominal',center,1.)
    verify('seed',seeds[seed],1.)
    for label in ('point','best_approximate'):
        if result[label] is not None:
            for fraction in FRACTIONS:
                verify(label,result[label],fraction)
    if len(checks)>CHECKS or not checks[0]['loss_passed']:
        raise ValueError('nominal anchor and finite checked point count required')
    best = max((row for row in checks if row['loss_passed']),key=lambda row:row['score_lower'])
    record = dict(model=model,seed=seed,earlier_unshared=gamma,best=best,
        checked_points=len(checks),nominal_separation=settings['shape']['nominal'],
        success=result['success'],status=result['status'],evaluations=result['evaluations'])
    context.save('linked-points.json',dict(record,checks=checks))
    return dict(record,passed=True,fit_starts=0,later_observations_used=0,scientific_decision='abstain')


def prepare(root):
    from .esa_attitude_physical_check import RESULT, SOURCE_SHA
    from .esa_attitude_refinement_score import ID as REFINEMENT
    from .esa_attitude_survivor_score import ID as SURVIVOR
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing linked physical freeze')
    raw_replay = (root/RESULT).read_bytes()
    if digest(raw_replay)!=REPLAY_SHA:
        raise ValueError('unchanged saved high-scoring physical replay required')
    replay = json.loads(raw_replay)
    staged = {'replay.json':raw_replay}
    with ExitStack() as stack:
        prior = stack.enter_context(closing(ClosedStudy(root,'data/'+SURVIVOR)))
        reference = stack.enter_context(closing(ClosedStudy(root,'data/'+REFINEMENT,store=prior.store)))
        if (prior.completion['manifest_sha256']!=SOURCE_SHA or replay['manifest_sha256']!=SOURCE_SHA
                or reference.completion['manifest_sha256']!=prior.input('cover')['manifest_sha256']):
            raise ValueError('exact archived score and calibration references required')
        staged['later-operator.npz'] = prior.input('later-operator',raw=True)
        for model in MODELS:
            for suffix, ext in (('', '.npz'), ('-weights','.npz'), ('-settings','.json')):
                staged[model+suffix+ext] = prior.input(model+suffix,raw=True)
            for suffix in ('-force','-first-sample','-reference'):
                staged[model+suffix+'.json'] = reference.input(model+suffix,raw=True)
            witnesses = reference.input(model+'-witnesses')['rows']
            best = max((r for r in witnesses if r['variant']=='linked_shared' and r['loss_passed']),
                       key=lambda r:r['score_lower'])
            prior_point = next(r['physical_point'] for r in replay['rows'] if r['identity'].startswith(model+'-'))
            staged[model+'-seeds.json'] = encoded(dict(nominal=reference.input(model+'-force')['center'],
                linked_witness=best['physical_point'],relaxed_replay=prior_point))
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name,payload in staged.items():
        path = base/name
        atomic(path,payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID,adapter=adapter,sources=source_closure(root,[adapter,PLAN]),
        inputs=inputs,tasks=tasks(),scope=SCOPE,workers=4,threads=1,maximum_wall_s=120.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
