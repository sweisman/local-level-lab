# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare wider value-only and tangent arithmetic at four sealed points."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path
from time import process_time

import numpy as np

from . import ilvis0_matched_observed_preflight as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-trial-probe-v1-20261118'
ADAPTER = 'analysis/lll/ilvis0_matched_trial_probe.py'
TEST = 'analysis/tests/test_ilvis0_matched_trial_probe.py'
PLAN = parent.FOLDER+'MATCHED_TRIAL_PROBE_PLAN.md'
REQUEST = parent.FOLDER+'matched-trial-probe-qualification.json'
REPORT = parent.FOLDER+'matched-trial-probe-tests.xml'
SCOPE = 'fixed recorded endpoints and correction; value-only versus wider tangent'
POINT_COUNTS = {
    '3df34ea39a6cbdbe15bb0f36-flat_still': 2,
    '3df34ea39a6cbdbe15bb0f36-sphere_rotating': 1,
    '2791235ca0b11b1ef4386e21-flat_geographic_field': 1,
}
TESTS = ('test_probe_grid_counts_only_the_four_declared_points',
         'test_probe_rejects_any_difference_even_at_sub_coordinate_roundoff',
         'test_wide_adapter_preserves_matched_disc_model_and_receiver_prefix')


def tasks(original):
    if not POINT_COUNTS.keys() <= original.keys():
        raise ValueError('missing sealed fit task')
    rows = []
    for identity, count in POINT_COUNTS.items():
        task = {k: v for k, v in original[identity].items() if k not in ('index', 'shard')}
        calls = 2*count
        rows.append(dict(task, native_kind='mixed', limits=dict(native_calls=calls,
            packet_visits=calls*task['training_packets']*task['training_epochs'],
            bound_calls=0, bound_steps=0)))
    return rows


def exact(value, coordinates, difference, residual, boundaries):
    return (value['boundaries'] == boundaries
            and np.array_equal(value['coordinates'], coordinates)
            and np.array_equal(value['coordinate_difference'], difference)
            and np.array_equal(value['residual'], residual))


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (ADAPTER, PLAN, TEST,
        'analysis/tests/test_ilvis0_matched_precision.py', 'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as freeze

    return freeze(root, sources=sources(root), environment=runtime_environment(),
                  output=REQUEST, report=REPORT)


def _point_input(study, task):
    from .ilvis0_matched_precision import correction_point

    identity = task['identity']
    fit = study.artifact(identity, 'fit.json')
    count = POINT_COUNTS[identity]
    if (fit['model'] != task['model'] or fit['converged'] != (count == 1)
            or fit['prediction_receiver_positions_used_in_training']):
        raise ValueError('saved training outcome differs from the declared point selection')
    points = [dict(name='endpoint', value=fit['normalized_parameters'],
        cost=fit['residual_sum_squares'], residual=fit['local_linearization']['residual'])]
    if count == 2:
        _, correction = correction_point(fit)
        points.append(dict(name='fresh_correction', value=correction.tolist(),
                           cost=fit['evaluation_trace'][-1]['cost']))
    return dict(identity=identity, active_parameters=fit['active_parameters'], points=points,
                original_converged=fit['converged'],
                compilation=study.artifact(identity, 'compilation.json'))


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    root = Path(root).resolve()
    base = root/'data'/(ID+'-inputs')
    if (root/'data'/ID).exists():
        raise ValueError('existing point probe allowance must be retained')
    environment, dependencies = runtime_environment(), sources(root)
    qualified, report = checked(root, REQUEST, sources=dependencies, environment=environment,
                                required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, parent.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=qualified, qualification_tests=report,
                     recovery=recovery, recovery_tests=recovery_tests)
    native_sources = ('analysis/lll/ilvis0_native.c', 'analysis/lll/ilvis0_tangent.cpp')
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.manifest['scope'] != parent.SCOPE or study.manifest['environment'] != environment
                or study.input('recipe') != parent.recipe() or study.summary['completed'] != 7
                or any(digest((root/name).read_bytes()) != study.manifest['sources'][name]
                       for name in native_sources)):
            raise ValueError('original closed preflight and numerical environment required')
        rows = tasks(study.tasks)
        materials.update(recipe=study.input('recipe', raw=True), parent_receipt=encoded(study.completion))
        for row in rows:
            identity, segment = row['identity'], row['segment_id']
            materials[identity+'-points'] = encoded(_point_input(study, row))
            for name in (row['input_key'], segment+'-queries', segment+'-training'):
                if name not in materials:
                    materials[name] = study.input(name, raw=True)
    base.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        _write_equal(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=dependencies,
                      inputs=inputs, tasks=rows, workers=3, threads=1, maximum_wall_s=900.)
    _write_equal(base/'definition.json', encoded(definition))
    frozen = Definition.from_dict(definition, root).prepare(root)
    return dict(id=ID, limits=frozen['limits'], allocation=frozen['allocation'])


