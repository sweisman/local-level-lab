# SPDX-License-Identifier: AGPL-3.0-or-later
"""Direct support and feasible points for the saved ESA static relaxation."""

from contextlib import closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_coupled_training_score import GAMMAS, MODELS
from .esa_linked_training_support import INCREASE


ID = 'esa-direct-training-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_DIRECT_TRAINING_SCORE_PLAN.md'
SCOPE = 'Direct support of the full earlier-loss and static relaxation on ESA 187'
PARENT_SHA = '3feadcd8f288ed55d23880d476fe967a1a6a4e2c65210aa932ee7e8b8c5cab46'
ITERATIONS = 200
FRACTIONS = (1., .999, .95)
STARTS = ('zero', 'linked_witness')
STEPS = 3+len(FRACTIONS)


def tasks():
    count = len(GAMMAS)*len(STARTS)
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=count,
                             bound_steps=count*STEPS)) for model in MODELS]


def feasible_box_and_cuts(point, lower, upper, static, limits):
    if any(not F(lo)<=x<=F(hi) for lo, x, hi in zip(lower, point, upper, strict=True)):
        return False
    return all(sum(F(v)*x for v,x in zip(row, point, strict=True) if v)<=F(b)
               for row,b in zip(static, limits, strict=True))


def evaluate(task, context):
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_training_score import translate_rows

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact direct support task required')

    def read(suffix):
        return json.loads(context.input_path(model+suffix).read_bytes())

    projection = load_projection_inputs(context, model)
    cuts = read('-cuts')
    kinds = ('coupling', 'consistency', 'orientation')
    static = [row for name in kinds for row in cuts[name]['design']]
    limits = cuts['translated_upper']
    center = read('-force')['center']+[0.]*24
    if len(static)!=132 or limits!=translate_rows(
            static, [b for name in kinds for b in cuts[name]['upper']], center):
        raise ValueError('original audited static constraints must reproduce')
    known = max((row for row in read('-witnesses')['rows']
                 if row['variant']=='linked_shared' and row['loss_passed']),
                key=lambda row:row['score_lower'])
    anchor = tuple(F(a)-F(b) for a,b in zip(known['physical_point']+known['shared'], center, strict=True))
    return compare(context, projection, static, limits, anchor, known['score_lower'], read('-previous'),
                   artifact='direct-support.json')


def compare(context, projection, static, limits, anchor, known_score, old, *, artifact):
    import numpy as np
    from .esa_calibration_witness import check_point
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_coupled_training_score import certify, direct_proposal
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals

    residual, raw, design, lower, upper, earlier, target, settings = projection
    if not feasible_box_and_cuts(anchor, lower, upper, static, limits):
        raise ValueError('saved feasible anchor must remain inside the relaxation')
    objective = np.array([float((a+b)/2) for a,b in target])
    starts = (np.zeros_like(objective), np.asarray(anchor, float))
    if (old['nominal_separation']!=settings['shape']['nominal']
            or [v['earlier_unshared'] for v in old['rows']]!=list(GAMMAS)):
        raise ValueError('exact preceding support settings required')

    rows = []
    for gamma, previous in zip(GAMMAS, old['rows'], strict=True):
        radius = sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))+gamma
        proposals = []
        best_upper = F(previous.get('exact_upper', previous['upper']))
        best_lower = known_score
        for label, start in zip(STARTS, starts, strict=True):
            context.charge(bound_calls=1, bound_steps=STEPS)
            proposal = direct_proposal(design, residual, lower, upper, objective, static, limits,
                                       radius=radius, start=start, iterations=ITERATIONS)
            direction = proposal['direction']
            lo, hi = adjoint_intervals(earlier, direction)
            projected = coefficients(lo, hi, np.ones(len(residual)), raw)
            exact = certify(residual, direction, zip(projected['lower'], projected['upper'], strict=True),
                            target, lower, upper, static, limits, proposal['weights'],
                            increase=INCREASE, unshared=gamma)
            best_upper = min(best_upper, exact)
            checks = []
            for amount in FRACTIONS:
                fraction = F(amount)
                point = [a+fraction*(F(float(b))-a) for a,b in zip(anchor, proposal['point'], strict=True)]
                static_passed = feasible_box_and_cuts(point, lower, upper, static, limits)
                measured = check_point(earlier, raw, residual, target, point, unshared=gamma) if static_passed else {}
                checks.append(dict(fraction=amount, static_passed=static_passed, **measured))
                if measured.get('loss_passed'):
                    best_lower = max(best_lower, measured['score_lower'])
                    break
            proposals.append(dict(start=label, exact_upper=str(exact), checks=checks,
                point=proposal['point'].tolist(), direction=direction.tolist(),
                weights=proposal['weights'].tolist(), iterations=proposal['iterations'],
                success=proposal['success'], status=proposal['status'],
                tangent_proposed=proposal['tangent_proposed']))
        if F(best_lower)>best_upper:
            raise ValueError('certified support and feasible point contradict each other')
        rows.append(dict(earlier_unshared=gamma, previous_upper=previous['upper'],
                         lower=best_lower, upper=endpoint(best_upper, True), proposals=proposals))
    context.save(artifact, dict(rows=rows, nominal_separation=settings['shape']['nominal']))
    return dict(passed=True, rows=[{k:v for k,v in row.items() if k!='proposals'} for row in rows],
                fit_starts=0, later_observations_used=0, physical_map_qualified=False,
                scientific_decision='abstain')


def prepare(root):
    from .esa_coupled_training_score import ID as PARENT
    from .studies.artifacts import atomic
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing direct support freeze')
    staged = {}
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_SHA or not parent.summary['passed']:
            raise ValueError('complete frozen whole-box results required')
        staged['later-operator.npz'] = parent.input('later-operator', raw=True)
        for model in MODELS:
            for suffix, extension in (('', '.npz'), ('-weights', '.npz'), ('-settings', '.json'),
                                      ('-force', '.json'), ('-witnesses', '.json')):
                staged[model+suffix+extension] = parent.input(model+suffix, raw=True)
            staged[model+'-cuts.json'] = parent.artifact(model, 'static-cuts.json', raw=True)
            staged[model+'-previous.json'] = parent.artifact(model, 'composed-support.json', raw=True)
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, payload in staged.items():
        path = base/name
        atomic(path, payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter,
        sources=source_closure(root, [adapter, PLAN]), inputs=inputs, tasks=tasks(), scope=SCOPE,
        workers=2, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
