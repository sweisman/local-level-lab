# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional shared GPS covariance of packet-averaged force predictions."""

import argparse
import csv
import gzip
import io
import json
from pathlib import Path
import platform

import numpy as np

from . import ilvis0_matched_force_average as average
from .ilvis0_error_model import Spec
from .ilvis0_force_magnitude_covariance import _gradient
from .ilvis0_solver_position import physical_metric
from .ilvis0_structured_force_projection import project_covariance
from .studies.artifacts import digest, encoded


support = average.support
SOURCE = 'analysis/lll/ilvis0_matched_force_covariance.py'
TEST = 'analysis/tests/test_ilvis0_matched_force_covariance.py'
PLAN = support.FOLDER+'MATCHED_FORCE_COVARIANCE_PLAN.md'
FREEZE = support.FOLDER+'matched-force-covariance-freeze.json'
OUTPUT = support.FOLDER+'matched-force-covariance-windows.csv.gz'
RESULT = support.FOLDER+'matched-force-covariance-receipt.json'
MODELS = average.MATCHED_MODELS
CONTRASTS = tuple((label+'_shape', MODELS.index(globe), MODELS.index(disc))
                  for label, globe, disc in average.FIELDS)
LABELS = tuple((clock, model) for clock in support.CLOCKS
               for model in (*MODELS, *(label for label, _, _ in CONTRASTS)))
SIDES = ('training', 'later')
WHITE_SIGMA = (.3, .3, .7)
SHARED_SIGMA = (1., 1., 3.)
TAU_S = 60.
NODES, QUADRATURE_WEIGHTS = np.polynomial.legendre.leggauss(4)


def mean_gradient(jet, interval, **model):
    """Differentiate the quadrature through the exact quadratic jet shift."""
    position, rate, acceleration = np.asarray(jet, float)
    a, b = interval
    if not a < b:
        raise ValueError('positive packet interval required')
    derivative = np.zeros((3, 3))
    for node, weight in zip(NODES, QUADRATURE_WEIGHTS, strict=True):
        time = (a+b)/2.+(b-a)/2.*node
        at_time = np.r_[position+time*rate+.5*time*time*acceleration, rate+time*acceleration, acceleration]
        p, v, acc = _gradient(at_time, **model).reshape((3, 3))
        derivative += .5*weight*np.stack((p, v+time*p, acc+time*v+.5*time*time*p))
    return derivative


def weights_for_interval(jet, weights, interval):
    """Keep force and direct contrast weights on the same receiver errors."""
    result = []
    for model in MODELS:
        g = mean_gradient(jet, interval, model=model, background_rate_rads=average.rate(model),
                          gravity_mps2=average.GRAVITY, disc_radius_m=average.RADIUS)
        result.append((weights.T @ g).ravel())
    return np.asarray(result + [result[i]-result[j] for _, i, j in CONTRASTS])


def _projection(record, packet_rows, gps_rows, intervals):
    t, tags = record['times'], record['tags']
    coords = record['coordinates']['onboard']
    metric = physical_metric(coords)
    transforms = np.eye(3)[None, :, :]/metric[:, :, None]
    shared = np.diag(np.square(SHARED_SIGMA))
    law = Spec(np.diag(np.square(WHITE_SIGMA)), ((TAU_S, shared),), shared, shared, t[0], t[-1]-t[0])
    aggregate = np.zeros((len(SIDES), len(LABELS), 3*len(t)))
    independent = np.zeros((len(SIDES), len(LABELS)))
    counts = np.zeros(len(SIDES), dtype=int)
    windows = []
    for window in packet_rows:
        tag = window['gps_millisecond_tag']
        gps = gps_rows[tag]
        start, stop = int(gps['first_used_tag']), int(gps['last_used_tag'])
        lo, hi = int(np.searchsorted(tags, start)), int(np.searchsorted(tags, stop, side='right'))
        target = int(np.searchsorted(tags, int(tag)))
        if (not lo <= target < hi or tags[lo] != start or tags[hi-1] != stop
                or tags[target] != int(tag) or hi-lo != int(gps['sample_count'])
                or lo < record['cut'] < hi or window['side'] != ('training' if hi <= record['cut'] else 'later')):
            raise ValueError('changed window or training support')
        weights = average.quadratic_weights((tags[lo:hi]-tags[target])/1000.)
        local = coords[lo:hi].copy()
        local[:, 1] = np.unwrap(local[:, 1])
        jet = weights @ local
        blocks = []
        for clock in support.CLOCKS:
            bounds = intervals[tag, clock]
            if bounds['side'] != window['side']:
                raise ValueError('changed averaged interval split')
            interval = (float(bounds['interval_start_s']), float(bounds['interval_end_s']))
            blocks.append(weights_for_interval(jet, weights, interval))
        matrix = np.vstack(blocks)
        cov = project_covariance(t[lo:hi], law, matrix, transforms=transforms[lo:hi])
        variances = np.diag(cov)
        if np.any(variances < 0.):
            raise ValueError('negative projected force variance')
        side = SIDES.index(window['side'])
        counts[side] += 1
        aggregate[side, :, 3*lo:3*hi] += matrix
        independent[side] += variances
        row = {key: window[key] for key in ('segment_id', 'imu_type', 'gps_millisecond_tag', 'side')}
        row.update({clock+'_'+candidate+'_sigma_mps2': float(sigma)
                    for (clock, candidate), sigma in zip(LABELS, np.sqrt(variances), strict=True)})
        windows.append(row)
    if np.any(counts == 0):
        raise ValueError('both declared receiver splits must have support')
    aggregate /= counts[:, None, None]
    independent /= counts[:, None]**2
    covariance = project_covariance(t, law, aggregate.reshape((-1, 3*len(t))), transforms=transforms)
    return windows, dict(counts=counts.tolist(), aggregate_covariance_mps4=covariance.tolist(),
        independent_window_variances_mps4=independent.ravel().tolist())


