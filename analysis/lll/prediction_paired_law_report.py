# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only totals for the paired aircraft error-law pilot."""
from collections import Counter
from pathlib import Path
import csv
import io
import math


LAWS = frozenset(('increment', 'point'))
TARGETS = ('physical_position', 'receiver_measurement')


def aggregate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('nonempty sealed paired-law results required')
    counts = Counter()
    largest_delta = 0.
    largest_sigma_ratio = 1.
    covered = {target:dict(covered=0, total=0) for target in TARGETS}
    for row in rows:
        if (not isinstance(row, dict) or row.get('truth_law') not in LAWS or
                row.get('passed') is not True or
                row.get('scientific_decision') != 'abstain' or
                row.get('original_reads') != 0 or row.get('protected_reads') != 0):
            raise ValueError('complete generated technical case and abstention required')
        candidates = row.get('candidate_results')
        if not isinstance(candidates, dict) or set(candidates) != LAWS:
            raise ValueError('both candidate fits required for each recording')
        comparison = row.get('comparison')
        if (not isinstance(comparison, dict) or
                comparison.get('selected_law') is not None or
                comparison.get('later_observations_used') is not False or
                comparison.get('coverage_calibrated') is not False or
                comparison.get('scientific_decision') != 'abstain'):
            raise ValueError('training-only abstention required')
        status = comparison.get('status')
        if status not in ('numerically_unqualified', 'active_bounds_unsupported',
                          'training_only_unqualified'):
            raise ValueError('declared paired comparison status required')
        counts['recordings'] += 1
        counts['comparison:'+status] += 1
        ranking = comparison.get('training_ranking')
        if status == 'numerically_unqualified':
            if ranking is not None:
                raise ValueError('unqualified numerical comparison cannot rank laws')
        else:
            if (not isinstance(ranking, list) or len(ranking) != 2 or
                    {entry.get('law_id') for entry in ranking} != LAWS):
                raise ValueError('complete paired training ranking required')
            counts['ranking_cases'] += 1
            counts['ranking_favors_generating_law'] += int(
                ranking[0]['law_id'] == row['truth_law'])
            delta = ranking[1].get('delta_nll')
            if (not isinstance(delta, (int, float)) or
                    not math.isfinite(delta) or delta < 0):
                raise ValueError('finite nonnegative training-score separation required')
            largest_delta = max(largest_delta, float(delta))
            ratio = comparison.get('maximum_future_sigma_ratio')
            if (not isinstance(ratio, (int, float)) or
                    not math.isfinite(ratio) or ratio < 1):
                raise ValueError('finite candidate forecast-scale ratio required')
            largest_sigma_ratio = max(largest_sigma_ratio, float(ratio))
        for candidate in candidates.values():
            if (not isinstance(candidate, dict) or
                    candidate.get('scientific_decision') != 'abstain' or
                    type(candidate.get('converged')) is not bool or
                    type(candidate.get('physical_prediction_passed')) is not bool or
                    (candidate['physical_prediction_passed'] and
                     not candidate['converged'])):
                raise ValueError('saved candidate fit outcome required')
            counts['fits'] += 1
            counts['numerically_passing_fits'] += int(candidate['converged'])
            counts['physical_passing_fits'] += int(
                candidate['physical_prediction_passed'])
            coverage = candidate.get('marginal_coverage')
            if not isinstance(coverage, dict) or set(coverage) != set(TARGETS):
                raise ValueError('both saved future targets required')
            for target in TARGETS:
                score = coverage[target]
                epochs = score.get('epochs')
                counts_by_axis = score.get('marginal_covered')
                if (type(epochs) is not int or epochs < 1 or
                        not isinstance(counts_by_axis, list) or
                        len(counts_by_axis) != 3 or
                        any(type(value) is not int or not 0 <= value <= epochs
                            for value in counts_by_axis) or
                        score.get('marginal_total') != 3*epochs or
                        score.get('confidence_calibrated') is not False):
                    raise ValueError('complete uncalibrated future marginals required')
                covered[target]['covered'] += sum(counts_by_axis)
                covered[target]['total'] += 3*epochs
    return dict(recordings=counts['recordings'], fits=counts['fits'],
                numerically_passing_fits=counts['numerically_passing_fits'],
                physical_passing_fits=counts['physical_passing_fits'],
                ranking_cases=counts['ranking_cases'],
                ranking_favors_generating_law=counts['ranking_favors_generating_law'],
                largest_training_delta_nll=largest_delta,
                largest_future_sigma_ratio=largest_sigma_ratio,
                comparison_statuses={name:counts['comparison:'+name] for name in
                                     ('numerically_unqualified',
                                      'active_bounds_unsupported',
                                      'training_only_unqualified')
                                     if counts['comparison:'+name]},
                fixed_parameter_coverage=covered,
                coverage_calibrated=False, scientific_decision='abstain')


