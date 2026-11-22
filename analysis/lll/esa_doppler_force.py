# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched force magnitudes using Doppler and logged iMAR acceleration only."""
import argparse
from contextlib import closing
import fcntl
from functools import lru_cache
import gzip
import io
import json
import math
import os
from pathlib import Path
import platform

from . import models
from .compute_budget import environment
from .esa_doppler_comparison import MATCH_SHA, VELOCITY_FREEZE, VELOCITY_SHA
from .esa_doppler_study import DIRECTORY
from .esa_rinex_code_comparison import BASE, FOLDER, MATRIX, MATRIX_SHA, coordinates
from .gnss_position import local_rotation
from .ilvis0_receiver_force import FIELD_MODELS, MATCHED_MODELS, evaluate, evaluate_batch
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_DOPPLER_FORCE_PLAN.md'
REPORT = FOLDER+'esa-doppler-force-result.json'
GRAVITY = 9.81
GRAVITY_LAWS = ('fixed', 'height_dependent')
WIDTHS = (11, 25)
CENTERS = range(12, 400, 25)
CONTRASTS = (
    ('matched_field_shape', 'sphere_rotating', 'flat_geographic_field'),
    ('zero_field_shape', 'sphere_still', 'flat_still'),
    ('globe_field', 'sphere_rotating', 'sphere_still'),
)


def rate_operator(times):
    """Local quadratic velocity coefficients and its acceleration kernel."""
    import numpy as np

    t = np.asarray(times, float)
    if (t.ndim != 1 or len(t) < 3 or not np.all(np.isfinite(t))
            or not t[0] < 0 < t[-1] or np.any(np.diff(t) <= 0)):
        raise ValueError('ordered velocity support around the center required')
    scale = np.max(abs(t))
    operator = np.linalg.pinv(np.polynomial.polynomial.polyvander(t/scale, 2))/scale**np.arange(3)[:, None]
    # Since the derivative row has zero sum, each interval's contribution is
    # its acceleration integral times the sum of all subsequent sample weights.
    weights = np.cumsum(operator[1, :0:-1])[::-1]
    if np.min(weights) < -1e-10 or abs(weights@np.diff(t)-1.) > 1e-10:
        raise ValueError('nonnegative unit-mass acceleration kernel required')
    return operator, np.maximum(weights, 0.)


def matched_weights(samples, knots, kernel):
    import numpy as np

    if len(samples) < 2 or samples[0] > knots[0] or samples[-1] < knots[-1]:
        raise ValueError('inertial samples must bracket velocity support')
    primitive = np.r_[0., np.cumsum(kernel*np.diff(knots))]
    weights = np.diff(np.interp(samples, knots, primitive))
    if np.min(weights) < 0 or abs(weights.sum()-1.) > 1e-10:
        raise ValueError('inertial weights changed the receiver kernel mass')
    return weights


def coordinate_rates(coordinates, velocities):
    import numpy as np

    coordinates = np.asarray(coordinates, float)
    velocity = np.asarray(velocities, float)
    if (coordinates.shape != velocity.shape or coordinates.ndim != 2 or coordinates.shape[1] != 3
            or not np.all(np.isfinite(coordinates)) or not np.all(np.isfinite(velocity))):
        raise ValueError('matched coordinates and local velocities required')
    latitude, _, h = coordinates.T
    north, prime = models.radii(latitude)
    return velocity/np.column_stack((north+h, (prime+h)*np.cos(latitude), np.ones(len(h))))


@lru_cache(maxsize=1)
def _quadrature_rule():
    import numpy as np

    return np.polynomial.legendre.leggauss(4)


def _required_force_inputs(knots, kernel, center, coefficients, gravity, first_height):
    import numpy as np

    nodes, weights = _quadrature_rule()
    half = np.diff(knots)[:, None]/2.
    t = ((knots[:-1]+knots[1:])[:, None]/2.+half*nodes).ravel()
    quadrature = (half*weights*kernel[:, None]).ravel()
    polynomial = np.polynomial.polynomial
    position = np.asarray(center)+np.moveaxis(polynomial.polyval(t, polynomial.polyint(coefficients)), -1, -2)
    speed = np.moveaxis(polynomial.polyval(t, coefficients), -1, -2)
    acceleration = np.moveaxis(polynomial.polyval(t, polynomial.polyder(coefficients)), -1, -2)
    gravity_values = np.full(position.shape[:-1], GRAVITY)
    if gravity == 'height_dependent':
        gravity_values *= ((models.WGS84_A+first_height)/(models.WGS84_A+position[..., 2]))**2
    return position, speed, acceleration, gravity_values, quadrature


def predicted_force(knots, kernel, center, coefficients, model, gravity, first_height):
    import numpy as np

    position, speed, acceleration, gravity_values, quadrature = _required_force_inputs(
        knots, kernel, center, coefficients, gravity, first_height)
    rate = models.OMEGA_E if model in FIELD_MODELS else 0.
    required = [np.linalg.norm(evaluate(p, v, a, model=model, background_rate_rads=rate,
                gravity_mps2=g, disc_radius_m=models.WGS84_A)['specific_force_ned_mps2'])
                for p, v, a, g in zip(position, speed, acceleration, gravity_values, strict=True)]
    return float(quadrature@required)


