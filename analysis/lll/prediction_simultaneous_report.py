# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of generated whole-period prediction coverage."""
import csv
import hashlib
import io
import math
from pathlib import Path


STUDY = 'data/prediction-simultaneous-law-family-v1-20261112'
TARGETS = ('physical_position', 'receiver_measurement')


def aggregate(rows):
    """The trial unit is a recording, including every technical failure."""
    from scipy.stats import beta
    from statistics import median

    if (not isinstance(rows, list) or len(rows) != 96 or
            {row.get('identity') for row in rows} !=
            {f'case-{i:03d}' for i in range(96)}):
        raise ValueError('exact frozen 96-recording cohort required')
    out = dict(total=96, completed=0, technical=0,
               numerical_passing_fits=0, physical_passing_fits=0,
               whole_recording_successes=0)
    widths = {target:[[], [], []] for target in TARGETS}
    out['targets'] = {target:dict(recordings=0, whole_recordings=0,
                                   coordinate_covered=0, coordinate_total=0)
                      for target in TARGETS}
    for row in rows:
        if (row.get('status') not in ('complete', 'interrupted', 'unstarted') or
                type(row.get('technical')) is not bool or
                type(row.get('numerical_passing_fits')) is not int or
                not 0 <= row['numerical_passing_fits'] <= 2 or
                type(row.get('physical_passing_fits')) is not int or
                not 0 <= row['physical_passing_fits'] <= row['numerical_passing_fits'] or
                not isinstance(row.get('targets'), dict) or
                (row['technical'] and row['status'] != 'complete') or
                (row['targets'] and set(row['targets']) != set(TARGETS))):
            raise ValueError('invalid complete recording outcome')
        out['completed'] += row['status'] == 'complete'
        out['technical'] += row['technical']
        out['numerical_passing_fits'] += row['numerical_passing_fits']
        out['physical_passing_fits'] += row['physical_passing_fits']
        whole = row['technical'] and row['physical_passing_fits'] == 2
        for target in TARGETS:
            value = row['targets'].get(target)
            if value is None:
                whole = False
                continue
            epochs, covered, axis_width = (value.get('epochs'),
                                            value.get('covered'),
                                            value.get('median_width'))
            if (not row['technical'] or type(epochs) is not int or epochs < 1 or
                    not isinstance(covered, list) or len(covered) != 3 or
                    any(type(n) is not int or not 0 <= n <= epochs
                        for n in covered) or
                    not isinstance(axis_width, list) or len(axis_width) != 3 or
                    any(type(w) not in (int, float) or not math.isfinite(w)
                        or w <= 0 for w in axis_width)):
                raise ValueError('invalid withheld target score')
            tally = out['targets'][target]
            tally['recordings'] += 1
            tally['whole_recordings'] += all(n == epochs for n in covered)
            tally['coordinate_covered'] += sum(covered)
            tally['coordinate_total'] += 3*epochs
            whole &= all(n == epochs for n in covered)
            for axis in range(3):
                widths[target][axis].append(axis_width[axis])
        out['whole_recording_successes'] += bool(whole)
    out['failures'] = 96 - out['whole_recording_successes']
    misses = out['failures']
    out['failure_upper_95'] = (1.0 if misses == 96 else
                               float(beta.ppf(.95, misses+1, 96-misses)))
    out['coverage_gate_passed'] = misses <= 1 and out['failure_upper_95'] <= .05
    for target in TARGETS:
        out['targets'][target]['median_case_width_by_axis'] = (
            [median(axis) for axis in widths[target]]
            if all(widths[target]) else None)
    return out


def recording_success(row):
    return (row['technical'] and row['physical_passing_fits'] == 2 and
            set(row['targets']) == set(TARGETS) and
            all(all(n == value['epochs'] for n in value['covered'])
                for value in row['targets'].values()))