def build(root, *, opener=None, source_verifier=None):
    """Verify the sealed study and recount every candidate from saved artifacts."""
    from lll.prediction_paired_law_study import (
        IDENTITY, SCOPE, limits, recipe, tasks)
    if opener is None:
        from lll.studies.closed import ClosedStudy
        opener = ClosedStudy
    if source_verifier is None:
        from lll.studies.source_binding import verify
        source_verifier = verify
    root = Path(root).resolve()
    study = opener(root, 'data/'+IDENTITY)
    try:
        expected = tasks()
        known = {task['identity'] for task in expected}
        allowance = limits(recipe())
        charged = {key:12*value for key,value in allowance.items()}
        if (study.completion.get('state') != 'complete' or
                study.summary.get('state') != 'complete' or
                study.summary.get('passed') is not True or
                study.summary.get('completed') != 12 or
                study.summary.get('total') != 12 or
                study.summary.get('charged') != charged or
                study.manifest.get('scope') != SCOPE or
                study.input('recipe') != recipe() or
                set(study.tasks) != known or set(study.rows) != known):
            raise ValueError('complete twelve-case paired-law study required')
        source_proof = source_verifier(
            root, declared=study.input('qualification_request')['sources'],
            manifest=study.manifest['sources'])
        rows = []
        for task in expected:
            identity = task['identity']
            if {key:value for key,value in study.tasks[identity].items()
                if key not in ('index', 'shard')} != task:
                raise ValueError('frozen paired-law task differs')
            result = study.envelope(identity)['result']
            comparison = study.artifact(identity,
                                        'training-law-comparison.json')
            if (result.get('truth_law') != task['payload']['truth_law'] or
                    result.get('comparison_status') != comparison.get('status') or
                    result.get('technical_pair_complete') is not True or
                    result.get('native_calls', -1) > task['limits']['native_calls']):
                raise ValueError('sealed paired-law result differs from saved comparison')
            rows.append(dict(identity=identity, **result,
                             comparison=comparison))
        total = aggregate(rows)
        return dict(verified=True, version='paired-aircraft-law-report-v1',
                    summary_sha256=study.completion['summary_sha256'],
                    source_proof=source_proof, charged=study.summary['charged'],
                    rows=rows, total=total,
                    confidence_calibrated=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def render(report):
    if (report.get('verified') is not True or
            report.get('scientific_decision') != 'abstain' or
            report.get('confidence_calibrated') is not False or
            report['total']['recordings'] != 12 or report['total']['fits'] != 24):
        raise ValueError('verified complete paired-law report required')
    total = report['total']
    statuses = total['comparison_statuses']
    lines = [
        '# Paired aircraft error-law pilot', '',
        '**12 generated recordings and 24 candidate fits were verified.**',
        'Each recording was fitted under both fixed IMU error laws using the',
        'same gyroscope, accelerometer and earlier receiver measurements.',
        'The complete comparison was saved before later positions were scored.', '',
        f"Numerical checks passed for {total['numerically_passing_fits']}/24 fits; "
        f"{total['physical_passing_fits']}/24 also passed the declared physical "
        'prediction screen. Training scores could be ranked in '
        f"{total['ranking_cases']}/12 recordings. The numerical minimum "
        f"matched the generating error law in "
        f"{total['ranking_favors_generating_law']} of those ranked cases. "
        f"The largest training-score separation was only "
        f"{total['largest_training_delta_nll']:.6g} negative-log-likelihood units. "
        f"The largest fixed-parameter future scale ratio was "
        f"{total['largest_future_sigma_ratio']:.9g}.", '',
        'Comparison status by recording: '
        + ', '.join(f'{name.replace("_", " ")}: {count}'
                    for name,count in statuses.items()) + '.', '',
        'These rankings are **not a calibrated error-law selection**. Every',
        'scientific decision remains **abstain**. The reported 95% marginal',
        'counts use fixed calibration parameters and omit uncertainty caused',
        'by fitting calibration, especially at active bounds. They are',
        'descriptive diagnostics, not demonstrated 95% coverage.', '',
    ]
    for target, label in ((
            'physical_position', 'Physical position'),
            ('receiver_measurement', 'Future receiver report')):
        tally = total['fixed_parameter_coverage'][target]
        lines.append(f"- {label}: {tally['covered']}/{tally['total']} "
                     'fixed-parameter marginal intervals contain the generated value.')
    lines += ['', 'The two-minute records use one predeclared noise seed and',
              'separately fitted physical candidates. The study tests error-law',
              'comparison and prediction mechanics, not Earth-model selection,',
              'aircraft error coverage or statistical significance. No recorded',
              'aircraft data or reserved confirmation groups were read.', '',
              '[Finite plan](PLAN.md) · [Per-fit results](results.csv) · '
              '[Sampling comparison](SAMPLING.md) · '
              '[Next analyses](../PREDICTION_ERROR_LAW_PLAN.md).', '']
    return '\n'.join(lines)


def publish(root):
    from lll.studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/prediction-paired-law'
    columns = ('recording', 'generating_law', 'candidate_law', 'converged',
               'physical_prediction_passed', 'training_cost',
               'later_horizontal_rms_m', 'later_height_rms_m',
               'physical_marginals_covered', 'physical_marginals_total',
               'receiver_marginals_covered', 'receiver_marginals_total',
               'comparison_status', 'training_delta_nll', 'active_bounds')
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    for row in report['rows']:
        ranking = row['comparison']['training_ranking'] or []
        deltas = {item['law_id']:item['delta_nll'] for item in ranking}
        for law in sorted(LAWS):
            candidate = row['candidate_results'][law]
            coverage = candidate['marginal_coverage']
            physical = coverage['physical_position']
            receiver = coverage['receiver_measurement']
            prediction = candidate.get('prediction', {})
            writer.writerow(dict(
                recording=row['identity'], generating_law=row['truth_law'],
                candidate_law=law, converged=candidate['converged'],
                physical_prediction_passed=candidate['physical_prediction_passed'],
                training_cost=candidate.get('training_cost'),
                later_horizontal_rms_m=prediction.get('horizontal_rms_m'),
                later_height_rms_m=prediction.get('vertical_rms_m'),
                physical_marginals_covered=sum(physical['marginal_covered']),
                physical_marginals_total=physical['marginal_total'],
                receiver_marginals_covered=sum(receiver['marginal_covered']),
                receiver_marginals_total=receiver['marginal_total'],
                comparison_status=row['comparison']['status'],
                training_delta_nll=deltas.get(law),
                active_bounds='|'.join(
                    row['comparison']['active_bounds_by_law'][law])))
    atomic(target/'verified-report.json', encoded(report))
    atomic(target/'results.csv', output.getvalue().encode())
    atomic(target/'RESULT.md', render(report).encode())
    return dict(published=str(target.relative_to(root)),
                recordings=report['total']['recordings'],
                fits=report['total']['fits'])