def predicted_force_batch(knots, kernel, center, coefficients, model, gravity, first_height):
    """Use the same quadrature, with force evaluation batched across its nodes."""
    import numpy as np

    position, speed, acceleration, gravity_values, quadrature = _required_force_inputs(
        knots, kernel, center, coefficients, gravity, first_height)
    rate = models.OMEGA_E if model in FIELD_MODELS else 0.
    forces = evaluate_batch(position, speed, acceleration, model=model, background_rate_rads=rate,
                            gravity_mps2=gravity_values, disc_radius_m=models.WGS84_A)
    return float(quadrature@np.linalg.norm(forces['specific_force_ned_mps2'], axis=1))


def predicted_force_ensemble(knots, kernel, center, coefficients, model, gravity, first_height):
    """Evaluate the same force quadrature for several coefficient sets at once."""
    import numpy as np

    coefficients = np.asarray(coefficients, float)
    if coefficients.ndim != 3 or coefficients.shape[1:] != (3, 3) or not len(coefficients):
        raise ValueError('one or more quadratic three-axis velocity fits required')
    position, speed, acceleration, gravity_values, quadrature = _required_force_inputs(
        knots, kernel, center, np.moveaxis(coefficients, 1, 0), gravity, first_height)
    rate = models.OMEGA_E if model in FIELD_MODELS else 0.
    forces = evaluate_batch(position.reshape(-1, 3), speed.reshape(-1, 3), acceleration.reshape(-1, 3),
                            model=model, background_rate_rads=rate, gravity_mps2=gravity_values.ravel(),
                            disc_radius_m=models.WGS84_A)
    magnitudes = np.linalg.norm(forces['specific_force_ned_mps2'], axis=1)
    return magnitudes.reshape(gravity_values.shape)@quadrature


def paths(matrix, velocity, indices):
    import numpy as np

    report = json.loads(gzip.decompress(matrix.input('training', raw=True)))
    times = np.asarray([row['time_s'] for row in report], float)
    if (len(times) != 400 or len(indices) != 400 or indices != sorted(set(indices))
            or not 0 <= indices[0] < indices[-1] < len(velocity)
            or np.any(np.diff(times) <= 0)):
        raise ValueError('complete unchanged 400-row earlier support required')
    coord = np.asarray(coordinates(report))
    coord[:, 1] = np.unwrap(coord[:, 1])
    rotation = np.asarray([local_rotation(phi, longitude) for phi, longitude, _ in coord])
    vel = dict(export=[[row[key] for key in ('north_mps','east_mps','up_mps')] for row in report])
    selected = [velocity[i] for i in indices]
    if any(row['gps_week'] != ref['gps_week'] or abs(row['gps_week_seconds']-t) > .001
           for row, ref, t in zip(selected, report, times, strict=True)):
        raise ValueError('Doppler training query changed')
    for system in ('G', 'R'):
        if any(row[system]['status'] != 'converged' for row in selected):
            raise ValueError('every earlier Doppler velocity must be solved')
        vel[system] = np.einsum('ijk,ik->ij', rotation,
                               [row[system]['velocity_ecef_mps'] for row in selected])
    return times, coord, {name:coordinate_rates(coord, values) for name, values in vel.items()}


def imu_force(matrix):
    import numpy as np

    binding = matrix.input('saved-input-binding')
    if binding['source_id'] != 'esa-99f1530c3eda4318':
        raise ValueError('unchanged opened iMAR source required')
    with np.load(io.BytesIO(matrix.input('interval', raw=True)), allow_pickle=False) as archive:
        dt, dv = archive['dt'], archive['dv']
    if (dt.shape != (155868,) or dv.shape != (155868, 3) or np.any(dt <= 0)
            or np.any(dt > .005) or not np.all(np.isfinite(dv)) or not np.all(np.isfinite(dt))):
        raise ValueError('complete sealed iMAR increments and clock required')
    return binding['time_origin_s']+np.r_[0., np.cumsum(dt)], np.linalg.norm(dv, axis=1)/dt


