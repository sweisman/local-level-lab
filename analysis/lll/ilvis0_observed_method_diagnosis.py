# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed recorded-data stopping probes without fitting or native calls."""

import hashlib
import math
from collections import Counter
from pathlib import Path

from . import ilvis0_observed_method_report_v2 as pilot
from .ilvis0_solver_position import POLICY as POSITION
from .ilvis0_solver_refinement import POLICY as STOPPING


def failed_gates(case):
    """Classify the frozen stopping rule; never change the saved outcome."""
    if case['converged'] is True:
        return ()
    if case['probe_reason'] == 'not_stationary':
        return ('stationarity_before_probe',)
    if case['probe_reason'] != 'fresh_position_probe_not_stable':
        raise ValueError('unknown saved nonstopping reason')
    cost = case['probe_actual_cost_change']
    stationarity = case['fresh_stationarity']
    rms = case['position_probe_rms_m']
    maximum = case['position_probe_max_m']
    if (not all(isinstance(value, (int, float)) and math.isfinite(value)
                for value in (cost, stationarity)) or
            len(rms) != 3 or len(maximum) != 3 or
            not all(isinstance(value, (int, float)) and math.isfinite(value)
                    for value in (*rms, *maximum))):
        raise ValueError('complete finite saved probe required')
    gates = []
    if cost > STOPPING['relative_cost_tolerance']:
        gates.append('relative_cost_change')
    if stationarity > STOPPING['stationarity_tolerance']:
        gates.append('fresh_stationarity')
    if max(rms) > POSITION['position_rms_tolerance_m']:
        gates.append('position_rms')
    if max(maximum) > POSITION['position_max_tolerance_m']:
        gates.append('position_maximum')
    if not gates:
        raise ValueError('saved failed fit has no failed original gate')
    return tuple(gates)


def build(root='.'):
    root = Path(root).resolve()
    saved = pilot.build(root)
    if (saved['tasks'] != 24 or saved['technical_failures'] != 0 or
            saved['numerical_stops'] != 7 or len(saved['task_rows']) != 24 or
            len(saved['cut_rows']) != 6):
        raise ValueError('exact sealed 24-fit observed pilot required')
    gates = Counter()
    reasons = Counter()
    cost_only = 0
    passing = []
    for case in saved['task_rows']:
        failed = failed_gates(case)
        if case['converged']:
            passing.append(case)
            continue
        reasons[case['probe_reason']] += 1
        gates.update(failed)
        cost_only += failed == ('relative_cost_change',)
    if sum(reasons.values()) != 17 or sum(reasons.values()) + len(passing) != 24:
        raise ValueError('observed pilot stopping population differs')
    spreads = [row for row in saved['cut_rows']
               if row['maximum_later_path_spread_m'] > .1]
    cut_timing = []
    for cut in saved['cut_rows']:
        matched = [case for case in saved['task_rows']
                   if (case['segment_id'], case['origin']) ==
                      (cut['segment_id'], cut['origin'])]
        if len(matched) != 4:
            raise ValueError('four sealed fits required per receiver cut')
        offsets = [case['parameters']['time_offset'] for case in matched]
        cut_timing.append(dict(segment_id=cut['segment_id'], origin=cut['origin'],
            maximum_later_path_spread_m=cut['maximum_later_path_spread_m'],
            time_offset_spread_s=max(offsets)-min(offsets)))
    bounds = ('gyro_bias_z', 'gyro_gain_z', 'gravity_delta')
    return dict(version='ilvis0-observed-method-diagnosis-v1',
        study=saved['study'], manifest_sha256=saved['manifest_sha256'],
        summary_sha256=saved['summary_sha256'],
        pilot_report_source_sha256=saved['source_sha256'],
        diagnosis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_outcomes_unchanged=True, refits=0, native_calls=0,
        scientific_decision='abstain', numerical_stops=len(passing),
        nonstopping_reasons=dict(sorted(reasons.items())),
        failed_gates=dict(sorted(gates.items())), cost_only_failures=cost_only,
        passing_fit_common_active_bounds=[bound for bound in bounds
            if all(bound in case['active_bounds'] for case in passing)],
        passing_later_horizontal_rms_range_m=[min(
            case['prediction_horizontal_rms_m'] for case in passing),max(
            case['prediction_horizontal_rms_m'] for case in passing)],
        passing_later_vertical_rms_range_m=[min(
            case['prediction_vertical_rms_m'] for case in passing),max(
            case['prediction_vertical_rms_m'] for case in passing)],
        cut_timing=cut_timing,
        path_disagreements=[{key:row[key] for key in
            ('segment_id', 'origin', 'maximum_later_path_spread_m',
             'training_cost_range', 'largest_path_pair')} for row in spreads])


def publish(root='.'):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    result = build(root)
    atomic(root/'docs/prediction-group-transfer/observed-method-v2-diagnosis.json',
           encoded(result))
    return result


if __name__ == '__main__':
    result = publish()
    print(f"{result['numerical_stops']}/24 numerical stops; "
          f"{result['cost_only_failures']} cost-only failures; "
          f"{len(result['path_disagreements'])}/6 differing paths")
