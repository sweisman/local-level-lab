# SPDX-License-Identifier: AGPL-3.0-or-later
"""Contract physical calibration boxes with checked necessary training rows."""

from contextlib import closing
from fractions import Fraction as F
from functools import partial
import json
from pathlib import Path
import sys

from .esa_linked_child_certificates import RANGES, INCREASE, read_dispositions, stored_certificate, task_for
from .esa_linked_loss_tangents import ID as PARENT, RESULT as PRIOR
from .esa_linked_scaled_proposals import collect_refinement
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-coordinates-v1'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_COORDINATE_PLAN.md'
RESULT = 'docs/prediction-observed-development/esa-linked-coordinate-result.json'
SCOPE = 'certified physical coordinate projections for all eleven saved ESA calibration children'
PRIOR_SHA = '5a1acfca36ff6cb9064742e3a9751328aeb925ceb87fb12cae15c48a7149a40d'
AXES = tuple(range(27))
TANGENTS = 5
SCORES = 3
frozen_task = partial(task_for, bound_calls=TANGENTS+2*len(AXES)+SCORES,
                      bound_steps=TANGENTS+6*len(AXES)+2*SCORES)


def relaxed_row(intervals, right, lower, upper):
    """Represent the necessary projected constraint using binary coefficients."""
    row = []
    padding = F(0)
    for (a, b), lo, hi in zip(intervals, lower, upper, strict=True):
        a, b, lo, hi = map(F, (a, b, lo, hi))
        if a > b or lo > hi:
            raise ValueError('ordered coefficient intervals and variable bounds required')
        value = float((a+b)/2)
        row.append(value)
        padding += max((F(value)-c)*v for c in (a, b) for v in (lo, hi))
    return row, endpoint(F(right)+padding, True)


def physical_box(lower, upper, center, coordinates):
    """Convert certified displacement projections to an original-source box."""
    lo, hi = list(lower), list(upper)
    for row in coordinates:
        j = row['parameter_index']
        lo[j] = max(lo[j], endpoint(F(center[j])+F(row['lower']), False))
        hi[j] = min(hi[j], endpoint(F(center[j])+F(row['upper']), True))
        if lo[j] > hi[j]:
            raise ValueError('inconsistent contracted endpoint bounds')
    return lo, hi


def _training_row(direction, earlier, residual, raw, lower, upper):
    import numpy as np

    from .esa_shared_profile_score import support
    from .ilvis0_linked_training_support import training_upper
    from .state_space_directional_bound import adjoint_intervals

    a, b = adjoint_intervals(earlier, direction)
    coefficients = support(a, b, np.ones(len(residual)), raw)
    right = training_upper(residual, direction, increase=INCREASE, unshared=0)
    padded = tuple(zip(coefficients['lower'], coefficients['upper'], strict=True))+((F(0), F(0)),)*9
    return relaxed_row(padded, right, lower, upper)


