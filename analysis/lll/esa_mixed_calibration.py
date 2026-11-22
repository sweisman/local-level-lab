# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check nonlinear interactions along matched weak calibration stencils."""

import argparse
from contextlib import closing
from itertools import combinations as choose
import json
from pathlib import Path
import sys


ID = 'esa-mixed-calibration-v1-20261118'
ADAPTER = 'analysis/lll/esa_mixed_calibration.py'
HELPER = 'analysis/lll/esa_tangent_remainder.py'
PLAN = 'docs/prediction-observed-development/ESA_MIXED_CALIBRATION_PLAN.md'
SCOPE = 'fixed earlier-calibration mixed finite changes on all three ESA candidates'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
RADII = (.01, .10)
SUBSETS = tuple(axis for size in range(1, 4) for axis in choose(range(3), size))
CALLS = 1 + len(RADII)*len(SUBSETS)
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'environment',
          'parent', 'frozen_python_native')
CANDIDATE = ('fit', 'forecast', 'training_observations', 'compiler')


def combinations(point, rays, *, radius):
    """All subsets use identical parameter increments regardless of order."""
    import numpy as np

    shifts = {axes: np.sum(rays[list(axes)], axis=0) for axes in SUBSETS}
    maximum = max(float(np.linalg.norm(step)) for step in shifts.values())
    if not np.isfinite(maximum) or maximum <= 0:
        raise ValueError('nonzero finite calibration stencil required')
    trials = {axes: point+(radius/maximum)*step for axes, step in shifts.items()}
    if any(np.any(np.abs(target) > 1) for target in trials.values()):
        raise ValueError('combined parameter step leaves the declared calibration bounds')
    return trials


def interaction(paths, axes):
    """Finite mixed difference with all paths relative to the same origin."""
    result = paths[axes].copy()
    for size in range(1, len(axes)):
        for subset in choose(axes, size):
            result += (-1)**(len(axes)-size)*paths[subset]
    return result


def inward_rays(point, rays):
    """Drop only outward components at active faces, using one sign per ray."""
    import numpy as np

    near_upper = point >= 1.-1e-8
    near_lower = point <= -1.+1e-8
    projected = []
    for ray in rays:
        choices = [np.where((near_upper & (candidate > 0)) |
                            (near_lower & (candidate < 0)), 0., candidate)
                   for candidate in (ray, -ray)]
        projected.append(max(choices, key=np.linalg.norm))
    matrix = np.asarray(projected)
    if np.linalg.matrix_rank(matrix) != 3:
        raise ValueError('three independent feasible calibration directions required')
    return matrix


def tasks():
    from .esa_tangent_remainder import PACKETS, TRAIN, FORECAST

    return [dict(identity=model, input_key='interval', native_kind='value',
                 payload=dict(model=model, radii=list(RADII)),
                 limits=dict(native_calls=CALLS, packet_visits=CALLS*PACKETS*(TRAIN+FORECAST),
                             bound_calls=0, bound_steps=0)) for model in MODELS]


def candidate_key(model, name):
    return model+'-'+name


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_native_tangent_replay import AUTHORITATIVE, PARENT_SHA
    from .esa_tangent_remainder import REPLAY, REPLAY_SHA, weak_rays
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing frozen mixed study')
    with (closing(ClosedStudy(root, AUTHORITATIVE)) as study,
          closing(ClosedStudy(root, REPLAY)) as replay):
        if (study.completion['manifest_sha256'] != PARENT_SHA
                or study.summary['completed'] != 24
                or replay.completion['manifest_sha256'] != REPLAY_SHA
                or replay.input('environment') != require_guarded_environment(environment())):
            raise ValueError('exact earlier-only parents and original environment required')
        materials = {key: replay.input(key, raw=True) for key in SHARED}
        for model in MODELS:
            identity = model+'-1-increment-0'
            if not study.rows[identity]['passed']:
                raise ValueError('passing original training fit required: '+identity)
            source = {name: study.artifact(identity, artifact, raw=True) for name, artifact in
                      [('fit', 'fit.json'), ('forecast', 'forecast.json'),
                       ('training_observations', 'training-observations.json')]}
            source['compiler'] = encoded(study.artifact(identity, 'compilation.json')['tangent'])
            fit = json.loads(source['fit'])
            point, rays = weak_rays(fit['normalized_parameters'], fit['local_linearization']['jacobian'])
            rays = inward_rays(point, rays)
            for radius in RADII:
                combinations(point, rays, radius=radius)
            materials.update({candidate_key(model, name): data for name, data in source.items()})
        if any(digest(materials[key]) != study.manifest['inputs'][key]['sha256']
               for key in ('interval', 'training', 'forecast_times', 'recipe')):
            raise ValueError('mixed study inputs differ from the original fit matrix')
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(), inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN]), workers=1,
                      threads=1, maximum_wall_s=180.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen

    model = declared['identity']
    keep = {k: v for k, v in declared.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or keep != next((row for row in tasks() if row['identity'] == model), None)
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('unchanged matched model, task and environment required')
    names = (*SHARED, *(candidate_key(model, key) for key in CANDIDATE))
    raw = invoke_frozen(context, entry=Path(__file__), calls=CALLS,
                        inputs=names, companions=(HELPER,))
    report = json.loads(raw)
    if report['model'] != model or len(report['comparisons']) != len(RADII):
        raise ValueError('all mixed comparisons must be present for the declared model')
    context.save_bytes('mixed-changes.json', raw)
    return dict(passed=True, model=model, radius_count=len(RADII), fit_starts=0,
                later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')


def frozen_replay(inputs, output):
    import numpy as np
    from lll.esa_tangent_remainder import TRAIN, scalar_replay, summarize, weak_rays
    from lll.studies.artifacts import encoded

    model, = [candidate for candidate in MODELS if candidate_key(candidate, 'fit') in inputs]
    inputs.update({name: inputs[candidate_key(model, name)] for name in CANDIDATE})
    fit, point, metric, compiler, baseline, baseline_max, displacement = scalar_replay(
        inputs, output, expected_model=model)
    _, original = weak_rays(point, fit['local_linearization']['jacobian'])
    rays = inward_rays(point, original)
    comparisons = []
    for radius in RADII:
        steps = combinations(point, rays, radius=radius)
        paths = {axes: displacement(target)-baseline for axes, target in steps.items()}
        errors = []
        for axes in SUBSETS:
            if len(axes) == 1:
                continue
            summed = paths[axes]-interaction(paths, axes)
            errors.append(dict(axes=axes, **summarize(paths[axes], summed, metric, cut=TRAIN)))
        triple = (0, 1, 2)
        additive = sum(paths[(axis,)] for axis in triple)
        comparisons.append(dict(radius=radius, interactions=errors,
            all_axes_vs_sum=summarize(paths[triple], additive, metric, cut=TRAIN),
            parameter_steps=[dict(axes=axes, change=(target-point).tolist())
                             for axes, target in steps.items()]))
    output.write_bytes(encoded(dict(model=model, compiler=compiler,
        baseline_scalar_max_m=baseline_max, retained_ray_norm=np.linalg.norm(rays, axis=1).tolist(),
        comparisons=comparisons, fit_starts=0, later_receiver_positions_read=0,
        protected_reads=0, establishes_uniform_bound=False, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
