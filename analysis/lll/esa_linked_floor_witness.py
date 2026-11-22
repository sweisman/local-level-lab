# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify candidate witnesses from the sealed calibration score-floor study."""

from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path
import sys

from .esa_linked_score_floor import ID as PARENT, RANGES, RESULT as PRIOR
from .esa_linked_child_certificates import task_for
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-floor-witness-v1'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'ESA_LINKED_FLOOR_WITNESS_PLAN.md'
RESULT = FOLDER + 'esa-linked-floor-witness-result.json'
SCOPE = 'Exact relaxed point checks and linked surrogate replay of eleven ESA score floors'
PRIOR_SHA = '35a27e8280cada9a1fc21ab1867c03782acd30a86b70be62e9d4aa0c0f14fd99'
MARGINS = (0., 1e-9)


def affine_violation(point, lower, upper, rows, limits):
    """Return the largest exact original-unit violation, or zero on feasibility."""
    x = tuple(Fraction(float(v)) for v in point)
    box = [max(Fraction(float(lo))-v, v-Fraction(float(hi)))
           for lo, v, hi in zip(lower, x, upper, strict=True)]
    inequalities = [sum(Fraction(float(a))*b for a, b in zip(row, x, strict=True) if a and b)
                    - Fraction(float(rhs)) for row, rhs in zip(rows, limits, strict=True)]
    return max([Fraction(0), *box, *inequalities])


