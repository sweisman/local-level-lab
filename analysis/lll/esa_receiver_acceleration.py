# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only ESA receiver acceleration with temporal covariance sensitivity."""

import argparse
import json
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_RECEIVER_ACCELERATION_PLAN.md'
FREEZE = BASE+'esa-receiver-acceleration-freeze.json'
RESULT = BASE+'esa-receiver-acceleration-result.json'
WIDTHS = (11, 25)
GROUP_SIZE = 25
GRAVITY = 9.81
DRIFT_SCALE = .001


def velocity_weights(times, center):
    """Evaluate a local quadratic and its first derivative at the center."""
    import numpy as np

    delta = np.asarray(times, float)-center
    if (delta.ndim != 1 or len(delta) < 3 or not np.isfinite(delta).all()
            or np.any(np.diff(delta) <= 0) or not delta[0] < 0 < delta[-1]):
        raise ValueError('finite ordered velocity observations bracketing the evaluation required')
    scale = float(np.max(np.abs(delta)))
    time = delta/scale
    coefficients = np.linalg.pinv(np.column_stack((np.ones(len(time)), time, time**2)))
    return coefficients[0], coefficients[1]/scale


def scalar_sd(weights, covariance):
    """Independent SD and the sharp Cauchy-Schwarz upper SD with given marginals."""
    import numpy as np

    variances = np.einsum('ni,nij,nj->n', weights, covariance, weights)
    standard_deviations = np.sqrt(np.maximum(variances, 0.))
    return float(np.linalg.norm(standard_deviations)), float(standard_deviations.sum())


def force_and_gradient(velocity, acceleration, *, latitude_rad, height_m, gravity_mps2):
    """Reported-chart force magnitude and its acceleration and velocity derivatives."""
    import numpy as np
    from .ilvis0_forward import skew
    from .models import earth_rate_sphere, radii

    north, prime = radii(latitude_rad)
    transport = np.array([[0., 1./(prime+height_m), 0.], [-1./(north+height_m), 0., 0.],
                          [0., -np.tan(latitude_rad)/(prime+height_m), 0.]])
    turn = 2.*earth_rate_sphere(latitude_rad)+transport@velocity
    force = acceleration+np.cross(turn, velocity)-[0., 0., gravity_mps2]
    magnitude = float(np.linalg.norm(force))
    unit = force/magnitude
    velocity_jacobian = skew(turn)-skew(velocity)@transport
    return magnitude, unit, unit@velocity_jacobian


def summarize(rows):
    import numpy as np
    from .esa_gnss_covariance_audit import covariance_matrix

    if len(rows) != 800:
        raise ValueError('exact earlier window required')
    time = np.asarray([row['time_s'] for row in rows])
    velocity = np.asarray([[row[k] for k in ('north_mps', 'east_mps', 'up_mps')] for row in rows])
    orientation = np.array([1., 1., -1.])
    velocity *= orientation
    covariance = (np.asarray([covariance_matrix(row['velocity_covariance_export']) for row in rows])
                  * np.outer(orientation, orientation))
    tolerance = 64*np.finfo(float).eps*np.max(np.abs(covariance), axis=(1, 2))
    if (not np.isfinite(time).all() or np.any(np.abs(np.diff(time)-1.) > .02)
            or np.any(np.linalg.eigvalsh(covariance)[:, 0] < -tolerance)):
        raise ValueError('complete one-second reports and positive semidefinite velocity covariance required')
    result = []
    for center in range(GROUP_SIZE//2, len(rows), GROUP_SIZE):
        row = rows[center]
        latitude = np.deg2rad(row['latitude_deg'])
        cases = {}
        for width in WIDTHS:
            half = width//2
            subset = slice(center-half, center+half+1)
            value, derivative = velocity_weights(time[subset], time[center])
            v, a = value@velocity[subset], derivative@velocity[subset]
            force, grad_a, grad_v = force_and_gradient(v, a, latitude_rad=latitude,
                                                      height_m=row['height_m'], gravity_mps2=GRAVITY)
            full_weights = derivative[:, None]*grad_a+value[:, None]*grad_v
            independence, arbitrary = scalar_sd(full_weights, covariance[subset])
            cases[str(width)] = dict(acceleration_ned_m_s2=a.tolist(), velocity_ned_m_s=v.tolist(),
                force_magnitude_m_s2=force, reported_independent_sd_m_s2=independence,
                reported_arbitrary_correlation_upper_sd_m_s2=arbitrary)
        change = abs(cases[str(WIDTHS[0])]['force_magnitude_m_s2']-cases[str(WIDTHS[1])]['force_magnitude_m_s2'])
        result.append(dict(center_time_s=float(time[center]), center_sequence=row['sequence'],
            force_stencil_difference_m_s2=change, stencils=cases))
    return result


def run(root, action):
    from .airquantumgrav_inventory import METADATA, validate_context
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .receiver_route_information import SELECTION, SOURCE, _read_queries
    from .studies.artifacts import digest, encoded, safe_path
    from .studies.dependencies import source_closure

    raw = {key: (root/name).read_bytes() for key, name in METADATA.items()}
    metadata = {key: json.loads(value) for key, value in raw.items()}
    context = validate_context(**metadata)
    selection_bytes = (root/SELECTION).read_bytes()
    selection = json.loads(selection_bytes)['plan']
    windows = selection['windows']
    inventory = metadata['receiver_report']
    if (selection['fit_authorized'] is not False or selection['confirmation_authorized'] is not False
            or inventory['epochs'] != 64080 or len(windows) != 3
            or any(w['group_id'] != context['group_id']
                   or w['receiver_source_sha256'] != context['receiver_sha256'] for w in windows)):
        raise ValueError('exact opened flight and three prospectively selected training supports required')
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_receiver_acceleration.py')
    freeze = encoded(dict(selection_sha256=digest(selection_bytes), environment=runtime_environment(),
        metadata_hashes={name:digest(value) for name, value in raw.items()},
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
        block_size=GROUP_SIZE, widths=WIDTHS, gravity_m_s2=GRAVITY, drift_scale_m_s2=DRIFT_SCALE,
        expected_receiver_queries=2400, expected_estimates=192, later_queries=0, fit_starts=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('receiver acceleration sources or frozen definition changed')
    records = _read_queries(safe_path(root, SOURCE), windows, context['receiver_sha256'], inventory['epochs'])
    results = {label: summarize(rows) for label, rows in records.items()}
    estimates = sum(len(item['stencils']) for rows in results.values() for item in rows)
    if estimates != 192:
        raise ValueError('frozen derivative evaluation count differs')
    result = encoded(dict(freeze_sha256=digest(freeze), windows=results, receiver_queries=2400,
        derived_accelerations=estimates, later_queries=0, fit_starts=0, protected_reads=0,
        scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    return dict(sha256=digest(result), training_windows=len(results), derived_accelerations=estimates)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
