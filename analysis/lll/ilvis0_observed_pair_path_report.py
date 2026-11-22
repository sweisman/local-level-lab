# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only cost and forecast report for complete calibration-vector paths."""

import csv
import hashlib
import io
from pathlib import Path

import numpy as np

from .ilvis0_fixed_vector_evaluation import interpolate
from .ilvis0_observed_calibration_swap import ID as PARENT_ID
from .ilvis0_observed_calibration_swap_report import (
    build as parent_report, later_distance_m,
)
from .ilvis0_observed_pair_path import ID, NORTH, SOUTH, tasks


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    previous=parent_report(root)
    study=ClosedStudy(root,'data/'+ID)
    parent=ClosedStudy(root,'data/'+PARENT_ID)
    try:
        expected={task['identity']:task for task in tasks(study.input('layouts'))}
        if (study.completion['state']!='complete' or
                study.summary['completed']!=6 or
                study.summary['charged']['native_calls']!=12 or
                study.summary['charged']['packet_visits']!=220247055 or
                set(study.tasks)!=set(expected) or
                set(study.rows)!=set(expected) or
                previous['manifest_sha256']!=parent.completion['manifest_sha256'] or
                previous['baseline_and_full_controls_exact'] is not True or
                any('-scoring' in key for key in study.manifest['inputs'])):
            raise ValueError('exact sealed six-vector and parent studies required')
        rows=[]
        for identity,task in expected.items():
            spec=task['payload']; segment=spec['segment_id']
            if (study.tasks[identity]['payload']!=spec or
                    study.rows[identity]['passed'] is not True):
                raise ValueError('changed sealed pair-path task')
            outcome=study.envelope(identity)['result']
            training=study.artifact(identity,'training.json')
            forecast=study.artifact(identity,'forecast.json')
            first=study.input('fit-'+spec['first_fit'])
            second=study.input('fit-'+spec['second_fit'])
            point=interpolate(first['normalized_parameters'],
                              second['normalized_parameters'],spec['quarter'])
            baseline=parent.artifact(
                f'{segment}-inner-anchor0-baseline','forecast.json')
            opposite=parent.artifact(
                f'{segment}-inner-anchor0-all','forecast.json')
            cut=training['training_epochs']
            if (outcome['technical_completion_only'] is not True or
                    outcome['native_calls']!=2 or
                    outcome['later_receiver_positions_used'] is not False or
                    outcome['training_cost']!=training['cost'] or
                    not np.array_equal(training['normalized_parameters'],point) or
                    forecast['prediction_receiver_positions_used'] is not False or
                    forecast['continuous_propagation_without_gps_reset'] is not True or
                    forecast['training_epochs']!=cut or
                    forecast['prediction_epochs']!=baseline['prediction_epochs'] or
                    forecast['prediction_epochs']!=opposite['prediction_epochs']):
                raise ValueError('changed saved training or forecast artifact')
            cost_a=first['residual_sum_squares']
            cost_b=second['residual_sum_squares']
            path=forecast['coordinates']
            rows.append(dict(segment_id=segment,quarter=spec['quarter'],
                fraction_from_a=spec['quarter']/4,
                endpoint_a_cost=cost_a,endpoint_b_cost=cost_b,
                training_cost=training['cost'],
                cost_above_best=training['cost']-min(cost_a,cost_b),
                cost_above_worst=training['cost']-max(cost_a,cost_b),
                later_path_gap_to_a_m=later_distance_m(
                    baseline['coordinates'],path,cut),
                later_path_gap_to_b_m=later_distance_m(
                    opposite['coordinates'],path,cut),
                endpoint_later_path_gap_m=later_distance_m(
                    baseline['coordinates'],opposite['coordinates'],cut)))
        rows.sort(key=lambda row:(row['segment_id'],row['quarter']))
        if len(rows)!=6 or {row['segment_id'] for row in rows}!={NORTH,SOUTH}:
            raise ValueError('both complete three-point paths required')
        return dict(version='ilvis0-observed-pair-path-report-v1',
            study='data/'+ID,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            tasks=6,technical_failures=0,native_calls=12,
            packet_visits=220247055,observed_fit_starts=0,
            withheld_positions_read=0,scientific_decision='abstain',rows=rows)
    finally:
        parent.close();study.close()


def render(report):
    lines=['# Complete-vector path between saved aircraft fits','',
        'Six fixed calibration vectors finished without refitting. Each vector',
        'is one quarter, one half or three quarters of the way between two',
        'saved solutions. Only the training receiver positions were scored.',
        'The later forecasts were compared with each other, never with later',
        'receiver positions. Costs are weighted squared errors, not metres.','']
    for segment,label in ((NORTH,'2010 northern'),(SOUTH,'2015 southern')):
        rows=[row for row in report['rows'] if row['segment_id']==segment]
        first=rows[0]
        lines += [f'## {label} pair','',
            f"Endpoint training costs: {first['endpoint_a_cost']:.6f} and "
            f"{first['endpoint_b_cost']:.6f}. Their later forecasts differ "
            f"by up to {first['endpoint_later_path_gap_m']:.3f} m.",'',
            '| Fraction from A | Training cost | Above worse endpoint | Later path gap to A | Later path gap to B |',
            '|---:|---:|---:|---:|---:|']
        for row in rows:
            lines.append(f"| {row['fraction_from_a']:.0%} | "
                f"{row['training_cost']:.6f} | "
                f"{row['cost_above_worst']:.6f} | "
                f"{row['later_path_gap_to_a_m']:.3f} m | "
                f"{row['later_path_gap_to_b_m']:.3f} m |")
        lines.append('')
    lines += [
        'The northern straight-line connection has a modest training-cost',
        'rise near its middle. All three sampled southern interior costs fall',
        'between the two endpoint costs while the later path moves across the',
        '0.320 m endpoint spread. These are paths through parameter space, not new',
        'optimized solutions; a different curved route could behave differently.',
        'This diagnostic cannot establish a global optimum, forecast accuracy,',
        'physical adequacy or an Earth-model decision. All earlier failed',
        'numerical stopping labels remain unchanged.','',
        '[Complete data table](observed-pair-path.csv) · '
        '[Frozen plan](OBSERVED_PAIR_PATH_PLAN.md) · '
        '[Calibration-swap study](OBSERVED_CALIBRATION_SWAP_RESULT.md)','']
    return '\n'.join(lines)


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    out=root/'docs/prediction-group-transfer'
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=tuple(report['rows'][0]),
                          lineterminator='\n')
    writer.writeheader();writer.writerows(report['rows'])
    atomic(out/'OBSERVED_PAIR_PATH_RESULT.md',render(report).encode())
    atomic(out/'observed-pair-path.csv',stream.getvalue().encode())
    atomic(out/'observed-pair-path-report.json',encoded(report))
    return report


if __name__=='__main__':
    result=publish()
    print(f"{result['tasks']}/6 sealed fixed vectors, no refits")
