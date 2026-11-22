# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary within-packet direction rates for the saved force comparisons."""

import argparse
from collections import defaultdict
import gzip
import json
import math
from pathlib import Path

import numpy as np

from . import ilvis0_force_interval_calibration as calibration
from . import ilvis0_force_path_order as order
from .ilvis0_control_shards import runtime_environment
from .studies.artifacts import digest, encoded

FOLDER = order.FOLDER
SUPPORT = order.SUPPORT
AVERAGE = order.average
CARRIER = order.carrier
GAIN_CAP = calibration.gain.GAIN_CAP
FORCE_TOL_MPS2 = calibration.ROUNDING_MPS2
RATE_TOL_RADS = 1e-10
PERIOD_LIMIT_S = {'nominal_200Hz': .005, 'header_elapsed': SUPPORT.MAX_INTERVAL}
PLAN = FOLDER+'FORCE_DIRECTION_GAP_PLAN.md'
FREEZE = FOLDER+'force-direction-gap-freeze.json'
RECEIPT = FOLDER+'force-direction-gap-receipt.json'


def required_rate(packet_upper, predicted_lower, period):
    """Invert the conservative midpoint-cone upper bound in radians per second."""
    if not all(math.isfinite(value) and value > 0 for value in (packet_upper, predicted_lower, period)):
        raise ValueError('positive finite force and period bounds required')
    if packet_upper >= predicted_lower:
        return 0.
    return 2.*math.acos(packet_upper/predicted_lower)/period


def _side(rows, gain):
    values = calibration._rows([row[:4] for row in rows])
    l, u, low, high = values
    scale = 1.+gain
    required = [required_rate(float(packet/scale), float(candidate), row[4])
                for packet, candidate, row in zip(u, low, rows, strict=True)]
    lower_fails = l > high*scale+FORCE_TOL_MPS2
    return required, int(np.count_nonzero(lower_fails))


def compare(training, later):
    earlier_shape = calibration._rows([row[:4] for row in training])
    l, _, _, high = earlier_shape
    minimum_gain = max(0., float(np.max(l/high-1.)))
    base = dict(training_gain=minimum_gain, gain_cap_exceeded=minimum_gain > GAIN_CAP,
                training_cases=len(training), later_cases=len(later))
    if minimum_gain > GAIN_CAP:
        return dict(base, training_required_rate_rads=None, later_required_rate_rads=None,
                    later_exceeds_training_rate=None, later_lower_bound_failures=None)
    earlier, train_failed = _side(training, minimum_gain)
    held, later_failed = _side(later, minimum_gain)
    if train_failed:
        raise ValueError('training gain does not satisfy its lower-bound constraint')
    limit = max(earlier)
    return dict(base, training_required_rate_rads=limit, later_required_rate_rads=max(held),
        training_cases_requiring_motion=sum(rate > 0. for rate in earlier),
        later_exceeds_training_rate=sum(rate > limit+RATE_TOL_RADS for rate in held),
        later_lower_bound_failures=later_failed)


def _inputs(root):
    raw = calibration._inputs(root)
    raw.update({p: (root/p).read_bytes() for p in (order.FREEZE, order.RECEIPT, order.OUTPUT)})
    receipt = json.loads(raw[order.RECEIPT])
    if (receipt['freeze_sha256'] != digest(raw[order.FREEZE])
            or receipt['output_sha256'] != digest(raw[order.OUTPUT])
            or receipt['scenarios'] != 3964 or receipt['imu_fit_starts']):
        raise ValueError('unchanged archived path order calculation required')
    return raw


def build(raw):
    samples = {(r['segment_id'], int(r['gps_millisecond_tag'])): r
               for r in AVERAGE._table(raw[SUPPORT.OUTPUT]) if r['state']=='supported'}
    onboard = {(r['segment_id'], int(r['gps_millisecond_tag']), r['clock']): r for r in
               AVERAGE._table(raw[AVERAGE.OUTPUT]) if r['gps_stream']=='onboard'}
    rows = json.loads(gzip.decompress(raw[order.OUTPUT]))
    phase = {(r['segment_id'], r['gps_millisecond_tag'], r['clock']): r for r in
             json.loads(gzip.decompress(raw[CARRIER.OUTPUT]))}
    expected = {(key, track) for key in onboard for track in order.TRACKS}
    if (len(samples) != AVERAGE.WINDOW_COUNT or set(phase) != set(onboard)
            or len(rows) != len(expected) or len(rows) != 3964):
        raise ValueError('changed common path, packet or clock inventory')
    seen = set()
    profiles = defaultdict(list)
    for row in rows:
        clock, track, side, imu = (row[k] for k in ('clock', 'track', 'side', 'imu_type'))
        key = row['segment_id'], row['gps_millisecond_tag'], clock
        token = (key, track)
        if token not in expected or token in seen or samples[key[:2]]['side'] != side:
            raise ValueError('duplicate or mismatched trajectory time support')
        measured = samples[key[:2]]
        if any(prior[key]['side'] != side or prior[key]['imu_type'] != imu for prior in (onboard, phase)):
            raise ValueError('changed training split or recorder')
        seen.add(token)
        l, h = (float(measured[clock+'_'+end+'_mps2']) for end in ('lower', 'upper'))
        for model in AVERAGE.MATCHED_MODELS:
            if track == 'onboard':
                quad = [float(onboard[key][model+'_'+end+'_mps2']) for end in ('lower', 'upper')]
            else:
                quad = phase[key]['bounds_mps2'][model]
            quart = row['models'][model]['quartic_bounds_mps2']
            for degree, (a, b) in zip(order.ORDERS, (quad, quart), strict=True):
                for scope in (track, 'both'):
                    profiles[imu, model, degree, scope, side].append((l, h, a, b, PERIOD_LIMIT_S[clock]))
    if seen != expected:
        raise ValueError('incomplete paired direction profile')
    return [dict(imu_type=imu, model=model, degree=degree, receiver_scope=scope,
                 **compare(profiles[imu, model, degree, scope, 'training'],
                           profiles[imu, model, degree, scope, 'later']))
            for imu in ('8', '21') for model in AVERAGE.MATCHED_MODELS
            for degree in order.ORDERS for scope in calibration.SCOPES]


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    raw = _inputs(root)
    own = Path(__file__).relative_to(root).as_posix()
    deps = source_closure(root, (own, PLAN, 'analysis/tests/test_ilvis0_force_direction_gap.py'))
    config = encoded(dict(inputs={p: digest(value) for p, value in raw.items()},
        sources={p: digest((root/p).read_bytes()) for p in deps}, environment=runtime_environment(),
        gain_cap=GAIN_CAP, period_ceiling_s=PERIOD_LIMIT_S, profiles=48,
        maximum_window_clock_track_rows=3964, threads=1, imu_fit_starts=0, position_solves=0))
    if args.action == 'freeze':
        SUPPORT._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('changed force-direction calculation freeze')
    results = build(raw)
    receipt = dict(freeze_sha256=digest(config), profiles=results,
        imu_fit_starts=0, gyro_observations_used=False, direction_measured=False,
        scientific_decision='abstain')
    SUPPORT._write_equal(root/RECEIPT, encoded(receipt))
    rates = [row['training_required_rate_rads'] for row in results if not row['gain_cap_exceeded']]
    print(json.dumps(dict(profiles=len(results), feasible_training_lower_bounds=len(rates),
        least_training_rate_rads=min(rates, default=None), greatest_training_rate_rads=max(rates, default=None))))


if __name__ == '__main__':
    main()
