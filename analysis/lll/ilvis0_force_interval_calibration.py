# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two-sided, training-only scalar force calibration on fixed GPS windows."""

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path

import numpy as np

from . import ilvis0_carrier_force as carrier
from . import ilvis0_matched_force_average as average, ilvis0_matched_force_gain as gain
from .ilvis0_control_shards import runtime_environment
from .studies.artifacts import digest, encoded

FOLDER = carrier.FOLDER
SUPPORT = average.support
PLAN = FOLDER+'FORCE_INTERVAL_CALIBRATION_PLAN.md'
FREEZE = FOLDER+'force-interval-calibration-freeze.json'
RECEIPT = FOLDER+'force-interval-calibration-receipt.json'
INPUTS = (carrier.FREEZE, carrier.RECEIPT, carrier.OUTPUT, average.FREEZE,
          average.RESULT, average.OUTPUT, SUPPORT.FREEZE, SUPPORT.RESULT, SUPPORT.OUTPUT)
SCOPES = ('onboard', 'carrier_phase', 'both')
BISECTION_STEPS = 52
ROUNDING_MPS2 = 1e-12


def _rows(values):
    rows = np.asarray(values, dtype=float)
    if (rows.ndim != 2 or rows.shape[1] != 4 or not len(rows)
            or not np.isfinite(rows).all() or np.min(rows) <= 0.
            or np.any(rows[:, 0] > rows[:, 1]) or np.any(rows[:, 2] > rows[:, 3])):
        raise ValueError('nonempty ordered positive force intervals required')
    return rows.T


def _errors(rows, correction):
    measured_lo, measured_hi, predicted_lo, predicted_hi = rows
    scale = 1.+correction
    return measured_lo-scale*predicted_hi, scale*predicted_lo-measured_hi


def profile(training, later):
    """Minimize the maximum gap with a single gain, then score without refitting."""
    train, heldout = _rows(training), _rows(later)
    measured_lo, measured_hi, predicted_lo, predicted_hi = train
    feasible_lo = max(0., float(np.max(measured_lo/predicted_hi-1.)))
    feasible_hi = min(gain.GAIN_CAP, float(np.min(measured_hi/predicted_lo-1.)))
    feasible = [feasible_lo, feasible_hi] if feasible_lo <= feasible_hi else None

    def extrema(correction):
        left, right = _errors(train, correction)
        return float(np.max(left)), float(np.max(right))

    if feasible is not None:
        correction, minimum_lower = feasible_lo, 0.
    else:
        lo, hi = 0., gain.GAIN_CAP
        low_gap, high_gap = extrema(lo)
        cap_low, cap_high = extrema(hi)
        if low_gap <= high_gap:
            correction, minimum_lower = lo, max(0., high_gap)
        elif cap_low >= cap_high:
            correction, minimum_lower = hi, max(0., cap_low)
        else:
            for _ in range(BISECTION_STEPS):
                middle = (lo+hi)/2.
                left, right = extrema(middle)
                if left > right:
                    lo = middle
                else:
                    hi = middle
            minimum_lower = max(0., extrema(hi)[0], extrema(lo)[1])
            correction = min((lo, hi), key=lambda value: max(0., *extrema(value)))
    training_gap = max(0., *extrema(correction))
    if feasible is not None and training_gap <= ROUNDING_MPS2:
        training_gap = 0.
    later_gap = np.maximum(0., np.maximum(*_errors(heldout, correction)))
    exceeded = later_gap > training_gap+ROUNDING_MPS2
    return dict(gain=correction, zero_error_training_gain_interval=feasible,
        training_cases=len(training), later_cases=len(later),
        training_error_mps2=training_gap, training_optimum_lower_mps2=min(minimum_lower, training_gap),
        later_error_mps2=float(np.max(later_gap)),
        later_outside_training_error=int(np.count_nonzero(exceeded)))


