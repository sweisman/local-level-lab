# SPDX-License-Identifier: AGPL-3.0-or-later
"""Assumed correlated GPS-error sensitivity, never calibrated accuracy or Earth fitting."""
from dataclasses import dataclass
import csv
import gzip
import json
import math

import numpy as np

from . import gnss_position as gps, ilvis0 as il, ilvis0_gnss as exports

VERSION = 'ilvis0-gps-error-sensitivity-v1'
METHODS = ('l1_broadcast', 'dual_frequency')
WINDOW_SECONDS = (2., 6., 12., 30., 60.)
AXES = ('north', 'east', 'up')


@dataclass(frozen=True)
class Assumption:
    name: str
    noise_neu_m: tuple
    correlation_s: float
    offset_neu_m: tuple
    drift_neu_m: tuple

    def __post_init__(self):
        for values in (self.noise_neu_m, self.offset_neu_m, self.drift_neu_m):
            if len(values) != 3 or any(not math.isfinite(v) or v < 0 for v in values):
                raise ValueError('three finite nonnegative assumed scales required')
        if not math.isfinite(self.correlation_s) or self.correlation_s < 0:
            raise ValueError('finite nonnegative correlation time required')

    def report(self):
        return dict(name=self.name, noise_neu_m=list(self.noise_neu_m),
            correlation_s=self.correlation_s, offset_neu_m=list(self.offset_neu_m),
            drift_neu_m=list(self.drift_neu_m), calibrated=False,
            semantics='assumed standard deviations, not supported bounds or confidence coverage')


def assumptions():
    result = [Assumption('formal_only', (0.,)*3, 0., (0.,)*3, (0.,)*3)]
    for horizontal, vertical in ((1., 3.), (3., 10.), (10., 30.)):
        scales = (horizontal, horizontal, vertical)
        for tau in (0., 10., 60., 300.):
            result.append(Assumption(f'h{horizontal:g}_v{vertical:g}_tau{tau:g}',
                scales, tau, scales, scales))
    return tuple(result)


def times(values):
    t = np.asarray(values, float)
    if t.ndim != 1 or len(t) < 2 or not np.all(np.isfinite(t)) or np.any(np.diff(t) <= 0):
        raise ValueError('finite strictly increasing actual receiver epochs required')
    return t


def correlation(t, tau):
    t = times(t)
    if not math.isfinite(tau) or tau < 0:
        raise ValueError('invalid correlation time')
    return np.eye(len(t)) if tau == 0 else np.exp(-abs(t[:, None]-t[None, :])/tau)


def formal_blocks(values):
    blocks = np.asarray(values, float)
    if blocks.ndim != 3 or blocks.shape[1:] != (3, 3) or not np.all(np.isfinite(blocks)):
        raise ValueError('finite per-epoch covariance blocks required')
    if not np.allclose(blocks, blocks.transpose(0, 2, 1), rtol=1e-12, atol=1e-14):
        raise ValueError('symmetric formal covariance required')
    blocks = (blocks + blocks.transpose(0, 2, 1))/2
    if np.min(np.linalg.eigvalsh(blocks)) <= 0:
        raise ValueError('positive definite formal covariance required')
    return blocks


def weighted_covariance(weights, blocks, kernel, drift_fraction, assumption):
    """Covariance of a fixed linear summary, retaining NEU cross-axis formal terms.

    Added OU noise, common offset and linear drift are assumed independent of
    formal errors and each other. Their axes are independent in one fixed local
    frame. Offset is constant across the file; drift is zero at its first epoch
    and has the stated assumed standard deviation at its last epoch.
    """
    w = np.asarray(weights, float)
    b = np.asarray(blocks, float)
    u = np.asarray(drift_fraction, float)
    k = np.asarray(kernel, float)
    n = len(w)
    if w.shape != (n,) or b.shape != (n, 3, 3) or u.shape != (n,) or k.shape != (n, n):
        raise ValueError('weights/covariance/time shapes disagree')
    if not all(np.all(np.isfinite(a)) for a in (w, b, u, k)):
        raise ValueError('nonfinite sensitivity input')
    variance = np.einsum('i,ijk->jk', w*w, b)
    extra = (max(0., float(w@k@w))*np.square(assumption.noise_neu_m)
        + float(np.sum(w))**2*np.square(assumption.offset_neu_m)
        + float(w@u)**2*np.square(assumption.drift_neu_m))
    return variance + np.diag(extra)