def _source_receipts(raw):
    for stage in (support, average):
        seal = json.loads(raw[stage.RESULT])
        if (digest(raw[stage.OUTPUT]) != seal['output_sha256']
                or digest(raw[stage.FREEZE]) != seal['freeze_sha256'] or seal['fit_starts']):
            raise ValueError('unchanged recorded support and average receipts required')


def build(earlier, raw):
    _source_receipts(raw)
    packet_rows = [row for row in average._table(raw[support.OUTPUT]) if row['state']=='supported']
    gps_rows = {(row['segment_id'], row['gps_millisecond_tag']): row
                for row in average._table(raw[support.WINDOWS]) if float(row['half_window_s'])==support.HALF_WINDOW_S}
    interval_rows = {(row['segment_id'], row['gps_millisecond_tag'], row['clock']): row
                     for row in average._table(raw[average.OUTPUT]) if row['gps_stream']=='onboard'}
    if len(packet_rows) != average.WINDOW_COUNT or len(interval_rows) != average.WINDOW_COUNT*len(support.CLOCKS):
        raise ValueError('changed recorded covariance allowance')
    windows, summaries = [], []
    for case in earlier['recordings']:
        identity = case['segment_id']
        selected = [row for row in packet_rows if row['segment_id']==identity]
        gps = {tag: row for (case_id, tag), row in gps_rows.items() if case_id==identity}
        intervals = {(tag, clock): row for (case_id, tag, clock), row in interval_rows.items() if case_id==identity}
        results, summary = _projection(average._record(case, raw), selected, gps, intervals)
        median = {clock+'_'+label: float(np.median([row[clock+'_'+label+'_sigma_mps2'] for row in results]))
                  for clock, label in LABELS}
        summaries.append(dict(segment_id=identity, imu_type=case['imu_type'],
                              median_window_sigma_mps2=median, **summary))
        windows.extend(results)
    if len(windows) != average.WINDOW_COUNT:
        raise ValueError('missing projected windows')
    return windows, summaries


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    earlier, raw = support._inputs(root)
    raw.update({path:(root/path).read_bytes() for stage in (support, average)
                for path in (stage.OUTPUT, stage.FREEZE, stage.RESULT)})
    config = encoded(dict(inputs={path: digest(value) for path, value in raw.items()},
        sources={path: digest((root/path).read_bytes()) for path in source_closure(root, (SOURCE, PLAN, TEST))},
        python=platform.python_version(), numpy=np.__version__, machine=platform.machine(), threads=1,
        windows=average.WINDOW_COUNT, force_mean_gradients=average.WINDOW_COUNT*len(MODELS)*len(support.CLOCKS),
        gradient_nodes=len(NODES), white_sigma_m=WHITE_SIGMA, shared_sigma_m=SHARED_SIGMA, correlation_s=TAU_S))
    if args.action=='freeze':
        support._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes()!=config:
        raise ValueError('receiver covariance comparison differs from its freeze')
    rows, summaries = build(earlier, raw)
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    data = gzip.compress(text.getvalue().encode(), mtime=0)
    receipt = dict(freeze_sha256=digest(config), output_sha256=digest(data), windows=len(rows),
        summaries=summaries, aggregate_order=[(side, clock, label) for side in SIDES for clock, label in LABELS],
        calibration_estimated=False, receiver_covariance_calibrated=False, fit_starts=0, scientific_decision='abstain')
    support._write_equal(root/OUTPUT, data)
    support._write_equal(root/RESULT, encoded(receipt))
    print(json.dumps(dict(windows=len(rows), output_sha256=digest(data), freeze_sha256=digest(config))))


if __name__ == '__main__':
    main()