def build(root, *, study_id=STUDY, definition=None):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    from lll.airquantumgrav_observed_hybrid_combined_audit import CombinedStudy
    from lll.studies.combined_task_evidence import inspect as inspect_lineage
    from lll.studies.task_resume_sourcefix import install as install_sourcefix
    from lll.ilvis0_control_shards import verify_completion
    from lll.prediction_paired_bound_report import replay_union_scores, _score
    if definition is None:
        from lll import prediction_simultaneous_study as definition
    root = Path(root).resolve()
    continuation = study_id+'-continuation'
    lineage = None
    if (root/continuation).exists():
        from lll.studies import task_resume as resume
        previous = (resume.runner.prepare, resume.qualification_sources,
                    resume.REQUIRED_TESTS)
        try:
            install_sourcefix()
            lineage = inspect_lineage(root, root/continuation)
        finally:
            (resume.runner.prepare, resume.qualification_sources,
             resume.REQUIRED_TESTS) = previous
        if (lineage.get('verified') is not True or
                lineage.get('parent') != study_id or
                lineage.get('total') != 96 or
                lineage.get('state') != 'all_tasks_finished' or
                lineage.get('completed') != 96 or
                lineage.get('pending_identities')):
            raise ValueError('whole-period continuation lineage changed')
        study = CombinedStudy(root, lineage)
    else:
        verified_summary = verify_completion(root/study_id)
        study = ClosedStudy(root, study_id)
    try:
        expected = definition.tasks()
        if (study.manifest.get('scope') != definition.SCOPE or
                study.input('recipe') != definition.recipe() or
                set(study.tasks) != {task['identity'] for task in expected} or
                len(study.rows) != 96):
            raise ValueError('frozen cohort differs')
        if lineage is None and verified_summary['charged'] != study.summary['charged']:
            raise ValueError('immutable journal charges differ from closed summary')
        for path, sha in study.manifest['sources'].items():
            if digest(study.read('source-freeze/'+path, raw=True)) != sha:
                raise ValueError('frozen source snapshot differs: '+path)
        rows = []
        for task in expected:
            identity = task['identity']
            if {key:value for key,value in study.tasks[identity].items()
                    if key not in ('index', 'shard')} != task:
                raise ValueError('frozen task differs')
            row = dict(identity=identity, **task['payload'], status='unstarted',
                       technical=False, numerical_passing_fits=0,
                       physical_passing_fits=0, targets={}, error_type=None,
                       reason=None)
            if identity in study.rows:
                record = study.rows[identity]
                result = study.envelope(identity)['result']
                if result.get('scientific_decision') != 'abstain':
                    raise ValueError('scientific abstention required')
                row.update(status=record['status'],
                           technical=bool(record['passed'] and result.get(
                               'technical_pair_complete') is True),
                           error_type=result.get('error_type'),
                           reason=result.get('reason'))
                if row['technical']:
                    if (result.get('noise_seed') != task['payload']['noise_seed'] or
                            result.get('original_reads') != 0 or
                            result.get('protected_reads') != 0):
                        raise ValueError('generated-only input binding differs')
                    binding = study.artifact(identity, 'input-binding.json')
                    intervals = {
                        target:study.artifact(identity,
                            'union-simultaneous-bounded-'+
                            ('physical' if target == TARGETS[0] else 'receiver')+
                            '.json') for target in TARGETS}
                    saved = study.artifact(identity, 'union-scores.json')
                    if result.get('union_scores') != saved or set(saved) != set(TARGETS):
                        raise ValueError('sealed withheld score differs')
                    supported = all(value.get('scope') ==
                                    'union_of_supplied_affine_simultaneous_laws'
                                    for value in intervals.values())
                    if supported:
                        replay_intervals = {target:dict(value,
                            scope='union_of_supplied_affine_known_laws')
                            for target,value in intervals.items()}
                        replay = replay_union_scores(
                            binding,
                            study.artifact(identity, 'withheld-physical-truth.json'),
                            study.artifact(identity, 'later-receiver-report.json'),
                            replay_intervals)
                        if saved != replay:
                            raise ValueError('sealed withheld scores differ on replay')
                        for target in TARGETS:
                            value = _score(saved[target])
                            row['targets'][target] = dict(
                                epochs=value['epochs'],
                                covered=value['marginal_covered'],
                                median_width=value['median_width_by_axis'])
                    elif not all(value.get('supported') is False and
                                 value.get('reason') == 'candidate_fit_unqualified' and
                                 value.get('scientific_decision') == 'abstain' and
                                 value.get('prediction_target') == target and
                                 saved[target] is None
                                 for target,value in intervals.items()):
                        raise ValueError('unsupported interval must abstain')
                    candidates = result['candidate_results']
                    if set(candidates) != {'increment', 'point'}:
                        raise ValueError('two candidate-law fits required')
                    for law,candidate in candidates.items():
                        fit = study.artifact(identity, law+'/fit.json')
                        numerical = fit.get('converged') is True and fit.get(
                            'stopping_rule_verified') is True
                        if candidate['converged'] is not numerical:
                            raise ValueError('saved numerical result differs')
                    row['numerical_passing_fits'] = sum(
                        item['converged'] for item in candidates.values())
                    row['physical_passing_fits'] = sum(
                        item['physical_prediction_passed']
                        for item in candidates.values())
            rows.append(row)
        totals = aggregate(rows)
        return dict(verified=True, version='simultaneous-report-v1',
                    study=study_id,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    continuation_lineage_sha256=(
                        lineage['lineage_sha256'] if lineage else None),
                    immutable_journals_verified=True,
                    frozen_sources_verified=len(study.manifest['sources']),
                    reporter_sha256=hashlib.sha256((root/
                        'analysis/lll/prediction_simultaneous_report.py').read_bytes()).hexdigest(),
                    charges=study.summary['charged'], totals=totals, rows=rows,
                    scientific_decision='abstain', observed_coverage_qualified=False)
    finally:
        study.close()