def evaluate(task, context):
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_affine_support import project_coordinates
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_linked_directional import directional_bound

    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    task_row = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or task_row != frozen_task(parent, model, index):
        raise ValueError('exact declared surviving coordinate task required')

    identity = task['identity']
    frozen = json.loads(context.input_path(identity+'-child').read_bytes())
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    certs = json.loads(context.input_path(identity+'-directions').read_bytes())
    child, prior = frozen['child'], frozen['prior']
    parent_cell = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    residual, raw, _, _, _, earlier, target, settings = load_projection_inputs(context, model)
    if (child['index'] != index or prior['index'] != index or prior['excluded']
            or len(parent_cell['static']) != 270 or settings['shape']['nominal'] != frozen['nominal']):
        raise ValueError('original child cover and its static rows must remain intact')

    lower, upper = child['lower'], child['upper']
    force = saved['force']
    center = tuple(map(F, force['center']))
    lo = [endpoint(F(x)-c, False) for x, c in zip(lower, center, strict=True)]+frozen['lower'][27:]
    hi = [endpoint(F(x)-c, True) for x, c in zip(upper, center, strict=True)]+frozen['upper'][27:]
    directions = (residual, parent_cell['earlier_loss']['direction'], parent_cell['score']['direction'],
                  certs['earlier'], certs['latest']['direction'])
    tangents = []
    for direction in directions:
        context.charge(bound_calls=1, bound_steps=1)
        tangents.append(_training_row(direction, earlier, residual, raw, lo, hi))
    design = list(parent_cell['static'])+[row for row, _ in tangents]
    bounds = list(parent_cell['limits'])+[right for _, right in tangents]
    projection = project_coordinates(lo, hi, design, bounds, axes=AXES,
        reserve=lambda calls, steps: context.charge(bound_calls=calls, bound_steps=steps))
    contracted_lo, contracted_hi = physical_box(lower, upper, center, projection['coordinates'])

    witnesses = [row for row in saved['points'] if all(a <= x <= b for a, x, b in
                 zip(lower, row['point'], upper, strict=True))]
    if len(witnesses) != prior['witnesses'] or any(not all(a <= x <= b for a, x, b in
            zip(contracted_lo, row['point'], contracted_hi, strict=True)) for row in witnesses):
        raise ValueError('coordinate projection lost a saved feasible point')

    reference = restore_static_reference(force['configuration'], saved['first_sample']['dv'], saved['first_sample']['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
    static = StaticMap(reference, expected_report=saved['reference'], numerical_allowance=saved['map_allowance'])
    projected = {}
    for label, proposal in (('original', parent_cell['score']), ('scaled', certs['scaled']), ('latest', certs['latest'])):
        context.charge(bound_calls=1, bound_steps=2)
        coefficients, offset = stored_certificate(dict(parent_cell, score=proposal), 'score', target, residual, raw, earlier)
        interval = directional_bound(static, contracted_lo, contracted_hi, coefficients)
        projected[label] = offset+F(interval.hi)

    bound = min(F(prior['upper']), *projected.values())
    if any(bound < F(point['score_lower']) for point in witnesses):
        raise ValueError('new linked score contradicts a saved feasible point')
    changed = [axis for axis in AXES if lower[axis] != contracted_lo[axis] or upper[axis] != contracted_hi[axis]]
    context.save('coordinate-projection.json', dict(projected=projection, lower=contracted_lo, upper=contracted_hi,
        displacement_lower=lo, displacement_upper=hi, training_rows=tangents, changed_coordinates=changed))
    result = dict(identity=identity, parent=parent, model=model, child=index, excluded=False,
        previous_upper=prior['upper'], upper=endpoint(bound, True), witnesses=len(witnesses),
        score_upper={name: str(value) for name, value in projected.items()},
        changed_coordinates=changed, passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def prepare(root):
    from .esa_linked_scaled_proposals import ID as SCALED, RESULT as SCALED_RESULT
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('reuse the existing coordinate projection study')
    raw = (root/PRIOR).read_bytes()
    scaled_report = json.loads((root/SCALED_RESULT).read_bytes())
    if digest(raw) != PRIOR_SHA:
        raise ValueError('exact original loss-tangent report required')
    report = json.loads(raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent, closing(
            ClosedStudy(root, 'data/'+SCALED, store=parent.store)) as scaled:
        for saved, closed in ((report, parent), (scaled_report, scaled)):
            if any(saved[key] != closed.completion[key] for key in ('manifest_sha256', 'summary_sha256')) or not closed.summary['passed']:
                raise ValueError('all saved reports must match their preceding closures')
        records, dispositions = read_dispositions(parent)
        scaled_records, _ = read_dispositions(scaled)
        if (records != report['rows'] or scaled_records != scaled_report['rows']
                or set(records) != set(scaled_records)
                or any(report['dispositions'][name] != row for name, row in dispositions.items())):
            raise ValueError('unchanged prior certificates and dispositions required')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model+suffix] = parent.input(model+suffix, raw=True)
        for name in ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split'):
            staged[name] = parent.input(name, raw=True)
        for identity, task in parent.tasks.items():
            row = dispositions[identity]
            if row['excluded']:
                raise ValueError('do not revisit an excluded calibration child')
            child = parent.input(identity+'-child')
            child['prior']['upper'] = row['upper']
            staged[identity+'-child'] = encoded(child)
            staged[identity+'-directions'] = encoded(dict(earlier=parent.input(identity+'-earlier-direction'),
                scaled=scaled_records[identity]['proposals']['score'], latest=records[identity]['proposals']['score']))
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child'))))
    if len(tasks) != 11:
        raise ValueError('all eleven surviving identities required')

    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR, 'scaled-report': SCALED_RESULT}
    for name, content in staged.items():
        path = base/name
        atomic(path, content)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=tasks,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_linked_coordinates.py']),
        workers=2, threads=1, maximum_wall_s=300.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


if __name__ == '__main__':
    root = Path.cwd()
    if sys.argv[1] == 'prepare':
        print(json.dumps(prepare(root), sort_keys=True))
    elif sys.argv[1] == 'report':
        collect_refinement(root, ID, RESULT)
    else:
        raise ValueError('unknown coordinate study command')
