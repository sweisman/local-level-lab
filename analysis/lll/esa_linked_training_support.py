# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use earlier observations to bound a saved ESA forecast contrast."""

from contextlib import ExitStack, closing
from fractions import Fraction
from io import BytesIO
import json
from pathlib import Path


ID = 'esa-linked-training-support-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_TRAINING_SUPPORT_PLAN.md'
SCOPE = 'Joint 51-coordinate earlier-loss support on sealed ESA 187 predictions'
MODELS = ('sphere_still', 'flat_still')
PROFILE_SHA = '80e3e13b8b7850b04d6c93f2cd3d033e337056b3bd59c5fab3b342728f64185b'
REMAINDERS = (0., .1, 1.)
INCREASE = .01
TRAIN = 400
LATER = 120


def tasks():
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=1, bound_steps=len(REMAINDERS))) for model in MODELS]


def load_projection_inputs(context, model):
    return projection_inputs(lambda key: context.input_path(key).read_bytes(), model)


def training_inputs(load, model):
    import numpy as np
    from .innovations_snapshot import restore

    settings = json.loads(load(model+'-settings'))
    earlier_raw = load(model+'-weights')
    earlier = restore(earlier_raw, expected_sha256=settings['earlier_weights'],
                      expected_configuration=settings['earlier_configuration'], maximum_bytes=2**26)
    with np.load(BytesIO(load(model)), allow_pickle=False) as data:
        residual, raw_design, lower, upper, local, nominal = (
            data[k] for k in ('residual', 'design', 'lower', 'upper', 'local', 'nominal')
        )
    start = 3*TRAIN
    if (raw_design.shape != (3*(TRAIN+LATER), 51) or residual.shape != (start,)
            or local.shape != (start, 27) or lower.shape != (51,) or upper.shape != (51,)
            or not np.array_equal(earlier.whiten(nominal), residual)):
        raise ValueError('original earlier fit, coordinate units and all shared terms required')
    raw_earlier = raw_design[:start]
    design = earlier.whiten(raw_earlier)
    if not np.allclose(design[:, :27], local, rtol=1e-10, atol=1e-8):
        raise ValueError('saved earlier calibration Jacobian did not reproduce')
    return residual, raw_design, design, lower, upper, earlier, settings


def projection_inputs(load, model):
    import numpy as np
    from .esa_shared_profile_score import support as coefficients
    from .innovations_snapshot import restore
    from .state_space_directional_bound import adjoint_intervals

    residual, raw_design, design, lower, upper, earlier, settings = training_inputs(load,model)
    later = restore(load('later-operator'), expected_sha256=settings['shape']['factors_sha256'],
                    expected_configuration=settings['shape']['configuration'], maximum_bytes=2**26)
    start = 3*TRAIN
    sign = 1 if model == 'sphere_still' else -1
    direction = sign * np.r_[np.zeros(start), settings['shape']['direction']]
    metric = np.tile(settings['shape']['metric'], TRAIN+LATER)
    score_lo, score_hi = adjoint_intervals(later, direction)
    objective = coefficients(score_lo, score_hi, metric, raw_design)
    target = tuple(zip(objective['lower'], objective['upper'], strict=True))
    return residual, raw_design[:start], design, lower, upper, earlier, target, settings


def evaluate(task, context):
    import numpy as np
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_linked_training_support import propose_direction, support
    from .state_space_directional_bound import adjoint_intervals
    from .studies.artifacts import digest

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact joint training-support task required')
    context.charge(bound_calls=1, bound_steps=len(REMAINDERS))
    residual, raw_earlier, design, lower, upper, earlier, target, settings = load_projection_inputs(context, model)
    midpoint = np.array([float((a+b)/2) for a, b in target])
    rows = []
    for gamma in REMAINDERS:
        radius = sqrt_upper(sum(Fraction(float(v))**2 for v in residual) + Fraction(INCREASE)) + gamma
        proposal, success = propose_direction(design, residual, midpoint, lower, upper, radius)
        lo, hi = adjoint_intervals(earlier, proposal)
        training = coefficients(lo, hi, np.ones(len(residual)), raw_earlier)
        certified = support(residual, proposal, zip(training['lower'], training['upper'], strict=True),
                            target, lower, upper, increase=INCREASE, unshared=gamma)
        rows.append(dict(unshared_earlier_norm=gamma, direction=proposal.tolist(),
                         proposal_success=success, **certified))
    context.save('supports.json', dict(rows=rows, input_sha256=digest(context.input_path().read_bytes()),
                                        nominal_separation=settings['shape']['nominal']))
    return dict(passed=True, rows=[{k: v for k, v in row.items() if k != 'direction'} for row in rows],
                parameter_count=51, training_epochs=TRAIN, later_observations_used=0,
                fit_starts=0, unshared_remainder_qualified=False,
                observational_coverage_qualified=False, scientific_decision='abstain')


