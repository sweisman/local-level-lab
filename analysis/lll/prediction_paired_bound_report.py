# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only audit of the generated paired error-law bound study."""
import csv
import hashlib
import io
import math
from pathlib import Path
from statistics import median


STUDY = 'data/prediction-paired-bound-family-v1-20261111'
CONTINUATION = STUDY + '-continuation-v2'
TARGETS = ('physical_position', 'receiver_measurement')
LAWS = ('increment', 'point')


def _score(value):
    if not isinstance(value, dict):
        return None
    epochs = value.get('epochs')
    counts = value.get('marginal_covered')
    widths = value.get('median_width_by_axis')
    if (type(epochs) is not int or epochs < 1 or
            not isinstance(counts, list) or len(counts) != 3 or
            any(type(n) is not int or not 0 <= n <= epochs for n in counts) or
            value.get('marginal_total') != 3*epochs or
            not isinstance(widths, list) or len(widths) != 3 or
            any(not isinstance(w, (int, float)) or
                not math.isfinite(w) or w <= 0 for w in widths) or
            value.get('nonlinear_coverage_established') is not False or
            value.get('scientific_decision') != 'abstain'):
        raise ValueError('complete descriptive withheld interval score required')
    return dict(epochs=epochs, marginal_covered=counts,
                marginal_total=3*epochs, median_width_by_axis=widths,
                whole_recording_contained=all(n == epochs for n in counts))


def aggregate(rows):
    """Count recordings, fits and correlated-coordinate containment separately."""
    if (not isinstance(rows, list) or len(rows) != 24 or
            len({row['identity'] for row in rows}) != 24):
        raise ValueError('exact 24-recording condition ledger required')
    result = dict(total=24, completed=0, technical=0,
                  numerical_passing_fits=0, physical_passing_fits=0,
                  union_recordings=0, both_targets_whole_recording=0,
                  targets={target:dict(recordings=0, whole_recordings=0,
                                       marginal_covered=0, marginal_total=0,
                                       median_case_width_by_axis=None)
                           for target in TARGETS},
                  method_gate_passed=False,
                  coverage_calibrated=False, scientific_decision='abstain')
    widths = {target:[[], [], []] for target in TARGETS}
    for row in rows:
        if (row.get('scientific_decision') != 'abstain' or
                row.get('status') not in ('unstarted', 'interrupted', 'complete') or
                type(row.get('technical')) is not bool or
                type(row.get('numerical_passing_fits')) is not int or
                not 0 <= row['numerical_passing_fits'] <= 2 or
                type(row.get('physical_passing_fits')) is not int or
                not 0 <= row['physical_passing_fits'] <= row['numerical_passing_fits'] or
                (row['technical'] and row['status'] != 'complete')):
            raise ValueError('complete per-recording technical outcome required')
        if row['status'] == 'complete':
            result['completed'] += 1
        result['technical'] += int(row['technical'])
        result['numerical_passing_fits'] += row['numerical_passing_fits']
        result['physical_passing_fits'] += row['physical_passing_fits']
        scores = row.get('union_scores')
        if scores is None:
            continue
        if not row['technical'] or not isinstance(scores, dict) or set(scores) != set(TARGETS):
            raise ValueError('union scores require complete technical outcome')
        prepared = {target:_score(scores[target]) for target in TARGETS}
        if all(value is not None for value in prepared.values()):
            result['union_recordings'] += 1
            result['both_targets_whole_recording'] += int(
                all(value['whole_recording_contained']
                    for value in prepared.values()))
        for target, value in prepared.items():
            if value is None:
                continue
            tally = result['targets'][target]
            tally['recordings'] += 1
            tally['whole_recordings'] += int(value['whole_recording_contained'])
            tally['marginal_covered'] += sum(value['marginal_covered'])
            tally['marginal_total'] += value['marginal_total']
            for axis in range(3):
                widths[target][axis].append(value['median_width_by_axis'][axis])
    for target in TARGETS:
        values = widths[target]
        if all(values):
            result['targets'][target]['median_case_width_by_axis'] = [
                median(axis) for axis in values]
    result['method_gate_passed'] = result['completed'] == result['technical'] == 24
    return result


def replay_union_scores(binding, truth, receiver_report, intervals):
    """Recount saved later truth against saved intervals without fitting."""
    import numpy as np
    from lll.bounded_nonlinear_case import _score as score_interval

    cut = binding.get('training_epochs')
    future = binding.get('prediction_epochs')
    if (type(cut) is not int or cut < 2 or
            type(future) is not int or future < 1 or
            receiver_report.get('training_prefix_exact') is not True or
            receiver_report.get('later_observations_used_for_training') is not False or
            set(intervals) != set(TARGETS)):
        raise ValueError('complete withheld scoring binding required')
    physical = np.asarray(truth.get('coordinates'), dtype=float)
    rows = receiver_report.get('rows')
    if (not isinstance(rows, list) or len(rows) != cut+future or
            physical.shape != (cut+future, 3)):
        raise ValueError('matched full-length withheld targets required')
    receiver = np.array([[math.radians(row['latitude_deg']),
                          math.radians(row['longitude_deg']), row['height_m']]
                         for row in rows])
    if receiver.shape != physical.shape:
        raise ValueError('matched receiver target required')
    values = dict(physical_position=physical,
                  receiver_measurement=receiver)
    return {target:(score_interval(interval, values[target], cut)
                    if interval.get('scope') == 'union_of_supplied_affine_known_laws'
                    else None)
            for target, interval in intervals.items()}


