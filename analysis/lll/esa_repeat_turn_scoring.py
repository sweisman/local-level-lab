# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed working covariance scores for sealed ESA repeat-turn forecasts."""

import argparse
import json
import math
from pathlib import Path
import re


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_REPEAT_TURN_SCORING_PLAN.md'
REQUEST = BASE+'esa-repeat-turn-scoring-qualification.json'
REPORT = BASE+'esa-repeat-turn-scoring-tests.xml'
TEST = 'analysis/tests/test_esa_repeat_turn_scoring.py'
VERSION = 'esa-repeat-turn-fixed-error-score-v1'
SOURCE_SHA = '5ba7d7e69ed3ce3ecfd164f7910af24efe2650f2e964e4fea72b571623848ee2'
NATIVE_VARIANCE = dict(increment=0.01120347374458397, point=0.01120343530700332)
STEADY_SD, TURN_SD, DECAY_S = .001, .001, 15.
MAX_REPORTS = 120
TEST_NAMES = (
    'test_score_agrees_with_independent_dense_gaussian_calculation',
    'test_changed_sealed_forecast_or_scoring_clock_is_rejected',
    'test_reversed_measured_turn_preserves_the_covariance_rule',
    'test_known_generated_errors_recover_joint_reference_distribution',
)


def _lower(root, dimension):
    import numpy as np

    value = np.asarray(root, float)
    if (value.shape != (dimension, dimension) or not np.isfinite(value).all()
            or np.any(np.triu(value, 1)) or np.any(value.diagonal() <= 0.)):
        raise ValueError('finite positive lower covariance factor required')
    return value


def factors(times, *, previous_time, native_root, exposure, law):
    """Keep the native and both conditional forecast-error terms separate."""
    import numpy as np
    from .maneuver_error_roots import roots

    if law not in NATIVE_VARIANCE or not 1 <= len(times) <= MAX_REPORTS:
        raise ValueError('declared native error description and finite forecast size required')
    native = _lower(native_root, 3*len(times))*math.sqrt(NATIVE_VARIANCE[law])
    components = roots(times, exposure, previous_time=previous_time, decay_s=DECAY_S)
    steady = components['persistent']*STEADY_SD
    maneuver = components['maneuver']*TURN_SD
    base = native@native.T
    persistent = steady@steady.T
    transient = maneuver@maneuver.T
    return dict(native=native, steady=np.linalg.cholesky(base+persistent),
                turn=np.linalg.cholesky(base+transient), both=np.linalg.cholesky(base+persistent+transient))


def gaussian(lower, samples):
    """Score each complete error vector, retaining covariance normalization."""
    import numpy as np
    from scipy.linalg import solve_triangular

    samples = np.asarray(samples, float)
    if (samples.ndim != 2 or not samples.size or samples.shape[1]%3
            or not np.isfinite(samples).all()):
        raise ValueError('finite samples of complete three-axis paths required')
    dimension = samples.shape[1]
    lower = _lower(lower, dimension)
    z = solve_triangular(lower, samples.T, lower=True, check_finite=False)
    quadratic = np.sum(z**2, axis=0)
    logdet = 2.*float(np.log(lower.diagonal()).sum())
    return dict(quadratic=quadratic, mean_standardized_error=quadratic/dimension,
                negative_log_score=.5*(quadratic+logdet+dimension*math.log(2.*math.pi)))


def seal(*, training_sha256, law, previous_time, times, anchor, mean, native_root, exposure):
    """Create the pre-score receipt from training output and available motion."""
    import numpy as np
    from .studies.artifacts import encoded

    time, anchor, mean, exposure = (np.asarray(a, float) for a in (times, anchor, mean, exposure))
    if (not isinstance(training_sha256, str) or not re.fullmatch('[0-9a-f]{64}', training_sha256)
            or law not in NATIVE_VARIANCE or time.ndim != 1 or not 1 <= len(time) <= MAX_REPORTS
            or mean.shape != (len(time), 3) or anchor.shape != (3,) or exposure.shape != time.shape
            or not math.isfinite(previous_time) or not previous_time < time[0] or np.any(np.diff(time) <= 0.)
            or not all(np.isfinite(a).all() for a in (time, anchor, mean, exposure)) or np.any(exposure < 0.)
            or abs(anchor[0]) >= np.pi/2-1e-6 or np.any(np.abs(mean[:, 0]) >= np.pi/2-1e-6)):
        raise ValueError('complete scoped training-only forecast and later timestamp support required')
    root = _lower(native_root, 3*len(time))
    return encoded(dict(policy=VERSION, training_sha256=training_sha256, law=law,
        previous_time=float(previous_time), times_s=time.tolist(), anchor_geodetic=anchor.tolist(),
        mean_geodetic=mean.tolist(), native_root_neu_m=root.tolist(), angular_exposure=exposure.tolist()))


def score_sealed(payload, *, expected_sha256, times, actual):
    import numpy as np
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .studies.artifacts import digest

    if digest(payload) != expected_sha256:
        raise ValueError('exact sealed forecast hash required before scoring')
    forecast = json.loads(payload)
    if forecast['policy'] != VERSION:
        raise ValueError('forecast uses a different frozen scoring rule')
    if not np.array_equal(np.asarray(times, float), forecast['times_s']):
        raise ValueError('original later receiver clock must match the sealed forecast')
    actual = np.asarray(actual, float)
    mean = np.asarray(forecast['mean_geodetic'])
    if (actual.shape != mean.shape or not np.isfinite(actual).all()
            or np.any(np.abs(actual[:, 0]) >= np.pi/2-1e-6)):
        raise ValueError('complete later receiver positions required')
    error = actual-mean
    error[:, 1] = longitude_residual(error[:, 1])
    error *= physical_metric([forecast['anchor_geodetic']])[0]
    roots = factors(times, previous_time=forecast['previous_time'], native_root=forecast['native_root_neu_m'],
                    exposure=forecast['angular_exposure'], law=forecast['law'])
    scores = {name: {key: float(values[0]) for key, values in gaussian(root, error.reshape(1, -1)).items()}
              for name, root in roots.items()}
    return dict(forecast_sha256=expected_sha256, training_sha256=forecast['training_sha256'], law=forecast['law'],
        physical_rms_neu_m=np.sqrt(np.mean(error**2, axis=0)).tolist(),
        horizontal_rms_m=float(np.sqrt(np.mean(np.sum(error[:, :2]**2, axis=1)))), scores=scores,
        receiver_used_for_training=False, aircraft_uncertainty_calibrated=False, scientific_decision='abstain')


def qualification(root, action):
    from .esa_fast_force_transfer import EARLIER
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import digest
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    raw = (root/EARLIER).read_bytes()
    if digest(raw) != SOURCE_SHA:
        raise ValueError('earlier native variance reference changed')
    prior = json.loads(raw)['by_sensor_law']
    if any(prior[law]['scores']['constant']['variance_scale'] != scale for law,scale in NATIVE_VARIANCE.items()):
        raise ValueError('fixed scales differ from the sealed earlier score')
    own = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (own, PLAN, TEST, EARLIER))
    environment = runtime_environment()
    if action == 'request':
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    req, report = checked(root, REQUEST, sources=sources, environment=environment,
                          required_tests=TEST_NAMES, minimum_tests=len(TEST_NAMES))
    return dict(request_sha256=digest(req), test_report_sha256=digest(report), tests=len(TEST_NAMES))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'verify'))
    print(json.dumps(qualification(Path.cwd(), parser.parse_args().action), sort_keys=True))
