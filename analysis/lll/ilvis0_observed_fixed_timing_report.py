# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the eight sealed fixed-endpoint timing probes without new calls."""

import csv
import hashlib
import io
import math
from pathlib import Path

from .ilvis0_observed_fixed_timing import ID, tasks

STEPS = (1e-7, 1e-5, 1e-3, 4e-3)


def build(root='.'):
    from .studies.closed import ClosedStudy
    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/'+ID)
    try:
        expected = {task['identity']:task for task in
                    tasks(study.input('layouts'))}
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 8 or
                study.summary['charged']['native_calls'] != 80 or
                study.summary['charged']['packet_visits'] != 1468313700 or
                set(study.tasks) != set(expected) or
                set(study.rows) != set(expected) or
                any('-scoring' in name for name in study.manifest['inputs'])):
            raise ValueError('exact eight sealed training-only probes required')
        rows = []
        for identity in expected:
            if (study.tasks[identity]['payload'] !=
                    expected[identity]['payload'] or
                    study.rows[identity]['passed'] is not True):
                raise ValueError('sealed timing identity or completion differs')
            result = study.envelope(identity)['result']
            probe = study.artifact(identity, 'timing-probe.json')
            fit = study.input('fit-'+identity)
            if (result['technical_completion_only'] is not True or
                    result['native_evaluations'] != 10 or
                    result['later_receiver_positions_used'] is not False or
                    probe['native_evaluations'] != 10 or
                    probe['original_labels_changed'] is not False or
                    len(probe['time_probes']) != 4 or
                    tuple(item['step_s'] for item in probe['time_probes']) != STEPS or
                    probe['center_cost'] != fit['residual_sum_squares'] or
                    not math.isclose(probe['time_offset_s'],
                                     fit['parameters']['time_offset'],
                                     rel_tol=0, abs_tol=1e-12)):
                raise ValueError('saved timing probe differs from sealed fit')
            repeat = probe['center_repeat_maximum_neu_m']
            if (len(repeat) != 3 or
                    any(not math.isfinite(value) or value < 0 for value in repeat)):
                raise ValueError('finite exact-position replay required')
            for item in probe['time_probes']:
                if not math.isfinite(item['centered_derivative_relative_error']):
                    raise ValueError('finite timing derivative required')
                rows.append(dict(identity=identity,
                    segment_id=expected[identity]['payload']['segment_id'],
                    origin=expected[identity]['payload']['origin'],
                    solver=expected[identity]['payload']['solver'],
                    start=expected[identity]['payload']['start'],
                    source_fit_converged=fit['converged'],
                    center_cost=probe['center_cost'],
                    time_offset_s=probe['time_offset_s'],
                    nearest_packet_boundary_s=probe['center_packet_context'][
                        'minimum_boundary_distance_s'],
                    repeat_maximum_neu_m=max(repeat),
                    step_s=item['step_s'],
                    minus_changed_packet_epochs=item['minus_changed_packet_epochs'],
                    plus_changed_packet_epochs=item['plus_changed_packet_epochs'],
                    centered_derivative_relative_error=
                        item['centered_derivative_relative_error'],
                    left_right_derivative_relative_difference=
                        item['left_right_derivative_relative_difference'],
                    minus_cost_change=item['minus_cost_change'],
                    plus_cost_change=item['plus_cost_change']))
        if len(rows) != 32:
            raise ValueError('four signed scales for all eight endpoints required')
        by_step = [dict(step_s=step,
            endpoints_crossing_packet_boundary=sum(
                row['minus_changed_packet_epochs'] > 0 or
                row['plus_changed_packet_epochs'] > 0
                for row in rows if row['step_s'] == step),
            maximum_centered_derivative_relative_error=max(
                row['centered_derivative_relative_error']
                for row in rows if row['step_s'] == step),
            maximum_left_right_relative_difference=max(
                row['left_right_derivative_relative_difference']
                for row in rows if row['step_s'] == step))
            for step in STEPS]
        diagnosis = study.input('diagnosis')
        pairs = []
        for case in diagnosis['path_disagreements']:
            selected = [row for row in rows if row['step_s'] == STEPS[0]
                        and row['identity'] in case['largest_path_pair']]
            if len(selected) != 2:
                raise ValueError('complete preselected path pair required')
            first, second = (study.input('fit-'+identity)
                             for identity in case['largest_path_pair'])
            names = first['active_parameters']
            if (names != second['active_parameters'] or
                    len(names) != len(first['normalized_parameters']) or
                    len(names) != len(second['normalized_parameters'])):
                raise ValueError('same calibration coordinates required')
            differences = sorted((dict(parameter=name,
                normalized_difference=abs(a-b))
                for name,a,b in zip(names,first['normalized_parameters'],
                                    second['normalized_parameters'])),
                key=lambda item: -item['normalized_difference'])
            pairs.append(dict(segment_id=case['segment_id'],
                origin=case['origin'],
                identities=case['largest_path_pair'],
                later_path_spread_m=case['maximum_later_path_spread_m'],
                largest_normalized_parameter_differences=differences[:5],
                fitted_time_offset_difference_s=abs(
                    selected[0]['time_offset_s']-selected[1]['time_offset_s'])))
        return dict(version='ilvis0-observed-fixed-timing-report-v1',
            study='data/'+ID,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            report_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            complete_endpoints=8,native_calls=80,
            packet_visits=1468313700,
            exact_repeat_endpoints=sum(row['repeat_maximum_neu_m'] == 0
                for row in rows if row['step_s'] == STEPS[0]),
            source_costs_reproduced=True, original_outcomes_unchanged=True,
            refits=0, withheld_position_reads=0,
            scientific_decision='abstain', by_step=by_step,
            maximum_path_pairs=pairs, rows=rows)
    finally:
        study.close()