def open_view(root):
    from lll.airquantumgrav_observed_hybrid_combined_audit import CombinedStudy
    from lll.studies.closed import ClosedStudy
    from lll.studies.combined_task_evidence import inspect as inspect_lineage
    from lll.studies.task_resume_sourcefix import install as install_sourcefix
    root = Path(root).resolve()
    if not (root/CONTINUATION).exists():
        return ClosedStudy(root, STUDY), None
    install_sourcefix()
    lineage = inspect_lineage(root, root/CONTINUATION)
    if (lineage.get('verified') is not True or
            lineage.get('parent') != STUDY or lineage.get('total') != 24 or
            lineage.get('scientific_decision') != 'abstain'):
        raise ValueError('bound-family continuation lineage changed')
    return CombinedStudy(root, lineage), lineage


def build(root):
    from lll.prediction_paired_bound_study import SCOPE, recipe, tasks
    from lll.studies.source_binding import verify as verify_source
    root = Path(root).resolve()
    study, lineage = open_view(root)
    try:
        expected = tasks()
        if (study.manifest.get('scope') != SCOPE or
                study.manifest['allocation']['workers'] != 4 or
                study.manifest['allocation']['threads'] != 1 or
                study.input('recipe') != recipe() or
                set(study.tasks) != {task['identity'] for task in expected}):
            raise ValueError('exact frozen bound-family matrix required')
        source_proof = verify_source(
            root, declared=study.input('qualification_request')['sources'],
            manifest=study.manifest['sources'])
        rows = []
        for task in expected:
            identity = task['identity']
            if ({key:value for key,value in study.tasks[identity].items()
                 if key not in ('index', 'shard')} != task):
                raise ValueError('frozen bound-family task changed')
            selected = identity in study.rows
            row = dict(identity=identity, **task['payload'],
                       origin=(lineage['selected'][identity]['origin']
                               if lineage is not None and identity in lineage['selected']
                               else STUDY if selected else None),
                       status='unstarted', technical=False,
                       numerical_passing_fits=0, physical_passing_fits=0,
                       union_scores=None, scientific_decision='abstain')
            if selected:
                record = study.rows[identity]
                envelope = study.envelope(identity)
                result = envelope['result']
                if (result.get('scientific_decision') != 'abstain' or
                        result.get('original_reads', 0) != 0 or
                        result.get('protected_reads', 0) != 0):
                    raise ValueError('generated-only scientific abstention required')
                row['status'] = record['status']
                row['technical'] = bool(
                    record['passed'] and result.get('technical_pair_complete') is True)
                if row['technical']:
                    if (result.get('native_calls', -1) > task['limits']['native_calls'] or
                            result.get('truth_law') != task['payload']['truth_law'] or
                            result.get('sensor_case') != task['payload']['sensor_case']):
                        raise ValueError('sealed bound-family result differs from task')
                    for name in ('input-binding.json', 'training-receiver.json',
                                 'training-law-comparison.json',
                                 'union-bounded-physical.json',
                                 'union-bounded-receiver.json',
                                 'withheld-physical-truth.json',
                                 'later-receiver-report.json', 'union-scores.json'):
                        study.artifact(identity, name)
                    binding = study.artifact(identity, 'input-binding.json')
                    intervals = dict(
                        physical_position=study.artifact(
                            identity, 'union-bounded-physical.json'),
                        receiver_measurement=study.artifact(
                            identity, 'union-bounded-receiver.json'))
                    replayed = replay_union_scores(
                        binding,
                        study.artifact(identity, 'withheld-physical-truth.json'),
                        study.artifact(identity, 'later-receiver-report.json'),
                        intervals)
                    if (result['union_scores'] != study.artifact(identity,
                                                                'union-scores.json') or
                            result['union_scores'] != replayed):
                        raise ValueError('reported union scores differ from sealed artifact')
                    for law in LAWS:
                        study.artifact(identity, law+'/fit.json')
                        study.artifact(identity, law+'/bounded-physical.json')
                        study.artifact(identity, law+'/bounded-receiver.json')
                    candidates = result['candidate_results']
                    if set(candidates) != set(LAWS):
                        raise ValueError('both candidate-law results required')
                    for law, candidate in candidates.items():
                        fit = study.artifact(identity, law+'/fit.json')
                        numerical = (fit.get('converged') is True and
                                     fit.get('stopping_rule_verified') is True)
                        if candidate['converged'] is not numerical:
                            raise ValueError('saved numerical stopping differs')
                    if (result['numerical_passing_fits'] != sum(
                            item['converged'] for item in candidates.values()) or
                            result['physical_passing_fits'] != sum(
                                item['physical_prediction_passed']
                                for item in candidates.values())):
                        raise ValueError('saved fit counts differ from individual fits')
                    row['numerical_passing_fits'] = result['numerical_passing_fits']
                    row['physical_passing_fits'] = result['physical_passing_fits']
                    row['union_scores'] = result['union_scores']
            rows.append(row)
        total = aggregate(rows)
        reporter = root/'analysis/lll/prediction_paired_bound_report.py'
        return dict(verified=True, version='paired-bound-family-report-v1',
                    original_manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    continuation_lineage_sha256=(lineage['lineage_sha256']
                                                 if lineage is not None else None),
                    reporter_sha256=hashlib.sha256(reporter.read_bytes()).hexdigest(),
                    source_proof=source_proof,
                    charges=study.summary['charged'],
                    total=total, rows=rows,
                    coverage_calibrated=False, scientific_decision='abstain')
    finally:
        study.close()


