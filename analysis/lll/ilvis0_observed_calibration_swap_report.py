# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only path and cost report for the fixed calibration-swap study."""

import csv
import hashlib
import io
from pathlib import Path

import numpy as np

from .ilvis0_calibration_groups import VARIANTS,hybrid
from .ilvis0_observed_calibration_swap import ID,NORTH,SOUTH,tasks
from .ilvis0_observed_method_pilot_v2 import ID as ORIGINAL_ID
from .ilvis0_solver_position import physical_metric


def later_distance_m(reference,other,cut):
    first,second=(np.asarray(value,float) for value in (reference,other))
    if (first.shape!=second.shape or first.ndim!=2 or first.shape[1]!=3 or
            not 0<cut<len(first) or
            not all(np.all(np.isfinite(value)) for value in (first,second))):
        raise ValueError('matched finite continuous later paths required')
    delta=second[cut:]-first[cut:]
    delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi
    return float(np.max(np.linalg.norm(delta*physical_metric(first[cut:]),axis=1)))


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,'data/'+ID)
    original=ClosedStudy(root,'data/'+ORIGINAL_ID)
    try:
        expected={task['identity']:task for task in tasks(study.input('layouts'))}
        if (study.completion['state']!='complete' or
                study.summary['completed']!=24 or
                study.summary['charged']['native_calls']!=48 or
                study.summary['charged']['packet_visits']!=880988220 or
                set(study.tasks)!=set(expected) or set(study.rows)!=set(expected)
                or original.completion['state']!='complete' or
                len(original.tasks)!=24 or
                any('-scoring' in key for key in study.manifest['inputs'])):
            raise ValueError('complete exact training-only swap study required')
        rows=[]
        for identity,task in expected.items():
            if (study.tasks[identity]['payload']!=task['payload'] or
                    study.rows[identity]['passed'] is not True):
                raise ValueError('sealed calibration-swap identity differs')
            spec=task['payload']
            outcome=study.envelope(identity)['result']
            training=study.artifact(identity,'training.json')
            forecast=study.artifact(identity,'forecast.json')
            anchor=study.input('fit-'+spec['anchor_fit'])
            counterpart=study.input('fit-'+spec['counterpart_fit'])
            point=hybrid(anchor['active_parameters'],
                anchor['normalized_parameters'],
                counterpart['normalized_parameters'],spec['variant'])
            baseline=original.artifact(spec['anchor_fit'],'forecast.json')
            opposite=original.artifact(spec['counterpart_fit'],'forecast.json')
            cut=training['training_epochs']
            if (outcome['technical_completion_only'] is not True or
                    outcome['native_calls']!=2 or
                    outcome['later_receiver_positions_used'] is not False or
                    training['cost']!=outcome['training_cost'] or
                    not np.array_equal(training['normalized_parameters'],point) or
                    forecast['prediction_receiver_positions_used'] is not False or
                    forecast['continuous_propagation_without_gps_reset'] is not True or
                    forecast['training_epochs']!=cut or
                    forecast['prediction_epochs']!=
                    baseline['prediction_epochs'] or
                    forecast['prediction_epochs']!=
                    opposite['prediction_epochs']):
                raise ValueError('sealed training or forecast artifact differs')
            path=forecast['coordinates']
            if spec['variant'] in ('baseline','all'):
                reference=baseline if spec['variant']=='baseline' else opposite
                fitted=anchor if spec['variant']=='baseline' else counterpart
                if (not np.array_equal(path,reference['coordinates']) or
                        training['cost']!=fitted['residual_sum_squares']):
                    raise ValueError('unchanged saved baseline/full-vector control differs')
            rows.append(dict(identity=identity,
                segment_id=spec['segment_id'],anchor=spec['anchor'],
                variant=spec['variant'],training_epochs=cut,
                training_cost=training['cost'],
                cost_change_from_anchor=training['cost']-
                    anchor['residual_sum_squares'],
                later_shift_from_anchor_m=later_distance_m(
                    baseline['coordinates'],path,cut),
                later_gap_to_counterpart_m=later_distance_m(
                    opposite['coordinates'],path,cut),
                original_pair_gap_m=later_distance_m(
                    baseline['coordinates'],opposite['coordinates'],cut)))
        if len(rows)!=24:
            raise ValueError('all 24 fixed vectors required')
        pairs=[]
        for segment in (NORTH,SOUTH):
            group=[row for row in rows if row['segment_id']==segment]
            if (len(group)!=12 or
                    {(row['anchor'],row['variant']) for row in group}!=
                    {(anchor,variant) for anchor in (0,1)
                     for variant in VARIANTS}):
                raise ValueError('both directions and all groups required')
            pairs.append(dict(segment_id=segment,
                original_pair_gap_m=group[0]['original_pair_gap_m'],
                variants=[dict(variant=variant,
                    shift_from_anchor_by_direction_m=[next(row[
                        'later_shift_from_anchor_m'] for row in group
                        if row['anchor']==anchor and row['variant']==variant)
                        for anchor in (0,1)],
                    cost_change_by_direction=[next(row[
                        'cost_change_from_anchor'] for row in group
                        if row['anchor']==anchor and row['variant']==variant)
                        for anchor in (0,1)])
                    for variant in VARIANTS]))
        return dict(version='ilvis0-observed-calibration-swap-report-v1',
            study='data/'+ID,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            original_manifest_sha256=original.completion['manifest_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            tasks=24,technical_failures=0,native_calls=48,
            packet_visits=880988220,baseline_and_full_controls_exact=True,
            original_outcomes_unchanged=True,observed_fit_starts=0,
            withheld_positions_read=0,scientific_decision='abstain',
            pairs=pairs,rows=rows)
    finally:
        original.close();study.close()


def render(report):
    lines=['# Fixed calibration-swap result','',
        'All 24 declared vectors finished. Each unchanged baseline and',
        'full-vector swap exactly reproduced the corresponding saved training',
        'cost and continuous forecast. No optimizer ran and no later receiver',
        'position entered a calculation. The table shows how far each',
        'one-group swap moves the **later forecast path** from its anchor;',
        'the two numbers are the two swap directions. Training cost is the',
        'weighted squared receiver error on the fitted portion, not metres.', '']
    for pair in report['pairs']:
        label='2010 northern' if pair['segment_id'].startswith('7df21c') else '2015 southern'
        lines += [f"## {label} pair",'',
            f"The two original forecasts differ by up to {pair['original_pair_gap_m']:.3f} m.", '',
            '| Swapped coordinates | A toward B path shift | B toward A path shift | Training cost increase |',
            '|---|---:|---:|---:|']
        for row in pair['variants']:
            if row['variant'] in ('baseline','all'):
                continue
            a,b=row['shift_from_anchor_by_direction_m']
            lo,hi=sorted(row['cost_change_by_direction'])
            lines.append(f"| {row['variant'].replace('_',' ')} | {a:.3f} m | "
                f"{b:.3f} m | {lo:.3g}–{hi:.3g} |")
        lines += ['',
            'The isolated swaps worsen the training fit. Their path shifts',
            'are not plausible alternative forecasts on their own. The',
            'nearly equal costs of the two whole vectors instead show that',
            'calibration groups compensate one another. Their effects need',
            'not add up to the full pair difference.', '']
    lines += [
        'Training costs and each vector’s remaining distance to the opposite',
        'forecast are retained in the [complete table](observed-calibration-swap.csv).',
        'A forecast shift does not identify the true physical calibration or',
        'make a failed fit pass. The numerical method, aircraft prediction',
        'adequacy and Earth-model decision remain unqualified.', '',
        '[Frozen plan](OBSERVED_CALIBRATION_SWAP_PLAN.md) · '
        '[Timing check](OBSERVED_FIXED_ENDPOINT_RESULT.md)', '']
    return '\n'.join(lines)


def csv_bytes(report):
    stream=io.StringIO(newline='')
    fields=tuple(report['rows'][0])
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader();writer.writerows(report['rows'])
    return stream.getvalue().encode()


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    out=root/'docs/prediction-group-transfer'
    atomic(out/'OBSERVED_CALIBRATION_SWAP_RESULT.md',render(report).encode())
    atomic(out/'observed-calibration-swap.csv',csv_bytes(report))
    atomic(out/'observed-calibration-swap-report.json',encoded(report))
    return report


if __name__=='__main__':
    report=publish()
    print(f"{report['tasks']}/24 sealed fixed vectors; exact baseline/full controls")