def coordinate_covariance(t, latitudes, heights, blocks, assumption):
    """Optional dense coordinate covariance for controls, under WGS84 only.

    Coordinates are [latitude radians, longitude radians, ellipsoid height m].
    This is a conditional sensitivity input, never evidence satisfying an
    observed-fit receiver-covariance prerequisite. No model-specific weighting.
    """
    t = times(t); b = formal_blocks(blocks)
    phi = np.asarray(latitudes, float); h = np.asarray(heights, float)
    if len(b) != len(t) or phi.shape != t.shape or h.shape != t.shape:
        raise ValueError('coordinate covariance shapes disagree')
    if not np.all(np.isfinite(phi)) or not np.all(np.isfinite(h)) or np.any(abs(phi) >= math.pi/2):
        raise ValueError('finite nonpolar coordinates required')
    a, e2 = 6378137., 6.6943799901413165e-3
    denominator = 1-e2*np.sin(phi)**2
    meridian = a*(1-e2)/denominator**1.5 + h
    parallel = (a/np.sqrt(denominator)+h)*np.cos(phi)
    if np.any(meridian <= 0) or np.any(parallel <= 0):
        raise ValueError('invalid conventional coordinate metric')
    transform = np.column_stack((1/meridian, 1/parallel, np.ones(len(t)))).ravel()
    k = correlation(t, assumption.correlation_s)
    u = (t-t[0])/(t[-1]-t[0])
    covariance = np.kron(k, np.diag(np.square(assumption.noise_neu_m)))
    covariance += np.kron(np.ones_like(k), np.diag(np.square(assumption.offset_neu_m)))
    covariance += np.kron(np.outer(u, u), np.diag(np.square(assumption.drift_neu_m)))
    for i, block in enumerate(b):
        covariance[3*i:3*i+3, 3*i:3*i+3] += block
    return covariance*transform[:, None]*transform[None, :]


def quadratic_weights(t, center, span_s, maximum_gap_s=1.5):
    """Fixed ordinary quadratic least-squares derivatives at an actual epoch.

    Endpoints must span the requested duration. No interpolation, edge-window
    shortening, covariance-dependent smoothing or maneuver-based selection.
    """
    t = times(t)
    if not math.isfinite(span_s) or span_s <= 0 or maximum_gap_s <= 0:
        raise ValueError('positive window duration and gap allowance required')
    if center not in t:
        raise ValueError('center must be an actual epoch')
    indices = np.flatnonzero(abs(t-center) <= span_s/2+1e-7)
    if len(indices) < 3:
        return None, 'insufficient_epochs'
    local = t[indices]
    if local[0] > center-span_s/2+1e-7 or local[-1] < center+span_s/2-1e-7:
        return None, 'incomplete_window'
    if np.max(np.diff(local)) > maximum_gap_s:
        return None, 'receiver_gap'
    x = (local-center)/(span_s/2)
    design = np.column_stack((np.ones(len(x)), x, x*x))
    if np.linalg.matrix_rank(design) != 3:
        return None, 'rank_deficient'
    inverse = np.linalg.pinv(design)
    return (indices, inverse[1]/(span_s/2), 2*inverse[2]/(span_s/2)**2), None


def load_series(path, expected_hash, expected_epochs):
    if il.sha256(path) != expected_hash:
        raise ValueError('position export hash mismatch')
    result = {method: [] for method in METHODS}
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            if row['method'] not in result:
                raise ValueError('unsupported method')
            result[row['method']].append(row)
    keys = []
    for method, rows in result.items():
        if len(rows) != expected_epochs:
            raise ValueError('preselected epoch count mismatch')
        if any(row['status'] != 'converged' for row in rows):
            raise ValueError('unsupported failed epoch; no replacement or omission')
        key = [(row['gps_week'], row['gps_week_seconds']) for row in rows]
        absolute = np.array([week*604800.+second for week, second in key])
        times(absolute)
        keys.append(key)
    if keys[0] != keys[1]:
        raise ValueError('method epoch mismatch')
    return result, absolute-absolute[0]


def describe(values):
    values = np.asarray(values, float)
    return dict(samples=len(values), median=float(np.median(values)),
        p95=float(np.percentile(values, 95)), maximum=float(np.max(values)),
        rms=float(np.sqrt(np.mean(values**2)))) if len(values) else dict(samples=0)


