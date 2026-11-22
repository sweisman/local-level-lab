# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reaudit the sealed fresh-threshold cohort without rerunning simulation."""

import hashlib
import json
import math
from pathlib import Path
from statistics import median


def summarize(rows):
    from .esa_threshold_42_validation import POLICY
    from .esa_integrated_drift_v2_validation import failure_upper_bound

    if ([row.get('seed') for row in rows] != POLICY['seeds'] or
            len({row['seed'] for row in rows}) != len(rows)):
        raise ValueError('exact ordered independent seed set required')
    strata = []
    for vibration in (False, True):
        group = [row for row in rows if row.get('vibration') is vibration]
        if len(group) != POLICY['stratum_histories']:
            raise ValueError('complete generated strata required')
        for row in group:
            if (type(row.get('technical_pass')) is not bool or
                    type(row.get('range_contained')) is not bool):
                raise ValueError('explicit technical and range decisions required')
            if row['technical_pass'] and (
                    type(row.get('maximum_absolute_standardized_error'))
                        not in (int, float) or
                    not math.isfinite(row['maximum_absolute_standardized_error']) or
                    row['maximum_absolute_standardized_error'] < 0 or
                    row['range_contained'] != (
                        row['maximum_absolute_standardized_error'] <=
                        POLICY['simultaneous_z'])):
                raise ValueError('finite score and frozen threshold required')
        failures = sum(not row['technical_pass'] or
                       not row['range_contained'] for row in group)
        strata.append(dict(vibration=vibration, count=len(group),
                           technical_passes=sum(row['technical_pass']
                                                for row in group),
                           failures=failures,
                           upper_failure_probability=failure_upper_bound(
                               failures, len(group),
                               POLICY['one_sided_alpha_per_stratum'])))
    return dict(strata=strata, technical_passes=sum(
                    row['technical_pass'] for row in rows),
                generated_gate_passed=all(
                    item['technical_passes'] == POLICY['stratum_histories'] and
                    item['failures'] <= POLICY['maximum_stratum_failures'] and
                    item['upper_failure_probability'] <=
                        POLICY['maximum_joint_failure_probability']
                    for item in strata),
                median_endpoint_half_width_m=(
                    median(row['endpoint_half_width_m'] for row in rows
                           if row['technical_pass'])
                    if any(row['technical_pass'] for row in rows) else None))


