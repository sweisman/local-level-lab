# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propagate per-epoch receiver velocity covariance through matched force averages."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_girafe_force_contrast as prior
from .esa_doppler_force import CENTERS, GRAVITY_LAWS, WIDTHS, coordinate_rates, predicted_force_ensemble, rate_operator
from .esa_gnss_covariance_audit import covariance_matrix
from .esa_rinex_code_comparison import coordinates
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-force-velocity-error-v1'
SCOPE = 'propagate reported velocity covariance and time-dependence scenarios on ESA 187'
PLAN = prior.PLAN.replace('ESA_GIRAFE_FORCE_CONTRAST_PLAN', 'ESA_FORCE_VELOCITY_ERROR_PLAN')
RESULT = prior.RESULT.replace('esa-girafe-force-contrast-result', 'esa-force-velocity-error-result')
FORCE_SHA = '1b8514cee22c7b5a3c0d0f0ddb10600d0b2fd12ba064f33bb24ef344628a0035'
PARENT = 'data/esa-girafe-force-contrast-v1'
PARENT_SHA = '3d644006180b62d620abc575ce883d7fb601649f54a1a5f9083bf5544db5521a'
RECEIVERS = ('air1', 'mosaic03', 'pwrpak7')
TRAINING = 8
TIME_CONSTANTS_S = (5, 30, 120)
STEP_MPS = .002
TRIALS = 37  # nominal plus positive and negative differences at both steps
PER_SUPPORT = len(prior.MODELS)*len(GRAVITY_LAWS)*TRIALS
TASKS = [task | dict(input_key=task['identity'], limits=dict(native_calls=0, packet_visits=0,
    bound_calls=len(RECEIVERS)*len(WIDTHS)*len(CENTERS),
    bound_steps=len(RECEIVERS)*len(CENTERS)*PER_SUPPORT*sum(4*(w-1) for w in WIDTHS))) for task in prior.TASKS]


def velocity_sensitivity(knots, kernel, center, weights, velocity, scale, model, gravity, initial_height):
    """Return the force value and its derivative with respect to velocity reports."""
    return force_sensitivity(knots, kernel, center, weights@(velocity*scale), weights, scale,
                             model, gravity, initial_height)


