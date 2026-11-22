# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check ESA training acceleration from positions against the sealed velocity result."""

import argparse
import json
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_POSITION_ACCELERATION_PLAN.md'
FREEZE = BASE+'esa-position-acceleration-freeze.json'
RESULT = BASE+'esa-position-acceleration-result.json'
VELOCITY_SHA256 = 'ff594de9187e690c231dbfe2748444c0bb5da185034aac59931eb7efa3536aae'
DEGREE = 3


def from_positions(times, coordinates, covariance, *, center):
    """Return acceleration and linearized force covariance in one fixed chart."""
    import numpy as np
    from .esa_receiver_acceleration import GRAVITY, scalar_sd
    from .ilvis0_receiver_derivatives import LocalPolynomial
    from .ilvis0_receiver_force import evaluate
    from .ilvis0_solver_position import physical_metric
    from .models import OMEGA_E, WGS84_A

    chart = np.asarray(coordinates, float).copy()
    chart[:, 1] = np.unwrap(chart[:, 1])
    reference = chart[center].copy()
    physical_scales = physical_metric(chart)
    scale = physical_scales[center]
    ratio = scale/physical_scales
    chart_covariance = covariance*ratio[:, :, None]*ratio[:, None, :]
    tolerance = 64*np.finfo(float).eps*np.max(abs(chart_covariance), axis=(1, 2))
    if np.any(scale <= 0.) or np.any(np.linalg.eigvalsh(chart_covariance)[:, 0] < -tolerance):
        raise ValueError('positive local chart and semidefinite reported position covariance required')
    positions = (chart-reference)*scale
    operator = LocalPolynomial(times, times[center], np.eye(3*len(times)), degree=DEGREE, maximum_gap_s=1.02)
    estimate = operator.apply(positions)
    jet = np.r_[estimate['position'], estimate['rate'], estimate['acceleration']]

    def kinematics(point):
        position, rate, acceleration = (point/np.tile(scale, 3)).reshape(3, 3)
        return evaluate(reference+position, rate, acceleration, model='sphere_rotating',
                        background_rate_rads=OMEGA_E, gravity_mps2=GRAVITY, disc_radius_m=WGS84_A)

    def magnitude(point):
        return np.linalg.norm(kinematics(point)['specific_force_ned_mps2'])

    def gradient(steps):
        return np.asarray([(magnitude(jet+step)-magnitude(jet-step))/(2*width)
                           for step, width in zip(np.diag(steps), steps, strict=True)])

    steps = np.repeat([.1, .01, .001], 3)
    partial = gradient(steps/2.)
    if not np.allclose(partial, gradient(steps), rtol=1e-6, atol=1e-8):
        raise ValueError('force covariance derivative is sensitive to numerical step')
    weights = (partial@operator.weights).reshape(-1, 3)
    independent, arbitrary = scalar_sd(weights, chart_covariance)
    terms = kinematics(jet)
    return dict(velocity_ned_m_s=terms['velocity_ned_mps'].tolist(),
                acceleration_ned_m_s2=terms['acceleration_ned_mps2'].tolist(),
                force_magnitude_m_s2=float(np.linalg.norm(terms['specific_force_ned_mps2'])),
                reported_independent_sd_m_s2=independent, reported_arbitrary_correlation_upper_sd_m_s2=arbitrary)


def compare(rows, prior):
    import numpy as np
    from .esa_gnss_covariance_audit import covariance_matrix
    from .esa_receiver_acceleration import GROUP_SIZE, WIDTHS

    time = np.asarray([r['time_s'] for r in rows])
    coords = np.asarray([[r['latitude_deg'], r['longitude_deg'], r['height_m']] for r in rows])
    coords[:, :2] = np.deg2rad(coords[:, :2])
    covariance = np.asarray([covariance_matrix(r['position_variance_m2']+r['position_cross_covariance_m2'])
                             for r in rows])
    result = []
    for center, previous in zip(range(GROUP_SIZE//2, len(rows), GROUP_SIZE), prior, strict=True):
        if (rows[center]['sequence'] != previous['center_sequence'] or time[center] != previous['center_time_s']):
            raise ValueError('exact sealed position and velocity comparison centers required')
        stencils = {}
        for width in WIDTHS:
            half = width//2
            subset = slice(center-half, center+half+1)
            values = from_positions(time[subset], coords[subset], covariance[subset], center=half)
            from_velocity = previous['stencils'][str(width)]
            values['difference_from_velocity_m_s2'] = values['force_magnitude_m_s2']-from_velocity['force_magnitude_m_s2']
            values['velocity_comparison_sd_upper_m_s2'] = (values['reported_arbitrary_correlation_upper_sd_m_s2']
                                                          + from_velocity['reported_arbitrary_correlation_upper_sd_m_s2'])
            stencils[str(width)] = values
        small, large = (stencils[str(width)]['force_magnitude_m_s2'] for width in WIDTHS)
        result.append(dict(center_time_s=float(time[center]), center_sequence=rows[center]['sequence'],
                           force_stencil_difference_m_s2=abs(small-large), stencils=stencils))
    return result


def run(root, action):
    from .airquantumgrav_inventory import METADATA, validate_context
    from .esa_receiver_acceleration import RESULT as VELOCITY_RESULT, DRIFT_SCALE, GRAVITY, WIDTHS
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
    prior_bytes = (root/VELOCITY_RESULT).read_bytes()
    prior = json.loads(prior_bytes)['windows']
    if (digest(prior_bytes) != VELOCITY_SHA256 or selection['fit_authorized'] is not False
            or selection['confirmation_authorized'] is not False or inventory['epochs'] != 64080
            or len(windows) != 3 or set(prior) != {w['window_id'] for w in windows}
            or any(w['group_id'] != context['group_id']
                   or w['receiver_source_sha256'] != context['receiver_sha256'] for w in windows)):
        raise ValueError('exact opened flight, velocity result and three training supports required')
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_position_acceleration.py')
    freeze = encoded(dict(environment=runtime_environment(), selection_sha256=digest(selection_bytes),
        velocity_result_sha256=VELOCITY_SHA256, metadata_hashes={name:digest(data) for name, data in raw.items()},
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
        widths=WIDTHS, polynomial_degree=DEGREE, drift_reference_m_s2=DRIFT_SCALE, gravity_m_s2=GRAVITY,
        expected_receiver_queries=2400, expected_estimates=192, fit_starts=0, later_queries=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('position acceleration sources or frozen definition changed')
    records = _read_queries(safe_path(root, SOURCE), windows, context['receiver_sha256'], inventory['epochs'])
    results = {label: compare(rows, prior[label]) for label, rows in records.items()}
    estimates = sum(len(item['stencils']) for rows in results.values() for item in rows)
    if estimates != 192:
        raise ValueError('frozen derivative evaluation count differs')
    report = encoded(dict(freeze_sha256=digest(freeze), windows=results, receiver_queries=2400,
        derived_accelerations=estimates, fit_starts=0, later_queries=0, protected_reads=0,
        scientific_decision='abstain'))
    _write_equal(root/RESULT, report)
    return dict(sha256=digest(report), training_windows=len(results), derived_accelerations=estimates)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