def build(root):
    import numpy as np
    from .esa_threshold_42_validation import ID, POLICY, tasks
    from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import encoded, digest
    from .studies.closed import ClosedStudy

    study = ClosedStudy(root, 'data/'+ID)
    try:
        raw = study.input('policy', raw=True)
        if (json.loads(raw) != POLICY or
                study.manifest['environment'] != runtime_environment() or
                POLICY['generated_case_policy_sha256'] != digest(encoded(CASE_POLICY)) or
                study.summary['total'] != len(tasks()) or
                study.summary['completed'] != len(tasks()) or
                study.summary['state'] != 'complete' or
                {row['identity'] for row in study.manifest['tasks']} !=
                    {row['identity'] for row in tasks()} or
                study.manifest['allocation']['workers'] != 1 or
                study.manifest['allocation']['threads'] != 1):
            raise ValueError('unchanged complete generated cohort required')
        for name, sha in study.manifest['sources'].items():
            study.read('source-freeze/'+name, sha, raw=True)
        rows = []
        for task in tasks():
            seed = task['payload']['seed']
            vibration = task['payload']['vibration']
            row = study.rows[task['identity']]
            if row['status'] != 'complete' or not row['passed']:
                rows.append(dict(seed=seed, vibration=vibration,
                                 technical_pass=False, range_contained=False,
                                 maximum_absolute_standardized_error=None,
                                 endpoint_half_width_m=None))
                continue
            result = study.envelope(task['identity'])['result']
            forecast = study.artifact(task['identity'], 'conditional-forecast.json')
            score = study.artifact(task['identity'], 'outcome.json')
            if (forecast.get('later_receiver_positions_used') is not False or
                    score.get('seed') != seed or
                    score.get('vibration') is not vibration or
                    score.get('validation_policy_sha256') != digest(raw) or
                    score.get('generated_case_policy_sha256') !=
                        POLICY['generated_case_policy_sha256'] or
                    score.get('threshold_z') != POLICY['simultaneous_z'] or
                    score.get('forecast_epochs') != POLICY['forecast_epochs'] or
                    result.get('forecast_epochs') != POLICY['forecast_epochs'] or
                    result.get('original_reads') != 0 or
                    result.get('protected_reads') != 0 or
                    result.get('scientific_decision') != 'abstain'):
                raise ValueError('saved forecast or score lineage changed')
            arrays = [np.asarray(value, float) for value in (
                score['later_residual_neu_m'],
                score['standardized_later_error_neu'],
                forecast['future_mean_neu_m'],
                forecast['future_sigma_neu_m'])]
            residual, standardized, mean, sigma = arrays
            if (any(array.shape != (POLICY['forecast_epochs'], 3) or
                    not np.all(np.isfinite(array)) for array in arrays) or
                    np.any(sigma <= 0)):
                raise ValueError('finite aligned future forecast required')
            np.testing.assert_allclose(standardized, (residual-mean)/sigma,
                                       rtol=1e-12, atol=1e-12)
            maximum = float(np.max(np.abs(standardized)))
            contained = maximum <= POLICY['simultaneous_z']
            if (not math.isclose(maximum,
                    score['maximum_absolute_standardized_error'],
                    rel_tol=1e-12, abs_tol=1e-12) or
                    score['range_contained'] is not contained or
                    result.get('range_contained') is not contained):
                raise ValueError('saved maximum or range decision changed')
            rows.append(dict(seed=seed, vibration=vibration,
                             technical_pass=True, range_contained=contained,
                             maximum_absolute_standardized_error=maximum,
                             endpoint_half_width_m=float(
                                 POLICY['simultaneous_z']*np.max(sigma[-1]))))
        report = summarize(rows)
        report.update(version='esa-generated-threshold-42-report-v1',
                      study_id=ID, completed=study.summary['completed'],
                      total=len(rows), threshold_z=POLICY['simultaneous_z'],
                      rows=rows, policy_sha256=digest(raw),
                      manifest_sha256=digest(study.read('manifest.json', raw=True)),
                      completion_sha256=digest(study.read('completion.json', raw=True)),
                      source_sha256=digest(Path(__file__).read_bytes()),
                      original_reads=0, protected_reads=0,
                      aircraft_coverage_established=False,
                      scientific_decision='abstain')
        return report
    finally:
        study.close()


def publish(root):
    from .esa_threshold_42_validation import HERE
    from .studies.artifacts import atomic, encoded

    result = build(root)
    target = Path(root).resolve()/HERE
    atomic(target/'RESULT.json', encoded(result))
    lines = ['# Fresh generated check of the wider range', '',
        '**{}/{}** histories completed; **{}** passed technical checks.'.format(
            result['completed'], result['total'], result['technical_passes']),
        'The predeclared generated gate **{}**.'.format(
            'passed' if result['generated_gate_passed'] else 'failed'), '',
        '| Generated condition | Whole histories | Failures | Exact 97.5% upper failure bound |',
        '|---|---:|---:|---:|']
    for group in result['strata']:
        lines.append('| {} vibration | {} | {} | {:.2%} |'.format(
            'With' if group['vibration'] else 'Without', group['count'],
            group['failures'], group['upper_failure_probability']))
    lines += ['', 'The threshold is 4.2 standardized units. The median',
        'endpoint per-coordinate half-width was {:.2f} m.'.format(
            result['median_endpoint_half_width_m']), '',
        'This new threshold was selected after the previous generated check',
        'failed. The previous result remains failed. A passing result here',
        'would apply only to this declared simulator, not to real aircraft',
        'or to a three-model scientific decision. Reserved ESA flights remain',
        'closed.', '', '[Frozen plan](PLAN.md) · [machine report](RESULT.json).', '']
    atomic(target/'RESULT.md', '\n'.join(lines).encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'publish'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root) if args.action == 'publish' else build(args.root)
    print(json.dumps({key: result[key] for key in (
        'completed', 'technical_passes', 'generated_gate_passed',
        'scientific_decision')}, sort_keys=True))


if __name__ == '__main__':
    main()