def run_file(task, prior, directory, output):
    name = task['task_id']+'.positions.jsonl.gz'
    records, t = load_series(directory/name, prior['artifacts_sha256'][name], prior['preselected_epochs'])
    first = records[METHODS[0]][0]
    rotation = gps.local_rotation(first['latitude_rad'], first['longitude_rad'])
    origin = np.asarray(first['ecef_m'])
    positions = {}; blocks = {}
    for method, rows in records.items():
        positions[method] = (np.asarray([r['ecef_m'] for r in rows])-origin)@rotation.T
        transformed = []
        for row in rows:
            local = gps.local_rotation(row['latitude_rad'], row['longitude_rad'])
            change = rotation@local.T
            transformed.append(change@np.asarray(row['formal_covariance_neu_m2'])@change.T)
        blocks[method] = formal_blocks(transformed)
    grid = assumptions(); u = (t-t[0])/(t[-1]-t[0])
    kernels = {tau: correlation(t, tau) for tau in {a.correlation_s for a in grid}}
    means = []
    for method in METHODS:
        iid = weighted_covariance(np.ones(len(t))/len(t), blocks[method], kernels[0.], u, grid[0])
        for assumption in grid:
            covariance = weighted_covariance(np.ones(len(t))/len(t), blocks[method],
                kernels[assumption.correlation_s], u, assumption)
            means.append(dict(method=method, assumption=assumption.name,
                sigma_neu_m=np.sqrt(np.diag(covariance)).tolist(),
                sigma_ratio_to_formal_iid=np.sqrt(np.diag(covariance)/np.diag(iid)).tolist(),
                covariance_neu_m2=covariance.tolist()))
    trajectory_summaries = []; uncertainty_summaries = []; method_differences = []
    window_path = output/(task['task_id']+'.windows.csv.gz')
    columns = ('method', 'span_s', 'center_gps_elapsed_s', 'assumption', 'epochs',
        'velocity_north_mps', 'velocity_east_mps', 'velocity_up_mps',
        'acceleration_north_mps2', 'acceleration_east_mps2', 'acceleration_up_mps2',
        'velocity_sigma_north_mps', 'velocity_sigma_east_mps', 'velocity_sigma_up_mps',
        'acceleration_sigma_north_mps2', 'acceleration_sigma_east_mps2', 'acceleration_sigma_up_mps2')
    with exports.compressed_text(window_path) as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n'); writer.writeheader()
        for span in WINDOW_SECONDS:
            windows = []; rejected = {}
            for center in t:
                weights, reason = quadratic_weights(t, center, span)
                if weights is None:
                    rejected[reason] = rejected.get(reason, 0)+1
                else:
                    windows.append((center, *weights))
            values = {method: {'velocity': [], 'acceleration': []} for method in METHODS}
            uncertainties = {(method, a.name): {'velocity': [], 'acceleration': []}
                for method in METHODS for a in grid}
            for center, indices, velocity_w, acceleration_w in windows:
                for method in METHODS:
                    velocity = velocity_w@positions[method][indices]
                    acceleration = acceleration_w@positions[method][indices]
                    values[method]['velocity'].append(velocity)
                    values[method]['acceleration'].append(acceleration)
                    for assumption in grid:
                        kernel = kernels[assumption.correlation_s][np.ix_(indices, indices)]
                        variances = [weighted_covariance(w, blocks[method][indices], kernel,
                            u[indices], assumption) for w in (velocity_w, acceleration_w)]
                        sigma_v, sigma_a = [np.sqrt(np.maximum(0., np.diag(v))) for v in variances]
                        uncertainty = uncertainties[method, assumption.name]
                        uncertainty['velocity'].append(sigma_v); uncertainty['acceleration'].append(sigma_a)
                        row = dict(method=method, span_s=span, center_gps_elapsed_s=float(center),
                            assumption=assumption.name, epochs=len(indices))
                        for axis, label in enumerate(AXES):
                            row['velocity_'+label+'_mps'] = velocity[axis]
                            row['acceleration_'+label+'_mps2'] = acceleration[axis]
                            row['velocity_sigma_'+label+'_mps'] = sigma_v[axis]
                            row['acceleration_sigma_'+label+'_mps2'] = sigma_a[axis]
                        writer.writerow(row)
            for method in METHODS:
                trajectory_summaries.append(dict(method=method, span_s=span, supported=len(windows),
                    unsupported=rejected, summary_frame='fixed first-L1-epoch conventional NEU; motion context only',
                    **{kind+'_neu':{axis:describe(np.asarray(v)[:, i]) if v else dict(samples=0)
                        for i, axis in enumerate(AXES)} for kind, v in values[method].items()}))
                for assumption in grid:
                    uncertainty_summaries.append(dict(method=method, span_s=span, assumption=assumption.name,
                        **{kind+'_sigma_neu':{axis:describe(np.asarray(v)[:, i]) if v else dict(samples=0)
                            for i, axis in enumerate(AXES)}
                            for kind, v in uncertainties[method, assumption.name].items()}))
            for kind in ('velocity', 'acceleration'):
                delta = np.asarray(values[METHODS[1]][kind])-np.asarray(values[METHODS[0]][kind])
                method_differences.append(dict(span_s=span, quantity=kind,
                    difference_neu={axis:describe(delta[:, i]) if len(delta) else dict(samples=0)
                        for i, axis in enumerate(AXES)}))
    return dict(version=VERSION, task_id=task['task_id'], filename=task['filename'],
        source_sha256=task['source_sha256'], epochs=len(t), duration_s=float(t[-1]-t[0]),
        assumptions=[a.report() for a in grid], mean_position_sensitivity=means,
        trajectory_summaries=trajectory_summaries, uncertainty_summaries=uncertainty_summaries,
        method_derivative_differences=method_differences,
        artifacts_sha256={window_path.name:il.sha256(window_path)},
        covariance_calibrated=False, assumption_grid_bounds_supported=False,
        source_audit_errors=0, empirical_earth_fit_attempts=0, gnss_position_fits=0,
        scientific_eligibility_changes=0, originals_deleted=0,
        limitations=['grid is sensitivity, not a measured error bound or confidence claim',
            'conventional GPS/WGS84 reconstruction cannot establish Earth-shape evidence',
            'formal block correlations are retained; added error axes/components assumed independent',
            'quadratic windows attenuate real short motion; no smoothing timescale selected',
            'fixed local-frame derivatives include geometry and aircraft motion',
            'method differences share receiver errors, not external truth',
            'IMU processing/calibration/mounting/physical timing still unsupported'])
