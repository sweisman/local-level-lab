# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bracket the ESA carrier-score ambiguity across all smooth position errors."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import esa_carrier_motion_witness_study as parent
from .studies.artifacts import digest, encoded


ID = 'esa-carrier-continuous-bound-v1'
SCOPE = 'ESA 187 continuous trajectory error bound on fixed carrier support'
FOLDER = parent.parent.FOLDER
PLAN = FOLDER+'ESA_CARRIER_CONTINUOUS_BOUND_PLAN.md'
RESULT = FOLDER+'esa-carrier-continuous-bound-result.json'
PARENT_SHA = '6662f1f8722db5574702bf8cb38aca3a677f4bab6953d324b5c56770066bf5bf'
ITERATIONS = 60
MAX_KNOTS = 361
CASE_STEPS = (ITERATIONS+2)*3*MAX_KNOTS
TASK = dict(identity='continuous-carrier-bracket', input_key='parent', payload={},
            limits=dict(native_calls=0, packet_visits=0,
                        bound_calls=1+parent.PAIRS+1+len(parent.CASES),
                        bound_steps=1+66*parent.PAIRS+(1+len(parent.CASES))*CASE_STEPS))


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite continuous bound study')
    receipt = (root/parent.RESULT).read_bytes()
    if digest(receipt) != PARENT_SHA:
        raise ValueError('original motion-search report required')
    supplied = json.loads(receipt)
    inputs = {'plan': PLAN, 'parent': parent.RESULT}
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        envelope = study.envelope(parent.TASK['identity'])
        if (study.completion != supplied['completion'] or envelope['charged'] != parent.TASK['limits']
                or any(supplied[key] != value for key, value in envelope['result'].items())):
            raise ValueError('completed motion search and preserved stops required')
        for key in ('budget', 'prior', 'motion', 'baseline', 'nkar', 'phase', 'score', 'anchor',
                    'path', 'metric', 'continuity', 'original', 'rinex', 'navigation', 'orbit', 'remainder'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_carrier_motion_witness.py',
                                   'analysis/tests/test_quadratic_support_bound.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=180)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .carrier_motion_witness import bracket, geometry_dilation, verify

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen continuous score bound is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    prior = json.loads(raw('parent'))
    problem, coordinate_cap, offset, gradients, support, screen = parent.reconstruct_problem(raw, context.charge)
    caps = problem['caps']
    buffer_m = problem['geometric_buffer_m']
    if caps != prior['caps'] or buffer_m != prior['geometric_buffer_rms_m'] or problem['gap'] != prior['score_gap']:
        raise ValueError('unchanged error limits and range remainder required')
    dilution = geometry_dilation(caps['visible_range_rms_m'], caps['invisible_range_rms_m'], buffer_m)
    knots = np.union1d(problem['times'], problem['score_times'])
    if (len(knots) > MAX_KNOTS or knots[0] != problem['times'][0] or knots[-1] != problem['times'][-1]):
        raise ValueError('the complete carrier and score grid must fit within the frozen allowance')
    results = []
    for initial, operator, retained in parent.screened_operators(
            problem['times'], gradients, support, screen, context.charge, CASE_STEPS):
        inputs = dict(problem, knots=knots, operator=operator, support=retained)
        solution = bracket(coordinate_caps=coordinate_cap, max_iterations=ITERATIONS, **inputs)
        # A little slack keeps the direct spline evaluation away from the
        # machine-precision boundary of the algebraic feasibility check.
        safety = 1-1e-6
        path = solution['positions']*safety
        checked = verify(path, **inputs)
        lower = min(solution['lower']*safety, checked['score_fraction'])
        upper = float(np.nextafter(solution['upper']*dilution, np.inf))
        if not checked['within_linear_and_geometry_caps'] or not 0 <= lower <= upper or not np.isfinite(upper):
            raise ValueError('independent continuous bound checks failed')
        status = 'witness' if lower >= 1 else 'excluded_under_caps' if upper < 1 else 'undetermined'
        results.append(dict(initial_tilt_allowance_deg=initial, verified_lower=lower, verified_upper=upper,
                            status=status, optimizer_status=solution['optimizer_status'],
                            optimizer_iterations=solution['iterations'], positions_m=path.tolist(),
                            multipliers=solution['multipliers'].tolist(), **checked))
    context.save('continuous-paths.json', dict(knot_gps_s=(knots+offset).tolist(), rows=results))
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                caps=caps, score_gap=problem['gap'], knots=len(knots), geometric_dilation=dilution,
                original_reads=0, new_fits=0, protected_reads=0,
                cases=[{key: value for key, value in row.items() if key not in ('positions_m', 'multipliers')}
                       for row in results])


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('complete verified continuous bracket required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'], paths=study.artifact(TASK['identity'], 'continuous-paths.json'))
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key not in ('inputs', 'paths')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
