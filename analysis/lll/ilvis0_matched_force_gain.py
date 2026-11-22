# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score a shared training-only gain against held-out force lower bounds."""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import platform

from . import ilvis0_matched_force_average as average
from .ilvis0_matched_force_support import FOLDER, _write_equal
from .studies.artifacts import digest, encoded


SOURCE = 'analysis/lll/ilvis0_matched_force_gain.py'
TEST = 'analysis/tests/test_ilvis0_matched_force_gain.py'
PLAN = FOLDER+'MATCHED_FORCE_GAIN_PLAN.md'
FREEZE = FOLDER+'matched-force-gain-freeze.json'
RESULT = FOLDER+'matched-force-gain-receipt.json'
GAIN_CAP = .15
MAX_CASES = 23_784


def _violation(rows, gain):
    excess = [max(0., low/(1.+gain)-math.nextafter(high, math.inf)) for low, high in rows]
    return sum(value > 0. for value in excess), max(excess)


def compare(training, later):
    if (not training or not later
            or any(not math.isfinite(low) or not math.isfinite(high) or low < 0. or high <= 0.
                   for side in (training, later) for low, high in side)):
        raise ValueError('positive predicted bounds and training and later packet support required')
    required = max(0., max(low/high-1. for low, high in training))
    feasible = required <= GAIN_CAP
    # Widen the normalization at equality so computing the quotient again
    # does not report a floating-point residue as a physical violation.
    gain = min(GAIN_CAP, math.nextafter(required, math.inf)) if feasible and required else required
    misses, excess = _violation(later, gain) if feasible else (None, None)
    return dict(training_cases=len(training), later_cases=len(later),
        zero_gain_training_violations=_violation(training, 0.)[0],
        zero_gain_later_violations=_violation(later, 0.)[0],
        required_training_gain=required, training_feasible=feasible,
        training_gain=gain if feasible else None,
        fitted_training_violations=_violation(training, gain)[0] if feasible else None,
        later_violations=misses, maximum_later_excess_mps2=excess)


def build(raw):
    support = average.support
    for study in (support, average):
        receipt = json.loads(raw[study.RESULT])
        if (receipt['output_sha256'] != digest(raw[study.OUTPUT])
                or receipt['freeze_sha256'] != digest(raw[study.FREEZE]) or receipt['fit_starts']):
            raise ValueError('changed force table or prior calculation receipt')
    packets = {(row['segment_id'], row['gps_millisecond_tag']): row
               for row in average._table(raw[support.OUTPUT]) if row['state']=='supported'}
    if len(packets) != average.WINDOW_COUNT:
        raise ValueError('exact recorded support required')
    cases = defaultdict(lambda: dict(training=[], later=[]))
    seen = set()
    for row in average._table(raw[average.OUTPUT]):
        key = row['segment_id'], row['gps_millisecond_tag']
        scope = key+(row['clock'], row['gps_stream'])
        if (scope in seen or len(seen)*len(average.MATCHED_MODELS) >= MAX_CASES
                or row['clock'] not in support.CLOCKS or row['gps_stream'] not in average.TRACKS):
            raise ValueError('unexpected force averaging case')
        seen.add(scope)
        observed = packets[key]
        if row['imu_type'] != observed['imu_type'] or row['side'] != observed['side']:
            raise ValueError('changed training and later split')
        low = float(observed[row['clock']+'_lower_mps2'])
        for model in average.MATCHED_MODELS:
            high = float(row[model+'_upper_mps2'])
            cases[row['imu_type'], model][row['side']].append((low, high))
    if len(seen)*len(average.MATCHED_MODELS) != MAX_CASES or len(cases) != 8:
        raise ValueError('incomplete gain comparison')
    return [dict(imu_type=imu, model=model, **compare(sides['training'], sides['later']))
            for (imu, model), sides in sorted(cases.items())]


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    stages = (average.support, average)
    raw = {path: (root/path).read_bytes() for stage in stages
           for path in (stage.OUTPUT, stage.RESULT, stage.FREEZE)}
    config = encoded(dict(input_sha256={path: digest(value) for path, value in raw.items()},
        sources={path: digest((root/path).read_bytes()) for path in source_closure(root, (SOURCE, PLAN, TEST))},
        python=platform.python_version(), gain_cap=GAIN_CAP, maximum_cases=MAX_CASES, threads=1,
        physical_optimizations=0))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
    else:
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('gain comparison differs from its freeze')
        result = dict(freeze_sha256=digest(config), model_cases=MAX_CASES,
            gain_cap=GAIN_CAP, by_recorder_model=build(raw), gyro_observations_used=False,
            absolute_fit_qualified=False, scientific_decision='abstain')
        _write_equal(root/RESULT, encoded(result))
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