def residual_point(design, residual, lower, upper, rows, limits, target, margin):
    """Propose a calibration near a previously saved residual using one LP."""
    import numpy as np

    from .esa_linked_scaled_proposals import scaled_problem
    from .ilvis0_affine_support import linear_proposal

    design, residual = np.asarray(design), np.asarray(residual)
    lower, upper = np.asarray(lower, float), np.asarray(upper, float)
    width = (upper-lower)/2
    center = lower+width
    zero = np.zeros(len(lower))
    d, r, lo, hi, a, b, _, _ = scaled_problem(design, residual, lower, upper, rows, limits, zero, center)
    basis, reduced = np.linalg.qr(np.c_[r, d], mode='reduced')
    wanted = basis.T @ target - reduced[:, 0]
    d = reduced[:, 1:]
    scale = np.maximum(1e-20, np.maximum(np.max(np.abs(a), axis=1), np.abs(b)))
    a, b = a/scale[:, None], b/scale
    b -= margin*np.any(a != 0., axis=1)
    residual_scale = max(1., float(np.linalg.norm(target)))
    d, wanted = d/residual_scale, wanted/residual_scale
    limit = 1.+float(np.max(np.abs(wanted)))
    optimum = linear_proposal((1-margin)*np.r_[lo, 0.], np.r_[(1-margin)*hi, limit],
        np.r_[np.c_[a, np.zeros(len(a))], np.c_[d, -np.ones(len(d))], np.c_[-d, -np.ones(len(d))]],
        np.r_[b, wanted, -wanted], np.r_[zero, -1.])
    return None if optimum is None else center + width*optimum[0][:-1]


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing frozen floor-witness study')
    prior_raw = (root/PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('original score-floor report required')
    prior = json.loads(prior_raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed']):
            raise ValueError('the exact score-floor closure is required')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model+suffix] = parent.input(model+suffix, raw=True)
        staged['later-operator'] = parent.input('later-operator', raw=True)
        for identity, task in parent.tasks.items():
            source = parent.artifact(identity, 'floor-certificates.json')
            trial = max(source['trials'], key=lambda row: row['floor'])
            if trial['excluded'] or 'loss' not in trial:
                raise ValueError('expected unresolved maximum tested score floor')
            staged[identity+'-trial'] = encoded(trial)
            for suffix in ('-child', '-floors'):
                staged[identity+suffix] = parent.input(identity+suffix, raw=True)
            tasks.append(task_for(*(task['payload'][key] for key in ('parent', 'model', 'child')),
                                  bound_calls=2, bound_steps=6))
    if len(tasks) != 11:
        raise ValueError('every surviving calibration range required')
    inputs = dict(plan=PLAN, prior=PRIOR)
    for name, raw in staged.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=tasks,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_linked_floor_witness.py']),
        workers=2, threads=1, maximum_wall_s=120.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    from .esa_calibration_witness import check_point
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_map import restore_static_reference
    from .ilvis0_exact_scale import sqrt_upper

    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != task_for(parent, model, index, bound_calls=2, bound_steps=6):
        raise ValueError('exact score-floor point check required')
    identity = task['identity']
    frozen, region, trial = [json.loads(context.input_path(identity+suffix).read_bytes())
                             for suffix in ('-child', '-floors', '-trial')]
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    static = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    residual, raw, design, _, _, earlier, score, settings = load_projection_inputs(context, model)
    lower, upper = region['lower'], region['upper']
    if len(lower) != 60 or len(upper) != 60 or len(region['rows']) != 12 or len(static['static']) != 270:
        raise ValueError('exact archived box and coupled inequalities required')
    rows = [*static['static'], *(row for row, _ in region['rows']), trial['floor_row']]
    limits = [*static['limits'], *(limit for _, limit in region['rows']), trial['floor_limit']]
    residual_target = np.asarray(trial['loss']['direction'])*trial['loss']['proposed_norm']
    full_design = np.c_[design, np.zeros((len(residual), 9))]
    force, packet = saved['force'], saved['first_sample']
    reference = restore_static_reference(force['configuration'], packet['dv'], packet['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
    center = reference.parent.center
    threshold = trial['floor']
    checks = []
    for margin in MARGINS:
        context.charge(bound_calls=1, bound_steps=3)
        point = residual_point(full_design, residual, lower, upper, rows, limits, residual_target, margin)
        if point is None:
            checks.append(dict(inward_margin=margin, point_proposed=False))
            continue
        violation = affine_violation(point, lower, upper, rows, limits)
        relaxed = check_point(earlier, raw, residual, score, point[:51])
        physical = np.clip(center+point[:27], frozen['child']['lower'], frozen['child']['upper'])
        common = reference.normalized_values_at(physical)
        delta = [Fraction(float(a))-Fraction(float(b)) for a, b in zip(physical, center, strict=True)]
        linked = (check_point(earlier, raw, residual, score, [*delta, *common])
                  if np.isfinite(common).all() and np.max(np.abs(common)) <= 1. else None)
        checks.append(dict(inward_margin=margin, point_proposed=True, point=point.tolist(),
            maximum_original_constraint_violation=float(violation), affine_passed=violation == 0,
            target_residual_error=float(np.linalg.norm(residual+full_design@point-residual_target)),
            relaxed=relaxed, relaxed_floor_verified=violation == 0 and relaxed['loss_passed']
            and relaxed['score_lower'] >= threshold,
            physical_parameters=physical.tolist(), linked=linked))
    radius = sqrt_upper(sum(Fraction(float(v))**2 for v in residual)+Fraction(.01))
    record = dict(identity=identity, model=model, score_floor=threshold, norm_radius=radius,
        saved_proposal_norm=trial['loss']['proposed_norm'], nominal_gap=settings['shape']['nominal'], checks=checks,
        passed=True, scientific_decision='abstain')
    context.save('checked-witness.json', record)
    return {k: v for k, v in record.items() if k != 'checks'} | dict(
        proposals_found=sum(row['point_proposed'] for row in checks),
        relaxed_floor_witnesses=sum(row.get('relaxed_floor_verified', False) for row in checks),
        linked_loss_passes=sum(bool(row.get('linked') and row['linked']['loss_passed']) for row in checks))


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != 22:
            raise ValueError('complete saved range checks required')
        rows = [study.artifact(identity, 'checked-witness.json') for identity in study.tasks]
        result = dict(manifest_sha256=study.completion['manifest_sha256'], ranges=rows,
                      scientific_decision='abstain')
    raw = encoded(result)
    dest = root/RESULT
    if not dest.exists():
        atomic(dest, raw)
    if dest.read_bytes() != raw:
        raise ValueError('saved floor-witness result differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_linked_floor_witness {prepare,report}')