def render(report):
    total = report['totals']
    errors = sorted({row['error_type'] for row in report['rows']
                     if row['error_type']})
    launch_failure = (total['technical'] == 0 and
                      report['charges']['native_calls'] == 0 and
                      errors == ['ImportError'])
    deadline_stops = [row for row in report['rows']
                      if row['error_type'] == 'BudgetStopped' and
                      row['reason'] == 'original cooperative deadline exhausted']
    lines = [
        '# Whole-period generated prediction coverage', '',
        f"**{total['completed']}/96 tasks closed; {total['technical']}/96 "
        'produced a paired forecast.**', '',
        f"The preregistered recording-level gate "
        f"{'passed' if total['coverage_gate_passed'] else 'failed'}: "
        f"{total['whole_recording_successes']}/96 complete recordings "
        'contained every later coordinate of both targets and passed both fits.', '',
        f"Exact one-sided 95% upper failure bound for the declared generated "
        f"mixture: {total['failure_upper_95']:.2%}. Technical errors count "
        'as failures.', '',
        f"Numerical fits: {total['numerical_passing_fits']}/192. "
        f"Physical prediction screens: {total['physical_passing_fits']}/192.", '',
        f"Sealed technical errors: {', '.join(errors) if errors else 'none'}.", '',
        ('All 96 workers failed to load the package adapter before the first '
         'numerical call. This is a software launch failure; it supplies no '
         'empirical coverage information. The original tasks and their sealed '
         'failure outcomes remain preserved.' if launch_failure else
         (f'{len(deadline_stops)} recordings stopped at the original eight-hour '
          'cooperative deadline. Their sealed failures remain failures; the '
          'separate continuation completed only 12 previously unstarted tasks. '
          'All 92 scored recordings contained every later coordinate, but the '
          'technical stops keep the predefined 5% gate from passing.'
          if len(deadline_stops) == 4 and
             report['continuation_lineage_sha256'] else
          'Every technical and scientific outcome is counted in the gate.')), '',
        'This does not establish observed-aircraft coverage or decide an '
        'Earth model. All scientific decisions remain abstain.', '',
        '## Withheld targets', '']
    for target,label in ((TARGETS[0], 'Physical position'),
                         (TARGETS[1], 'Future receiver report')):
        tally = total['targets'][target]
        lines.append(f"- {label}: {tally['whole_recordings']}/"
                     f"{tally['recordings']} scored recordings contained every "
                     'later coordinate.')
        widths = tally['median_case_width_by_axis']
        if widths is not None:
            lines.append('  Median interval width per recording: '
                         f'{math.degrees(widths[0]):.5g}° latitude, '
                         f'{math.degrees(widths[1]):.5g}° longitude, '
                         f'{widths[2]:.5g} m height.')
    lines += ['', '[Frozen plan](PLAN.md) · [Recording ledger](results.csv) · '
              '[Condition summary](condition-summary.csv) · '
              '[Method](../PREDICTION_ERROR_LAW_PLAN.md).', '']
    return '\n'.join(lines)