def _inputs(root):
    raw = {p: (root/p).read_bytes() for p in INPUTS}
    for freeze, receipt, output in ((carrier.FREEZE, carrier.RECEIPT, carrier.OUTPUT),
                                     (average.FREEZE, average.RESULT, average.OUTPUT),
                                     (SUPPORT.FREEZE, SUPPORT.RESULT, SUPPORT.OUTPUT)):
        sealed = json.loads(raw[receipt])
        if (digest(raw[freeze]) != sealed['freeze_sha256'] or digest(raw[output]) != sealed['output_sha256']
                or sealed.get('imu_fit_starts', sealed.get('fit_starts')) != 0):
            raise ValueError('changed archived force intervals')
    return raw


def build(raw):
    count = average.WINDOW_COUNT
    windows = {(r['segment_id'], int(r['gps_millisecond_tag'])): r
              for r in average._table(raw[SUPPORT.OUTPUT]) if r['state']=='supported'}
    onboard = {(r['segment_id'], int(r['gps_millisecond_tag']), r['clock']): r
               for r in average._table(raw[average.OUTPUT]) if r['gps_stream']=='onboard'}
    phase = json.loads(gzip.decompress(raw[carrier.OUTPUT]))
    if len(windows) != count or len(onboard) != count*len(SUPPORT.CLOCKS) or len(phase) != len(onboard):
        raise ValueError('changed number of matched force windows')
    cases = defaultdict(list)
    seen = set()
    for row in phase:
        base = row['segment_id'], row['gps_millisecond_tag']
        clock, side, imu = row['clock'], row['side'], row['imu_type']
        key = (*base, clock)
        original, measured = onboard[key], windows[base]
        if (key in seen or clock not in SUPPORT.CLOCKS or side not in ('training', 'later')
                or side != original['side'] or side != measured['side']
                or imu != measured['imu_type'] or imu != original['imu_type']
                or row['interval_s'] != [float(original[name]) for name in ('interval_start_s', 'interval_end_s')]):
            raise ValueError('force intervals must share window, recorder, clock and split')
        seen.add(key)
        observed = [float(measured[clock+'_'+end+'_mps2']) for end in ('lower', 'upper')]
        for model in average.MATCHED_MODELS:
            on = [float(original[model+'_'+end+'_mps2']) for end in ('lower', 'upper')]
            ph = row['bounds_mps2'][model]
            for name, bounds in zip(SCOPES, ((on,), (ph,), (on, ph)), strict=True):
                cases[imu, model, name, side].extend((*observed, *values) for values in bounds)
    if set(onboard) != seen:
        raise ValueError('incomplete clock and window support')
    return [dict(imu_type=imu, model=model, receiver_scope=name,
                 **profile(cases[imu, model, name, 'training'], cases[imu, model, name, 'later']))
            for imu in ('8', '21') for model in average.MATCHED_MODELS for name in SCOPES]


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    raw = _inputs(root)
    source = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (source, PLAN, 'analysis/tests/test_ilvis0_force_interval_calibration.py'))
    config = encoded(dict(inputs={p: digest(value) for p, value in raw.items()},
        sources={p: digest((root/p).read_bytes()) for p in sources}, environment=runtime_environment(),
        gain_bounds=[0., gain.GAIN_CAP], window_allowance=average.WINDOW_COUNT,
        profiles=24, maximum_bisection_steps_per_profile=BISECTION_STEPS,
        threads=1, imu_fit_starts=0, position_solves=0))
    if args.action == 'freeze':
        SUPPORT._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('changed force interval calibration freeze')
    rows = build(raw)
    result = dict(freeze_sha256=digest(config), profiles=rows, imu_fit_starts=0,
        receiver_error_calibrated=False, gyro_observations_used=False, scientific_decision='abstain')
    SUPPORT._write_equal(root/RECEIPT, encoded(result))
    print(json.dumps(dict(freeze_sha256=digest(config), profiles=len(rows),
        overlaps=sum(row['zero_error_training_gain_interval'] is not None for row in rows),
        minimum_training_error_mps2=min(row['training_error_mps2'] for row in rows),
        maximum_training_error_mps2=max(row['training_error_mps2'] for row in rows)), sort_keys=True))


if __name__ == '__main__':
    main()
