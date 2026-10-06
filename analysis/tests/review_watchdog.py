# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic oracle crab correction on saved bins; never an operational decision rule."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from lll import slip
from lll.analyze import _clean
from lll.synth import CAL_SEQUENCES, wind_velocity


def review(report):
    if report.get('partition') != 'development' or not report.get('replay') or report.get('state') != 'complete':
        raise ValueError('requires completed development diagnostic replays')
    results = []
    for row in report['cases']:
        inputs = row['watchdog_inputs']
        bins = {key: np.asarray(value) for key, value in inputs['bins'].items()}
        simulator = row['design']['simulator']
        # Match the recorded simulator timeline, including its 1,000-second elapsed-clock origin.
        flight_start = 1000.+simulator['gap_s']
        if 'pre' in simulator['cal']:
            flight_start += sum(simulator['cal_pos_s']*multiple+20. for _, multiple in CAL_SEQUENCES[simulator['cal_sequence']])
        flight_start += simulator['reversal_pairs']*2*(simulator['reversal_s']+20.)
        if simulator['drift_runs']: flight_start += 1800.
        if simulator['wind_ne_mps'] is not None:
            _, _, heading = wind_velocity(bins['psi'], bins['t']-flight_start,
                simulator['wind_airspeed_mps'] or simulator['speed'], simulator['wind_ne_mps'],
                simulator['wind_rate_ne_mps_per_h'])
            bins['psi'] = heading
        corrected = slip.watchdog(bins, inputs['hard_iron'], inputs['year'], inputs['max_slip_dph'])
        original = row['slip']
        results.append(dict(case=row['case'], original_excluded=original['exclude_segments'],
            oracle_heading_excluded=corrected['exclude_segments'], oracle_watchdog=corrected,
            original_geometry=row['pre_exclusion_geometry'], selected_fits=row['fits']))
    return _clean(dict(partition='development', replay=True, mode='known simulator wind oracle; magnetic bins only',
        source_implementation_hash=report['implementation_hash'], cases=results,
        limitations=['Uses injected wind unavailable to operational analysis.',
            'Does not remove magnetic noise or imperfect airframe-field calibration.',
            'Does not change exclusions, thresholds or flight eligibility.',
            'Eight paired replays are neither fresh calibration nor independent validation.']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('-o', type=Path, required=True)
    args = parser.parse_args()
    result = review(json.loads(args.report.read_text()))
    result['source_report_sha256'] = hashlib.sha256(args.report.read_bytes()).hexdigest()
    result['review_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.o.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps([dict(case=row['case'], original=row['original_excluded'],
        oracle=row['oracle_heading_excluded']) for row in result['cases']]))


if __name__ == '__main__':
    main()