def csv_bytes(report):
    output = io.StringIO()
    fields = ['identity', 'model', 'profile', 'truth_law', 'sensor_case',
              'noise_seed', 'status', 'technical', 'error_type', 'reason',
              'numerical_passing_fits', 'physical_passing_fits']
    for target in TARGETS:
        fields += [f'{target}_{name}' for name in (
            'epochs', 'covered_lat', 'covered_lon', 'covered_height',
            'whole_recording')]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in report['rows']:
        item = {name:row.get(name) for name in fields}
        for target in TARGETS:
            value = row['targets'].get(target)
            if value is None:
                continue
            counts = value['covered']
            item.update({f'{target}_epochs':value['epochs'],
                         f'{target}_covered_lat':counts[0],
                         f'{target}_covered_lon':counts[1],
                         f'{target}_covered_height':counts[2],
                         f'{target}_whole_recording':all(
                             n == value['epochs'] for n in counts)})
        writer.writerow(item)
    return output.getvalue().encode()


def condition_summary_bytes(report):
    output = io.StringIO()
    fields = ['model', 'profile', 'truth_law', 'sensor_case', 'recordings',
              'technical', 'numerical_passing_fits', 'physical_passing_fits',
              'whole_recording_successes']
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    groups = {}
    for row in report['rows']:
        key = tuple(row[name] for name in fields[:4])
        tally = groups.setdefault(key, dict(zip(fields[:4], key),
                                            recordings=0, technical=0,
                                            numerical_passing_fits=0,
                                            physical_passing_fits=0,
                                            whole_recording_successes=0))
        tally['recordings'] += 1
        tally['technical'] += row['technical']
        tally['numerical_passing_fits'] += row['numerical_passing_fits']
        tally['physical_passing_fits'] += row['physical_passing_fits']
        tally['whole_recording_successes'] += bool(recording_success(row))
    for key in sorted(groups):
        writer.writerow(groups[key])
    return output.getvalue().encode()


def publish(root, *, study_id=STUDY, definition=None, directory=None):
    from lll.studies.artifacts import atomic, encoded
    report = build(root, study_id=study_id, definition=definition)
    directory = (Path(root)/directory if directory else
                 Path(root)/'docs/prediction-simultaneous-law-family')
    atomic(directory/'RESULT.md', render(report).encode())
    atomic(directory/'results.csv', csv_bytes(report))
    atomic(directory/'condition-summary.csv', condition_summary_bytes(report))
    atomic(directory/'verified-report.json', encoded(report))
    return report


if __name__ == '__main__':
    report = publish('.')
    total = report['totals']
    print(f"{total['completed']}/96 audited; technical={total['technical']}; "
          f"coverage_gate={total['coverage_gate_passed']}")