def compare(matrix, velocity, indices):
    import numpy as np

    times, coord, rate_paths = paths(matrix, velocity, indices)
    imu_times, magnitude = imu_force(matrix)
    rows = {}
    summary = []
    def rms(values):
        values = np.asarray(values, float)
        return float(np.linalg.norm(values)/math.sqrt(len(values)))

    for width in WIDTHS:
        half = width//2
        observed, candidates = [], {name:{g:[] for g in GRAVITY_LAWS} for name in rate_paths}
        for center in CENTERS:
            window = slice(center-half, center+half+1)
            epochs = times[window]
            relative = epochs-times[center]
            operator, kernel = rate_operator(relative)
            first = np.searchsorted(imu_times, epochs[0], side='right')-1
            last = np.searchsorted(imu_times, epochs[-1], side='left')
            if not 0 <= first < last < len(imu_times):
                raise ValueError('sealed inertial record does not bracket fixed earlier stencil')
            weights = matched_weights(imu_times[first:last+1]-times[center], relative, kernel)
            observed.append(float(weights@magnitude[first:last]))
            for name, rates in rate_paths.items():
                fit = operator @ rates[window]
                for gravity in GRAVITY_LAWS:
                    candidates[name][gravity].append({model:predicted_force(relative, kernel,
                        coord[center], fit, model, gravity, coord[0, 2]) for model in MATCHED_MODELS})
        rows[width] = dict(observed_force_mps2=observed, required_force_mps2=candidates)
        for name in rate_paths:
            for law in GRAVITY_LAWS:
                expected = {m:np.asarray([row[m] for row in candidates[name][law]]) for m in MATCHED_MODELS}
                scores = {}
                for model, prediction in expected.items():
                    raw = np.asarray(observed)-prediction
                    offset = float(np.median(raw[:8]))
                    scores[model] = dict(earlier_offset_mps2=offset,
                        later_uncorrected_rms_mps2=rms(raw[8:]), later_corrected_rms_mps2=rms(raw[8:]-offset))
                contrasts = {}
                for contrast, model_a, model_b in CONTRASTS:
                    delta = expected[model_a]-expected[model_b]
                    contrasts[contrast] = dict(later_raw_rms_mps2=rms(delta[8:]),
                       later_offset_adjusted_rms_mps2=rms(delta[8:]-np.median(delta[:8])))
                receivers = {}
                for other in rate_paths:
                    if other == name:
                        continue
                    receivers[other] = {model:rms(expected[model][8:]-[
                        row[model] for row in candidates[other][law][8:]]) for model in MATCHED_MODELS}
                summary.append(dict(width_reports=width, source=name, gravity=law, models=scores,
                    contrasts=contrasts, receiver_disagreement_later_rms_mps2=receivers))
    return dict(centers_gps_s=times[list(CENTERS)].tolist(), rows=rows, summary=summary,
                gyro_samples_used=0, original_reads=0, reserved_reads=0, new_earth_model_fits=0,
                raw_disturbance_uncertainty_calibrated=False, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in threads.items()):
        raise ValueError('one numerical thread required')
    import numpy as np

    root = Path.cwd()
    folder = root/DIRECTORY
    velocity = json.loads(gzip.decompress((folder/'velocity.json.gz').read_bytes()))
    matched = json.loads((root/(BASE+'comparison.json')).read_bytes())
    if (velocity['velocity_sha256'] != VELOCITY_SHA
            or digest(encoded(velocity['velocity'])) != VELOCITY_SHA
            or velocity['freeze_sha256'] != VELOCITY_FREEZE
            or digest((folder/'freeze.json').read_bytes()) != VELOCITY_FREEZE
            or matched['result_sha256'] != MATCH_SHA or digest(encoded(matched['result'])) != MATCH_SHA):
        raise ValueError('exact sealed Doppler and matching sources required')
    with (folder/'force.lock').open('a') as lock, closing(ClosedStudy(root, MATRIX)) as matrix:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (matrix.completion['manifest_sha256'] != MATRIX_SHA
                or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('unchanged sealed development cut required')
        sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_doppler_force.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'esa_rinex_code_comparison.py','esa_doppler_comparison.py','gnss_position.py',
            'ilvis0_receiver_force.py','ilvis0_channel_controls.py','models.py','compute_budget.py',
            'studies/artifacts.py','studies/closed.py'))
        freeze = encoded(dict(inputs=dict(velocity=VELOCITY_SHA, match=MATCH_SHA, matrix=MATRIX_SHA),
            sources={str(path.relative_to(root)):digest(path.read_bytes()) for path in sources},
            environment=dict(python=platform.python_version(),numpy=np.__version__,
                os=platform.system(),arch=platform.machine(),threads=threads),
            maximum_inertial_intervals=155868, maximum_velocity_stencils=96,
            maximum_force_predictions=768, maximum_new_fits=0, observed_groups=['187']))
        binding = folder/'force-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding, freeze)
        if binding.read_bytes()!=freeze:
            raise ValueError('Doppler force freeze differs')
        if args.action=='freeze':
            print(digest(freeze))
            return
        output = root/REPORT
        if not output.exists():
            result = compare(matrix, velocity['velocity'], matched['result']['matched_code_indices'][:400])
            atomic(output, encoded(dict(freeze=json.loads(freeze), freeze_sha256=digest(freeze),
                result=result, result_sha256=digest(encoded(result)))))
        saved = json.loads(output.read_bytes())
        if (saved['freeze_sha256']!=digest(freeze) or digest(encoded(saved['freeze']))!=digest(freeze)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed force comparison differs')
        print(f'{len(saved["result"]["summary"])} settings, SHA-256 {saved["result_sha256"]}')


if __name__=='__main__':
    main()