def render(report):
    if (report.get('verified') is not True or
            report.get('scientific_decision') != 'abstain' or
            report.get('coverage_calibrated') is not False):
        raise ValueError('verified bound-family report required')
    total = report['total']
    lines = ['# Paired error-law interval study', '',
             f"**{total['completed']}/24 recordings returned; "
             f"{total['technical']}/24 passed the technical gate.**", '',
             f"The two-law fits passed numerical stopping in "
             f"{total['numerical_passing_fits']}/48 cases and the declared "
             f"physical prediction screen in {total['physical_passing_fits']}/48.", '',
             f"Both interval unions were available for "
             f"{total['union_recordings']}/24 recordings. Both targets contained "
             f"every later coordinate in {total['both_targets_whole_recording']} "
             'of those recordings.', '']
    for target, label in ((TARGETS[0], 'Physical position'),
                          (TARGETS[1], 'Future receiver report')):
        tally = total['targets'][target]
        lines.append(f"- {label}: {tally['whole_recordings']}/{tally['recordings']} "
                     'recordings contained every later coordinate. '
                     f"Descriptive coordinate count: {tally['marginal_covered']}/"
                     f"{tally['marginal_total']}.")
        widths = tally['median_case_width_by_axis']
        if widths is not None:
            lines.append('  Median interval width per recording: '
                         f'{math.degrees(widths[0]):.5g}° latitude, '
                         f'{math.degrees(widths[1]):.5g}° longitude, '
                         f'{widths[2]:.5g} m height.')
    lines += ['',
              ('The 24/24 technical gate passed.' if total['method_gate_passed']
               else 'The 24/24 technical gate did not pass.'),
              'Receiver epochs within one recording are correlated. These counts',
              'do not establish 95% coverage, an observed-aircraft uncertainty',
              'threshold or an Earth-model decision. All scientific decisions',
              'remain abstain. The detailed ledger preserves every missing,',
              'failed and completed recording.', '',
              '[Frozen plan](PLAN.md) · [Recording ledger](results.csv) · '
              '[Uncertainty method](../PREDICTION_ERROR_LAW_PLAN.md).', '']
    return '\n'.join(lines)


def csv_bytes(report):
    output = io.StringIO()
    fields = ['identity', 'model', 'profile', 'truth_law', 'sensor_case',
              'origin', 'status', 'technical', 'numerical_passing_fits',
              'physical_passing_fits']
    for target in TARGETS:
        fields.extend(f'{target}_{name}' for name in (
            'whole_recording', 'epochs', 'covered_lat', 'covered_lon',
            'covered_height', 'width_lat_deg', 'width_lon_deg',
            'width_height_m'))
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in report['rows']:
        scores = row['union_scores'] or {}
        item = dict(identity=row['identity'], model=row['model'],
                    profile=row['profile'], truth_law=row['truth_law'],
                    sensor_case=row['sensor_case'], origin=row['origin'],
                    status=row['status'], technical=row['technical'],
                    numerical_passing_fits=row['numerical_passing_fits'],
                    physical_passing_fits=row['physical_passing_fits'])
        for target in TARGETS:
            value = _score(scores.get(target))
            if value is None:
                continue
            counts = value['marginal_covered']
            widths = value['median_width_by_axis']
            item.update({f'{target}_whole_recording':value['whole_recording_contained'],
                         f'{target}_epochs':value['epochs'],
                         f'{target}_covered_lat':counts[0],
                         f'{target}_covered_lon':counts[1],
                         f'{target}_covered_height':counts[2],
                         f'{target}_width_lat_deg':math.degrees(widths[0]),
                         f'{target}_width_lon_deg':math.degrees(widths[1]),
                         f'{target}_width_height_m':widths[2]})
        writer.writerow(item)
    return output.getvalue().encode()


def publish(root):
    from lll.studies.artifacts import atomic, encoded
    report = build(root)
    directory = Path(root)/'docs/prediction-paired-bound-family'
    atomic(directory/'RESULT.md', render(report).encode())
    atomic(directory/'results.csv', csv_bytes(report))
    atomic(directory/'verified-report.json', encoded(report))
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    result = publish(args.root)
    total = result['total']
    print(f"{total['completed']}/24 recordings audited; "
          f"technical gate={total['method_gate_passed']}")


if __name__ == '__main__':
    main()