def force_sensitivity(knots, kernel, center, coefficients, weights, scale, model, gravity, initial_height):
    """Pass the coefficient sensitivity through the input reports' linear weights."""
    import numpy as np

    amplitude = scale[len(scale)//2]/max(abs(knots))**np.arange(3)[:, None]
    directions = np.eye(9).reshape(9, 3, 3)*amplitude
    offsets = directions*STEP_MPS
    ensemble = np.concatenate((coefficients[None], coefficients+offsets, coefficients-offsets,
                               coefficients+offsets/2., coefficients-offsets/2.))
    values = predicted_force_ensemble(knots, kernel, center, ensemble, model, gravity, initial_height)
    coarse = (values[1:10]-values[10:19]).reshape(3, 3)/(2.*STEP_MPS*amplitude)
    fine = (values[19:28]-values[28:37]).reshape(3, 3)/(STEP_MPS*amplitude)
    a, b = ((weights.T@est)*scale for est in (coarse, fine))
    if not np.allclose(a, b, rtol=0., atol=5e-9):
        raise ValueError('receiver force derivative differs between finite-difference steps')
    return float(values[0]), b


def _time_kernels(times):
    import numpy as np

    t = np.asarray(times, float)
    if t.ndim != 1 or not len(t) or not np.isfinite(t).all() or np.any(np.diff(t) <= 0.):
        raise ValueError('complete, increasing receiver times required')
    distance = abs(t[:, None]-t)
    return {f'{tau}_s': np.exp(-distance/tau) for tau in TIME_CONSTANTS_S}


def _propagate(sensitivity, factors, kernels):
    import numpy as np

    g = np.asarray(sensitivity, float)
    f = np.asarray(factors, float)
    if (g.ndim != 3 or g.shape[2] != 3 or f.shape != (g.shape[1], 3, 3)
            or not np.isfinite(g).all() or not np.isfinite(f).all()):
        raise ValueError('matched finite velocity sensitivities and covariance factors required')
    whitened = np.einsum('sna,nab->snb', g, f)
    results = dict(independent=np.sqrt(np.sum(whitened**2, axis=(1, 2))),
                   shared=np.linalg.norm(whitened.sum(axis=1), axis=1),
                   unrestricted_bound=np.linalg.norm(whitened, axis=2).sum(axis=1))
    for name, kernel in kernels.items():
        filtered = np.einsum('ij,sja->sia', kernel, whitened, optimize=True)
        results[name] = np.sqrt(np.maximum(0., np.sum(whitened*filtered, axis=(1, 2))))
    return results


def propagated_sd(sensitivity, factors, times):
    """Propagate one or more linear force errors under the fixed time scenarios."""
    return _propagate(sensitivity, factors, _time_kernels(times))


def _center_later(values):
    return values[TRAINING:]-values[:TRAINING].mean(axis=0)


def _summarize(sensitivity, factors, kernels):
    import numpy as np

    return {name: dict(support_sd_mps2=values.tolist(), rms_sd_mps2=float(np.sqrt(np.mean(values**2))))
            for name, values in _propagate(_center_later(sensitivity), factors, kernels).items()}


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing velocity-error freeze must stay intact')
    force = (root / prior.RESULT).read_bytes()
    if digest(force) != FORCE_SHA:
        raise ValueError('original matched force scores required')
    scores = {f"{w['kind']}-{w['window']}": w for w in json.loads(force)['windows']}
    paths = {}
    with closing(ClosedStudy(root, PARENT)) as frozen:
        if (frozen.completion['manifest_sha256'] != PARENT_SHA
                or any(frozen.summary['charged'].values()) or set(frozen.tasks) != set(scores)):
            raise ValueError('original eight receiver input freezes required')
        for task in TASKS:
            key = task['identity']
            path = directory / key
            atomic(path, encoded(dict(receiver=frozen.input(key), scores=scores[key])))
            paths[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=paths, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_force_velocity_error.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _receiver_source(rows, width, time, reference, context):
    import numpy as np

    coord = np.asarray(coordinates(rows))
    coord[:, 1] = np.unwrap(coord[:, 1])
    velocities = np.asarray([[r[k] for k in ('north_mps', 'east_mps', 'up_mps')] for r in rows])
    scale = coordinate_rates(coord, np.ones_like(velocities))
    factors = np.linalg.cholesky(np.asarray([covariance_matrix(r['velocity_covariance_export']) for r in rows]))
    kernels = _time_kernels(time)
    estimates = {law: {model: [] for model in prior.MODELS} for law in GRAVITY_LAWS}
    jacobians = {law: {model: np.zeros((len(CENTERS), len(rows), 3)) for model in prior.MODELS}
                 for law in GRAVITY_LAWS}
    half = width//2
    for index, center in enumerate(CENTERS):
        context.charge(bound_calls=1, bound_steps=4*(width-1)*PER_SUPPORT)
        sl = slice(center-half, center+half+1)
        knots = time[sl]-time[center]
        weights, kernel = rate_operator(knots)
        for law in GRAVITY_LAWS:
            for model in prior.MODELS:
                value, slope = velocity_sensitivity(knots, kernel, coord[center], weights, velocities[sl],
                    scale[sl], model, law, coord[0, 2])
                estimates[law][model].append(value)
                jacobians[law][model][index, sl] = slope
    cases = {}
    for law in GRAVITY_LAWS:
        models = jacobians[law]
        recorded = reference[law]['models_mps2']
        if any(not np.allclose(estimates[law][model], recorded[model], atol=2e-12, rtol=0.) for model in models):
            raise ValueError('the original force values did not reproduce')
        differences = {}
        for field, (g, d) in prior.CONTRASTS.items():
            differences[field] = dict(
                shape_difference_rms_mps2=reference[law]['contrasts'][field]['rms_mps2'],
                velocity_error=_summarize(models[g]-models[d], factors, kernels))
        cases[law] = dict(candidate_force={m: _summarize(s, factors, kernels) for m, s in models.items()},
                          contrasts=differences)
    return cases


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact receiver sensitivity task required')
    recorded = json.loads(context.input_path(task['identity']).read_bytes())
    receivers = recorded['receiver']
    scores = recorded['scores']
    primary = receivers['primary']
    times = np.asarray([r['time_s'] for r in primary])
    sources = {'air1': primary, **{name: receivers['alternatives'][name]['rows'] for name in RECEIVERS[1:]}}
    if any(len(v) != 400 for v in sources.values()):
        raise ValueError('full matched receiver velocity reports required')
    widths = []
    for setting in scores['widths']:
        width = setting['width_reports']
        if width not in WIDTHS:
            raise ValueError('force averaging width changed')
        expected = {(row['source'], row['gravity']): row for row in setting['comparisons']}
        cases = {name: _receiver_source(rows, width, times, {law: expected[name, law] for law in GRAVITY_LAWS},
                                       context) for name, rows in sources.items()}
        widths.append(dict(width_reports=width, receivers=cases))
    context.save_bytes('velocity-error.json', encoded(dict(window=scores['window'], kind=scores['kind'],
        widths=widths, scientific_decision='abstain')))
    return dict(passed=len(widths) == len(WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(TASKS):
            raise ValueError('complete eight-window velocity error propagation required')
        windows = []
        for task in TASKS:
            name = task['identity']
            charged = study.rows[name]['charged']
            if any(charged[key] != expected for key, expected in task['limits'].items()):
                raise ValueError('force sensitivity and quadrature charges differ')
            windows.append(study.artifact(name, 'velocity-error.json'))
        result = dict(windows=windows, charged=study.summary['charged'], manifest_sha256=study.completion['manifest_sha256'],
                      force_sha256=FORCE_SHA, parent_manifest_sha256=PARENT_SHA, new_receiver_decodes=0,
                      protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved velocity-error report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_force_velocity_error {prepare,report}')
