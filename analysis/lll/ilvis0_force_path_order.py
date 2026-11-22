# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare quadratic and quartic estimates of the same recorded force windows."""

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path

import numpy as np
from numpy.polynomial.polynomial import polyder, polyval, polyvander

from . import ilvis0_carrier_force as carrier
from . import ilvis0_force_interval_calibration as calibration
from . import ilvis0_matched_force_average as average
from .ilvis0_control_shards import runtime_environment
from .ilvis0_force_bounds import _Box, force_bounds
from .ilvis0_gps_force_comparison import _matching_positions
from .ilvis0_receiver_force import evaluate
from .studies.artifacts import digest, encoded

FOLDER = carrier.FOLDER
SUPPORT = average.support
PLAN = FOLDER+'FORCE_PATH_ORDER_PLAN.md'
FREEZE = FOLDER+'force-path-order-freeze.json'
OUTPUT = FOLDER+'force-path-order-windows.json.gz'
RECEIPT = FOLDER+'force-path-order-receipt.json'
ORDERS = (2, 4)
QUADRATURE = 8
TRACKS = ('onboard', 'carrier_phase')
METHODS = ('quartic_bounds', 'quadratic_sampled', 'quartic_sampled')


def fit_path(offsets, coordinates, *, degree):
    time, coordinates = np.asarray(offsets, float), np.asarray(coordinates, float)
    if (degree not in ORDERS or time.ndim != 1 or len(time) <= degree
            or coordinates.shape != (len(time), 3) or not np.isfinite(coordinates).all()
            or not np.isfinite(time).all() or np.any(np.diff(time) <= 0.)
            or not time[0] <= 0. <= time[-1]):
        raise ValueError('common ordered support and a declared polynomial order required')
    scale = np.max(abs(time))
    design = polyvander(time/scale, degree)
    base = coordinates[np.argmin(abs(time))]
    coeff, _, rank, _ = np.linalg.lstsq(design, coordinates-base, rcond=None)
    if rank != degree+1:
        raise ValueError('receiver path polynomial is rank deficient')
    coeff[0] += base
    return coeff/(scale**np.arange(degree+1))[:, None]


def point_jet(coefficients, time):
    return np.array([polyval(time, polyder(coefficients, order)) for order in range(3)])


def coordinate_boxes(coefficients, left, right):
    interval = _Box(left, right)
    result = []
    for order in range(3):
        for axis in polyder(coefficients, order).T:
            value = _Box(axis[-1])
            for coefficient in reversed(axis[:-1]):
                value = value*interval+coefficient
            result.append((value.lo, value.hi))
    return np.asarray(result)


def mean_bounds(coefficients, support, *, subdivisions, offset, model, background_rate_rads,
                gravity_mps2, disc_radius_m):
    if not support[0] < support[1] or type(subdivisions) is not int or not 1 <= subdivisions <= 256 or offset < 0.:
        raise ValueError('contiguous finite time support required')
    integral = _Box(0.)
    edges = np.linspace(*support, subdivisions+1)
    translation = _Box(-offset, offset)
    for a, b in zip(edges[:-1], edges[1:], strict=True):
        time = _Box(a, b)+translation
        bounds = force_bounds(coordinate_boxes(coefficients, time.lo, time.hi), model=model,
            include_matched_disc=True, background_rate_bounds_rads=(background_rate_rads,)*2,
            gravity_bounds_mps2=(gravity_mps2,)*2, disc_radius_m=disc_radius_m)['magnitude_bounds_mps2']
        integral += _Box(*bounds)*(_Box(b)-_Box(a))
    result = integral/(_Box(support[1])-_Box(support[0]))
    return max(0., result.lo), result.hi


def _settings(model):
    return dict(model=model, background_rate_rads=average.rate(model),
        gravity_mps2=average.GRAVITY, disc_radius_m=average.RADIUS)


def _paths(root, raw, source, pairs):
    picks, stored, completion = _matching_positions(root)
    if completion != source['provenance']['code_completion']:
        raise ValueError('changed matched GPS position study')
    tracks = {r['segment_id']: stored[r['identity']] for r in picks}
    timestamps = {key: sorted(rows) for key, rows in tracks.items()}
    spans = {(r['segment_id'], r['gps_millisecond_tag']): r for r in
             average._table(raw[SUPPORT.WINDOWS]) if float(r['half_window_s']) == SUPPORT.HALF_WINDOW_S}
    originals = {(r['segment_id'], r['gps_millisecond_tag'], r['clock']): r for r in
                 average._table(raw[average.OUTPUT]) if r['gps_stream'] == 'onboard'}
    supported = [r for r in average._table(raw[SUPPORT.OUTPUT]) if r['state']=='supported']
    if len(supported) != average.WINDOW_COUNT or len(originals) != len(supported)*len(SUPPORT.CLOCKS):
        raise ValueError('changed matched trajectory support')
    for row in supported:
        key = row['segment_id'], row['gps_millisecond_tag']
        signal, target = key[0], int(key[1])
        span, all_tags = spans[key], timestamps[signal]
        lo, hi = int(span['first_used_tag']), int(span['last_used_tag'])
        tags = all_tags[all_tags.index(lo):all_tags.index(hi)+1]
        if len(tags) != int(span['sample_count']) or span['state'] != 'evaluated':
            raise ValueError('changed recorded receiver interval')
        onboard = np.array([tracks[signal][tag]['onboard'] for tag in tags])
        onboard[:, 1] = np.unwrap(onboard[:, 1])
        phase = carrier.centered_path(tags, target, tracks[signal][target]['onboard'], pairs[signal])
        prior = [originals[(*key, clock)] for clock in SUPPORT.CLOCKS]
        if any(p['side'] != row['side'] or p['imu_type'] != row['imu_type'] for p in prior):
            raise ValueError('changed training side or recorder')
        yield row, (np.asarray(tags)-target)/1000., (onboard, phase), prior