def evaluate(task, context):
    from .ilvis0_precision_value import _whiten, calculate, load as load_value
    from .ilvis0_wide_tangent import evaluate as wide_evaluate, load as load_wide

    identity = task['identity']
    calls = 2*POINT_COUNTS[identity]
    visits = task['training_packets']*task['training_epochs']
    if (context.manifest['scope'] != SCOPE or task['native_kind'] != 'mixed' or task['limits'] !=
            dict(native_calls=calls, packet_visits=calls*visits, bound_calls=0, bound_steps=0)):
        raise ValueError('changed fixed-point allowance')
    material = parent._json(context, identity+'-points')
    if (material['identity'] != identity or len(material['points']) != calls//2
            or task['input_key'] != task['segment_id']+'-packets'):
        raise ValueError('point input differs from the declared case')
    base, directory, _, compilation = parent.load_training(task, context)
    if list(base.bounds.active) != material['active_parameters']:
        raise ValueError('saved calibration coordinates changed')
    source = context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    tangent, compilation['wide'] = load_wide(directory, expected_source_sha256=source)
    scalar, compilation['scalar'] = load_value(directory, precision='long_double',
                                                expected_source_sha256=source)
    for name in ('value', 'tangent', 'wide'):
        original = material['compilation'][name]
        if any(compilation[name][key] != original[key] for key in ('source_sha256', 'compiler', 'flags')):
            raise ValueError('compiled training arithmetic differs from the parent')
    context.save('compilation.json', compilation)

    model = task['model']
    results = []
    for point in material['points']:
        context.charge(native_kind='tangent', native_calls=1, packet_visits=visits)
        start = process_time()
        coordinates, difference, _, boundaries = wide_evaluate(base, point['value'], model, kernel=tangent)
        residual = _whiten(base, difference, 'stable')
        tangent_cpu_s = process_time()-start
        cost = float(residual @ residual)
        context.charge(native_kind='value', native_calls=1, packet_visits=visits)
        start = process_time()
        value = calculate(base, point['value'], model, kernel=scalar, longitude='stable')
        scalar_cpu_s = process_time()-start
        # Endpoint replay has the original full residual. The correction only
        # has the stored cost because the earlier optimizer did not save its residual.
        replayed = (np.array_equal(residual, point['residual']) if 'residual' in point else
                    math.isclose(cost, point['cost'], rel_tol=1e-10, abs_tol=1e-12))
        result = dict(point=point['name'], exact=exact(value, coordinates, difference, residual, boundaries),
                      cost=cost, saved_cost=point['cost'], replayed=bool(replayed),
                      tangent_cpu_s=tangent_cpu_s, value_cpu_s=scalar_cpu_s,
                      boundaries=boundaries)
        context.save(point['name']+'.json', dict(result,
            tangent_coordinates=coordinates.tolist(), tangent_difference=difference.tolist(),
            tangent_residual=residual.tolist(), scalar_coordinates=value['coordinates'].tolist(),
            scalar_difference=value['coordinate_difference'].tolist(),
            scalar_residual=value['residual'].tolist(), scalar_boundaries=value['boundaries']))
        results.append(result)
    return dict(passed=all(item['exact'] and item['replayed'] for item in results),
        model=model, points=results, original_converged=material['original_converged'],
        fit_starts=0, later_receiver_positions_used=False, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    args = parser.parse_args()
    root = Path.cwd().resolve()
    result = request(root) if args.action == 'request' else prepare(root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