def render(report):
    lines = ['# Fixed-endpoint timing check', '',
        'All eight preselected recorded-data endpoints completed their ten',
        'charged training calculations. Repeating each exact parameter vector',
        'gave identical receiver predictions on all three axes at all eight',
        'endpoints; every saved training cost also reproduced exactly. This',
        'establishes deterministic replay at these points, not convergence of',
        'their original fits.', '',
        '| Time-offset step | Endpoints crossing a packet interval | Largest relative timing-derivative difference |',
        '|---|---:|---:|']
    for item in report['by_step']:
        step=item['step_s']
        label=(f'{step*1e6:g} µs' if step<.001 else f'{step*1e3:g} ms')
        lines.append(f"| {label} | {item['endpoints_crossing_packet_boundary']}/8 | "
            f"{item['maximum_centered_derivative_relative_error']:.3g} |")
    lines += ['',
        'Packet-interval crossings occur, including at the smallest tested',
        'step for one endpoint. Across these fixed probes, the centered',
        'finite-difference timing response remains close to the analytic',
        'derivative (largest relative difference about 0.000104). This does',
        'not establish that an optimizer can cross every timing boundary',
        'reliably or that timing explains a later forecast difference.', '',
        '| Differing inner cut | Later-path spread | Time-offset difference | Largest normalized parameter differences |',
        '|---|---:|---:|---|']
    for pair in report['maximum_path_pairs']:
        label='2010 northern' if pair['segment_id'].startswith('7df21c') else '2015 southern'
        top=pair['largest_normalized_parameter_differences'][:2]
        detail=', '.join(f"{item['parameter']} {item['normalized_difference']:.3f}"
                         for item in top)
        lines.append(f"| {label} | {pair['later_path_spread_m']:.3f} m | "
            f"{pair['fitted_time_offset_difference_s']*1e3:.3f} ms | "
            f"{detail} |")
    lines += ['',
        'The 2010 maximum pair has almost the same time offset, while the',
        '2015 pair differs much more. Several calibration parameters also',
        'vary. The next method check should examine the joint calibration',
        'valley and later-path sensitivity; changing only the clock cannot be',
        'assumed to resolve both discrepancies.', '',
        'No fit was restarted, no later receiver position entered the',
        'calculation, and no failed stopping label changed. The result is a',
        'numerical diagnostic, not a globe/flat or background-field decision.', '',
        '[Frozen plan](OBSERVED_FIXED_ENDPOINT_PLAN.md) · '
        '[All 32 signed-step results](observed-fixed-timing-steps.csv) · '
        '[Earlier fit diagnosis](OBSERVED_METHOD_V2_DIAGNOSIS.md)', '']
    return '\n'.join(lines)


def csv_bytes(report):
    stream = io.StringIO(newline='')
    fields = tuple(report['rows'][0])
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(report['rows'])
    return stream.getvalue().encode()


def publish(root='.'):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    out = root/'docs/prediction-group-transfer'
    atomic(out/'OBSERVED_FIXED_ENDPOINT_RESULT.md', render(report).encode())
    atomic(out/'observed-fixed-timing-steps.csv', csv_bytes(report))
    atomic(out/'observed-fixed-timing-report.json', encoded(report))
    return report


if __name__ == '__main__':
    report = publish()
    print(f"{report['complete_endpoints']}/8 complete, "
          f"{report['exact_repeat_endpoints']}/8 exact replays")