def build(root, raw, source, pairs, old_profiles):
    nodes, weights = np.polynomial.legendre.leggauss(QUADRATURE)
    profiles = defaultdict(list)
    rows = []
    for window, times, sources, priors in _paths(root, raw, source, pairs):
        imu, side = window['imu_type'], window['side']
        for track, coordinates in zip(TRACKS, sources, strict=True):
            poly = [fit_path(times, coordinates, degree=order) for order in ORDERS]
            height_rms = [float(np.sqrt(np.mean((polyval(times, coefficients[:, 2])-coordinates[:, 2])**2)))
                          for coefficients in poly]
            for previous in priors:
                clock = previous['clock']
                lo, hi = (float(previous[key]) for key in ('interval_start_s', 'interval_end_s'))
                times_at_nodes = (hi+lo)/2.+nodes*(hi-lo)/2.
                jets = [[point_jet(coefficients, t) for t in times_at_nodes] for coefficients in poly]
                observed = [float(window[clock+'_'+end+'_mps2']) for end in ('lower', 'upper')]
                results = {}
                for model in average.MATCHED_MODELS:
                    settings = _settings(model)
                    bounds = mean_bounds(poly[1], (lo, hi), subdivisions=average.SUBDIVISIONS,
                                         offset=SUPPORT.TIME_OFFSET_S, **settings)
                    nominal = [float(weights@np.array([np.linalg.norm(evaluate(*jet, **settings)
                        ['specific_force_ned_mps2']) for jet in values])/2.) for values in jets]
                    if not bounds[0] <= nominal[1] <= bounds[1]:
                        raise ValueError('sampled quartic mean outside its interval enclosure')
                    results[model] = dict(quartic_bounds_mps2=bounds, nominal_mean_mps2=nominal)
                    for method, predicted in zip(METHODS, (bounds, (nominal[0],)*2, (nominal[1],)*2), strict=True):
                        for scope in (track, 'both'):
                            profiles[imu, model, scope, method, side].append((*observed, *predicted))
                rows.append(dict(segment_id=window['segment_id'], gps_millisecond_tag=int(window['gps_millisecond_tag']),
                    imu_type=imu, side=side, clock=clock, track=track, height_fit_rms_m=height_rms, models=results))
    if len(rows) != average.WINDOW_COUNT*len(TRACKS)*len(SUPPORT.CLOCKS):
        raise ValueError('incomplete path order comparison')
    reports = []
    for prior in old_profiles:
        imu, model, scope = (prior[k] for k in ('imu_type', 'model', 'receiver_scope'))
        assessments = {}
        for method in METHODS:
            prefix = imu, model, scope, method
            earlier, later = (profiles[(*prefix, side)] for side in ('training', 'later'))
            if len(earlier) != prior['training_cases'] or len(later) != prior['later_cases']:
                raise ValueError('changed prior training or later case count')
            assessments[method] = calibration.profile(earlier, later)
        reports.append(dict(imu_type=imu, model=model, receiver_scope=scope,
                            archived_quadratic_bounds=prior, **assessments))
    return rows, reports


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    raw, source, _, pairs = carrier._checked_inputs(root)
    raw.update(calibration._inputs(root))
    saved = {path: (root/path).read_bytes() for path in (calibration.FREEZE, calibration.RECEIPT)}
    previous = json.loads(saved[calibration.RECEIPT])
    if (previous['freeze_sha256'] != digest(saved[calibration.FREEZE])
            or previous['imu_fit_starts'] or len(previous['profiles']) != 24):
        raise ValueError('original two-sided calibration profiles required')
    raw.update(saved)
    own = Path(__file__).relative_to(root).as_posix()
    dependencies = source_closure(root, (own, PLAN, 'analysis/tests/test_ilvis0_force_path_order.py'))
    config = encoded(dict(inputs={p: digest(value) for p, value in raw.items()},
        sources={p: digest((root/p).read_bytes()) for p in dependencies}, environment=runtime_environment(),
        windows=average.WINDOW_COUNT, degrees=ORDERS, quadrature_nodes=QUADRATURE,
        maximum_interval_evaluations=126848, maximum_point_evaluations=253696,
        profiles=len(previous['profiles'])*len(METHODS), threads=1, imu_fit_starts=0))
    if args.action == 'freeze':
        SUPPORT._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('changed path order calculation freeze')
    rows, profiles = build(root, raw, source, pairs, previous['profiles'])
    payload = gzip.compress(encoded(rows), mtime=0)
    result = dict(freeze_sha256=digest(config), output_sha256=digest(payload),
        scenarios=len(rows), profiles=profiles, imu_fit_starts=0, scientific_decision='abstain')
    SUPPORT._write_equal(root/OUTPUT, payload)
    SUPPORT._write_equal(root/RECEIPT, encoded(result))
    print(json.dumps(dict(scenarios=len(rows), profiles=len(profiles)*len(METHODS), output_sha256=digest(payload))))


if __name__ == '__main__':
    main()
