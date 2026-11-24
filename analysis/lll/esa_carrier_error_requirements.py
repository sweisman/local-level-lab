# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the ESA continuous score bound at alternative, illustrative error caps."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from . import esa_carrier_continuous_bound as parent
from . import esa_carrier_motion_witness_study as geometry
from .studies.artifacts import digest, encoded


ID = 'esa-carrier-error-requirements-v1'
SCOPE = 'ESA 187 independent accuracy requirements from saved continuous bound'
PLAN = parent.FOLDER+'ESA_CARRIER_ERROR_REQUIREMENTS_PLAN.md'
RESULT = parent.FOLDER+'esa-carrier-error-requirements-result.json'
PARENT_SHA = '2081e8d8fc863ddf2e3ccb6cb5ac607e416b3fd8567e6c02623590b330e5b837'
TASK = dict(identity='carrier-accuracy-requirements', input_key='certificate', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=245, bound_steps=1+66*240+4*32*4))
CEILINGS = dict(anchor_axis_m=5., acceleration_rms_mps2=.010, visible_range_rms_m=.020)


def checked_upper(coefficients, caps, geometric_buffer_m, residual):
    terms = [coefficients[key]*caps[key] for key in ('anchor_axis_m', 'acceleration_rms_mps2')]
    terms += [coefficients[key]*(caps[key]+geometric_buffer_m)
              for key in ('visible_range_rms_m', 'invisible_range_rms_m')]
    return math.nextafter(math.fsum([*terms, residual]), math.inf)


def bracket_limit(lower, upper, bound, *, score_limit):
    """Find a verified passing cap in a fixed monotone bracket."""
    if bound(lower) >= score_limit:
        return None
    if bound(upper) < score_limit:
        return dict(value=upper, at_search_ceiling=True)
    for _ in range(32):
        middle = lower+(upper-lower)/2
        if bound(middle) < score_limit:
            lower = middle
        else:
            upper = middle
    return dict(value=lower, at_search_ceiling=False)


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite accuracy requirements replay')
    receipt = (root/parent.RESULT).read_bytes()
    if digest(receipt) != PARENT_SHA:
        raise ValueError('the original continuous bound report is required')
    supplied = json.loads(receipt)
    inputs = {'plan': PLAN, 'certificate': parent.RESULT}
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        identity = parent.TASK['identity']
        if (study.completion != supplied['completion'] or study.envelope(identity)['charged'] != parent.TASK['limits']
                or study.artifact(identity, 'continuous-paths.json') != supplied['paths']):
            raise ValueError('the exact saved continuous bound and multipliers are required')
        for key in ('budget', 'prior', 'motion', 'baseline', 'nkar', 'phase', 'score', 'anchor',
                    'path', 'metric', 'continuity', 'original', 'rinex', 'navigation', 'orbit', 'remainder'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_carrier_error_requirements.py',
                                   'analysis/tests/test_quadratic_support_bound.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .carrier_motion_witness import bracket
    from .carrier_range_remainder import bound_score_remainder, position_cap

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen accuracy requirements replay is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    previous, remainder = (json.loads(raw(key)) for key in ('certificate', 'remainder'))
    problem, position_bound, offset, gradients, support, screen = geometry.reconstruct_problem(raw, context.charge)
    caps = problem['caps']
    knots = np.union1d(problem['times'], problem['score_times'])
    buffer = problem['geometric_buffer_m']
    if (caps != previous['caps'] or problem['gap'] != previous['score_gap']
            or (knots+offset).tolist() != previous['paths']['knot_gps_s']):
        raise ValueError('unchanged score grid and error limits required')
    anchors = (problem['times'][problem['anchor_indices']]+offset).tolist()

    def geometry_cap(limits):
        coordinate = position_cap(anchors, limits['anchor_axis_m'], limits['acceleration_rms_mps2'])
        end = bound_score_remainder([1, -1], [2], remainder['metric'],
                                   remainder['max_absolute_path_height_m'], coordinate)
        return (math.nextafter(float(coordinate), math.inf),
                math.nextafter(float(2*end['endpoint_range_remainder_m']), math.inf))

    if geometry_cap(caps) != (position_bound, buffer):
        raise ValueError('the base geometric remainder must reproduce')
    results = []
    for (initial, operator, retained), saved in zip(geometry.screened_operators(
            problem['times'], gradients, support, screen, context.charge, 32*4),
            previous['paths']['rows'], strict=True):
        if initial != saved['initial_tilt_allowance_deg']:
            raise ValueError('unchanged case order required')
        replay = bracket(coordinate_caps=position_bound, multipliers=saved['multipliers'],
                         **problem, knots=knots, operator=operator, support=retained)
        if (replay['iterations'] != 0
                or not math.isclose(replay['upper']*previous['geometric_dilation'], saved['verified_upper'],
                                    rel_tol=1e-10, abs_tol=1e-11)):
            raise ValueError('the original upper bound must reproduce without optimizing')
        terms = replay['norm_terms']
        coefficients = dict(
            acceleration_rms_mps2=float(terms[0])/caps['acceleration_rms_mps2'],
            visible_range_rms_m=float(terms[1])/(caps['visible_range_rms_m']-buffer),
            invisible_range_rms_m=float(terms[2])/(caps['invisible_range_rms_m']-buffer),
            anchor_axis_m=math.fsum(terms[3:])/caps['anchor_axis_m'],
        )
        residual_per_m = math.fsum(replay['residual_by_coordinate'])

        def bound(limits):
            coordinate, margin = geometry_cap(limits)
            return checked_upper(coefficients, limits, margin, residual_per_m*coordinate)

        baseline = bound(caps)
        if baseline > saved['verified_upper']+1e-10:
            raise ValueError('separate remainder terms cannot exceed the uniform bound')
        one_at_a_time = {
            key: bracket_limit(0., ceiling, lambda value: bound(caps | {key: value}), score_limit=1.)
            for key, ceiling in CEILINGS.items()
        }
        joint = bracket_limit(0., 5., lambda factor: bound({key: cap*factor for key, cap in caps.items()}),
                              score_limit=1.)
        results.append(dict(initial_tilt_allowance_deg=initial, at_example_caps=baseline,
                            original_upper=saved['verified_upper'], exact_score_weights=coefficients,
                            residual_score_per_m=residual_per_m, one_cap_at_a_time=one_at_a_time,
                            joint_factor=joint))
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                original_reads=0, new_fits=0, protected_reads=0, optimizer_iterations=0,
                example_caps=caps, cases=results)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the verified completed accuracy requirements replay is required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'])
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key != 'inputs'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
