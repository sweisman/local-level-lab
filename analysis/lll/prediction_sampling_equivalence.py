# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only white-noise comparison for the prepared ESA development cadence."""
import hashlib
import io
import json
import math
import platform
from pathlib import Path


def variance_ratio(intervals, *, rate_hz):
    """Point-endpoint / independent-increment variance for an accumulated path.

    The two settings have point-rate standard deviation q/sqrt(1/rate_hz),
    where q is the increment law's white amplitude per square-root second.
    This ratio concerns white errors only; it is not an observation model fit.
    """
    import numpy as np
    if type(rate_hz) is not int or rate_hz < 1:
        raise ValueError('positive declared sampling rate required')
    dt = np.asarray(intervals, dtype=float)
    if (dt.ndim != 1 or not 1 <= len(dt) <= 360028 or
            not np.all(np.isfinite(dt)) or np.any(dt <= 0) or
            np.any(dt > 1.5 / rate_hz)):
        raise ValueError('finite supported packet intervals required')
    weights = np.empty(len(dt) + 1)
    weights[0] = dt[0] / 2
    weights[-1] = dt[-1] / 2
    weights[1:-1] = (dt[:-1] + dt[1:]) / 2
    ratio = float(np.sum(weights * weights) / ((1 / rate_hz) * np.sum(dt)))
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError('representable accumulated variance required')
    return ratio


def audit(root):
    """Open only sealed timing artifacts and declared synthetic settings."""
    import numpy as np
    from .airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
    from .studies.closed import ClosedStudy
    root = Path(root).resolve()
    study = ClosedStudy(root, 'docs/esa-development-pilot-preparation')
    try:
        if (study.summary.get('state') != 'complete' or
                study.completion.get('state') != 'complete'):
            raise ValueError('closed verified ESA preparation required')
        identity = 'prepare-earliest-187-v2'
        interval_bytes = study.artifact(identity, 'interval.npz', raw=True)
        layout_bytes = study.artifact(identity, 'query-layout.json', raw=True)
    finally:
        study.close()
    layout = json.loads(layout_bytes)
    if (layout.get('sampling_hypothesis') != 'linear_points' or
            layout.get('training_epochs') != 800 or
            layout.get('prediction_epochs') != 400 or
            layout.get('maximum_interval_s') != 0.005):
        raise ValueError('expected frozen development preparation required')
    with np.load(io.BytesIO(interval_bytes)) as archive:
        dt = np.array(archive['dt'], dtype=float, copy=True)
        raw_time = np.array(archive['raw_time_s'], dtype=float, copy=True)
    if (len(dt) != 360028 or len(raw_time) != len(dt) + 1 or
            not np.array_equal(np.diff(raw_time), dt)):
        raise ValueError('complete exact prepared packet timing required')
    queries = np.asarray(layout['times_s'], dtype=float)
    if (queries.shape != (1200,) or not np.all(np.isfinite(queries)) or
            np.any(np.diff(queries) <= 0)):
        raise ValueError('complete ordered frozen receiver query layout required')
    cutoff = int(np.searchsorted(np.cumsum(dt), queries[799], side='right'))
    if not 1 <= cutoff < len(dt):
        raise ValueError('earlier-only timing support required')
    earlier = dt[:cutoff]
    increment = noise_settings(seed=71)
    point = rate_point_noise_settings(seed=71)
    nominal_dt = 1 / 300
    for increment_key, point_key in (
            ('gyro_white_rads_per_sqrt_s', 'gyro_point_std_rads'),
            ('accel_white_mps_per_sqrt_s', 'accel_point_std_mps2')):
        if not math.isclose(point[point_key],
                            increment[increment_key] / math.sqrt(nominal_dt),
                            rel_tol=1e-12, abs_tol=0):
            raise ValueError('candidate white-noise scale relation changed')
    source = Path(__file__).read_bytes()
    plan = (root/'docs/prediction-paired-law/SAMPLING_PLAN.md').read_bytes()
    return dict(version='prediction-sampling-equivalence-v1',
                prepared_study='docs/esa-development-pilot-preparation',
                prepared_identity=identity,
                interval_sha256=hashlib.sha256(interval_bytes).hexdigest(),
                layout_sha256=hashlib.sha256(layout_bytes).hexdigest(),
                source_sha256=hashlib.sha256(source).hexdigest(),
                plan_sha256=hashlib.sha256(plan).hexdigest(),
                python=platform.python_version(), numpy=np.__version__,
                nominal_rate_hz=300, earlier_intervals=len(earlier),
                earlier_duration_s=float(np.sum(earlier)),
                min_dt_s=float(np.min(earlier)),
                median_dt_s=float(np.median(earlier)),
                max_dt_s=float(np.max(earlier)),
                point_to_increment_accumulated_white_variance_ratio=
                    variance_ratio(earlier, rate_hz=300),
                fixed_law_settings_scale_relation_verified=True,
                receiver_positions_read=False, original_reads=0,
                protected_reads=0, optimizer_starts=0, native_calls=0,
                error_law_identified=False, coverage_calibrated=False,
                scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    result = audit(root)
    output = root/'docs/prediction-paired-law'
    ratio = result['point_to_increment_accumulated_white_variance_ratio']
    lines = [
        '# Sampling comparison', '',
        f"The {result['earlier_intervals']:,} packet intervals before the last "
        'training receiver fix cover '
        f"{result['earlier_duration_s']:.2f} seconds. Their durations range from "
        f"{result['min_dt_s']:.9f} to {result['max_dt_s']:.9f} seconds.", '',
        f'For these timestamps, the point-endpoint law has {ratio:.9f} times '
        'the accumulated white-noise variance of the independent-increment law.',
        'Both frozen gyro and acceleration settings use the same nominal '
        '300 Hz long-run white-noise scale. Endpoint sharing changes the '
        'short-lag structure, but actual packet-timing variation here does '
        'not create a meaningful difference in accumulated white noise.', '',
        'This is a calculation from verified packet times and declared '
        'synthetic settings, **not an estimate of actual IMU noise**. It '
        'does not explain every model-fit result or qualify prediction '
        'coverage. Testing an error law would require independent evidence '
        'about high-frequency sensor error or a different sampling design. '
        'Until then, carry both laws when assessing forecasts.', '',
        '[Calculation plan](SAMPLING_PLAN.md) · '
        '[Paired-fit result](RESULT.md) · '
        '[Error-law roadmap](../PREDICTION_ERROR_LAW_PLAN.md).', '']
    atomic(output/'sampling-audit.json', encoded(result))
    atomic(output/'SAMPLING.md', '\n'.join(lines).encode())
    return dict(earlier_intervals=result['earlier_intervals'], ratio=ratio)