def prepare(root):
    import numpy as np
    from .esa_shared_profile import ID as PROFILE
    from .esa_shared_profile_score import WITNESS_MANIFEST
    from .ilvis0_saved_prediction_audit import endpoint
    from .ilvis0_precision_value import longitude_residual
    from .shape_remainder_witness import ID as WITNESS, SOURCE, SOURCE_SHA
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing joint-support freeze')
    staged = {}
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, SOURCE)))
        profile = stack.enter_context(closing(ClosedStudy(root, 'data/'+PROFILE, store=parent.store)))
        witness = stack.enter_context(closing(ClosedStudy(root, 'data/'+WITNESS, store=parent.store)))
        receipts = {}
        for name, study, expected in (('calibration-contrast', parent, SOURCE_SHA),
                                      ('shared-profile', profile, PROFILE_SHA),
                                      ('shape-witness', witness, WITNESS_MANIFEST)):
            if study.completion['manifest_sha256'] != expected or not study.summary['passed']:
                raise ValueError('exact completed parent studies required')
            receipts[name] = expected
        shape = witness.input('shape-direction')
        staged['later-operator'] = ('.npz', witness.input('later-operator', raw=True))
        times = np.asarray(witness.input('forecast_times'))
        for model in MODELS:
            raw_snapshot = parent.input(model+'-weights', raw=True)
            receipt = parent.input(model+'-weights-receipt')
            forecast = parent.input(model+'-forecast')
            fit = parent.input(model+'-fit')
            tangent = parent.artifact(model, 'full-tangent.json')
            with np.load(BytesIO(profile.input(model, raw=True)), allow_pickle=False) as settings:
                center, low, high, positions = (settings[k] for k in ('center', 'lower', 'upper', 'positions'))
            with np.load(BytesIO(profile.artifact(model, 'shared-profile.npz', raw=True)),
                         allow_pickle=False) as saved:
                shared = saved['shared']
                if not np.array_equal(saved['times'], times):
                    raise ValueError('joint design must use the saved scoring epochs')
            if (fit['active_parameters'] != tangent['active_parameters']
                    or digest(raw_snapshot) != receipt['snapshot_sha256']
                    or digest(parent.input(model+'-forecast', raw=True)) != tangent['source_forecast_sha256']
                    or not np.array_equal(positions, forecast['coordinates'])
                    or not np.array_equal(center, tangent['normalized_parameters'])
                    or not np.array_equal(center, fit['normalized_parameters'])
                    or not np.array_equal(tangent['forecast_queries_s'], times)):
                raise ValueError('shared coefficients do not align with the saved fit and tangent')
            lower = [endpoint(Fraction(float(a))-Fraction(float(c)), False)
                     for a, c in zip(low, center, strict=True)] + [-1.]*24
            upper = [endpoint(Fraction(float(b))-Fraction(float(c)), True)
                     for b, c in zip(high, center, strict=True)] + [1.]*24
            nominal = np.array(forecast['training_coordinate_difference'])
            nominal[:, 1] = longitude_residual(nominal[:, 1])
            local = fit['local_linearization']
            payload = BytesIO()
            np.savez_compressed(payload, design=np.c_[tangent['jacobian'], shared.reshape(-1, 24)],
                                residual=local['residual'], lower=lower, upper=upper,
                                local=local['jacobian'], nominal=nominal.ravel())
            staged[model] = ('.npz', payload.getvalue())
            staged[model+'-weights'] = ('.npz', raw_snapshot)
            staged[model+'-settings'] = ('.json', encoded(dict(
                parent_manifests=receipts, earlier_weights=receipt['snapshot_sha256'],
                earlier_configuration=forecast['error_training_configuration'], shape=shape)))
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, (extension, payload) in staged.items():
        path = base/(name+extension)
        atomic(path, payload)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter,
        sources=source_closure(root, [adapter, PLAN]), inputs=inputs, tasks=tasks(), scope=SCOPE,
        workers=2, threads=1, maximum_wall_s=120.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
