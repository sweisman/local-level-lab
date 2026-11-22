# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of the independent generated coverage check."""

import hashlib
import json
from pathlib import Path


def _build_study(study):
    import numpy as np
    from .esa_integrated_drift_v2_validation import (
        ID, POLICY, tasks, failure_upper_bound)
    from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
    from .studies.artifacts import encoded
    from . import ilvis0_control_shards as runner

    manifest = runner.verify(study)
    summary = runner.verify_completion(study)
    selected = tasks()
    if (summary['total'] != len(selected) or
            manifest['environment'] != runner.runtime_environment() or
            len(manifest['tasks']) != len(selected)):
        raise ValueError('sealed unchanged generated cohort required')
    raw = (study/manifest['inputs']['policy']['path']).read_bytes()
    policy_sha = hashlib.sha256(raw).hexdigest()
    if (json.loads(raw) != POLICY or
            manifest['inputs']['policy']['sha256'] != policy_sha or
            POLICY['generated_case_policy_sha256'] !=
                hashlib.sha256(encoded(CASE_POLICY)).hexdigest()):
        raise ValueError('fixed law and validation policy changed')
    sealed = {item['identity']: item for item in summary['results']}
    rows = []
    for task in manifest['tasks']:
        requested = {key: value for key, value in task.items()
                     if key not in ('index', 'shard')}
        if requested not in selected:
            raise ValueError('generated task set changed')
        record = sealed.get(task['identity'])
        common = dict(seed=task['payload']['seed'],
                      vibration=task['payload']['vibration'])
        if record is None or not record['passed'] or record['status'] != 'complete':
            rows.append(dict(common, technical_pass=False,
                             simultaneous_95_contained=False,
                             maximum_absolute_standardized_error=None,
                             endpoint_simultaneous_half_width_m=None,
                             forecast_sha256=None, outcome_sha256=None))
            continue
        directory = study/'artifacts'/task['identity']
        forecast_raw = (directory/'conditional-forecast.json').read_bytes()
        outcome_raw = (directory/'outcome.json').read_bytes()
        forecast = json.loads(forecast_raw)
        outcome = json.loads(outcome_raw)
        if (forecast['later_receiver_positions_used'] is not False or
                outcome['seed'] != common['seed'] or
                outcome['vibration'] != common['vibration'] or
                outcome['validation_policy_sha256'] != policy_sha or
                outcome['generated_case_policy_sha256'] !=
                    POLICY['generated_case_policy_sha256'] or
                outcome['forecast_epochs'] != CASE_POLICY['forecast_epochs'] or
                outcome['scientific_decision'] != 'abstain'):
            raise ValueError('saved forecast/outcome lineage changed')
        shape = (CASE_POLICY['forecast_epochs'], 3)
        residual = np.asarray(outcome['later_residual_neu_m'], float)
        standardized = np.asarray(outcome['standardized_later_error_neu'], float)
        mean = np.asarray(forecast['future_mean_neu_m'], float)
        sigma = np.asarray(forecast['future_sigma_neu_m'], float)
        if (any(value.shape != shape or not np.all(np.isfinite(value))
                for value in (residual, standardized, mean, sigma)) or
                np.any(sigma <= 0)):
            raise ValueError('finite aligned saved future comparison required')
        np.testing.assert_allclose(standardized, (residual-mean)/sigma,
                                   rtol=1e-12, atol=1e-12)
        maximum = float(np.max(np.abs(standardized)))
        contained = maximum <= POLICY['simultaneous_95_z']
        if (not np.isclose(maximum,
                            outcome['maximum_absolute_standardized_error']) or
                contained != outcome['simultaneous_95_contained']):
            raise ValueError('saved simultaneous score does not reproduce')
        rows.append(dict(common, technical_pass=True,
                         simultaneous_95_contained=contained,
                         maximum_absolute_standardized_error=maximum,
                         endpoint_simultaneous_half_width_m=float(
                             POLICY['simultaneous_95_z']*np.max(sigma[-1])),
                         forecast_sha256=hashlib.sha256(
                             forecast_raw).hexdigest(),
                         outcome_sha256=hashlib.sha256(
                             outcome_raw).hexdigest()))
    rows.sort(key=lambda item: item['seed'])
    if [row['seed'] for row in rows] != POLICY['seeds']:
        raise ValueError('exact frozen seed identities required')
    strata = []
    for vibration in (False, True):
        group = [row for row in rows if row['vibration'] is vibration]
        if len(group) != POLICY['stratum_histories']:
            raise ValueError('complete fixed generated stratum required')
        failures = sum(not row['technical_pass'] or
                       not row['simultaneous_95_contained'] for row in group)
        strata.append(dict(vibration=vibration, count=len(group),
                           technical_passes=sum(row['technical_pass']
                                                for row in group),
                           simultaneous_failures=failures,
                           failure_upper_97_5= failure_upper_bound(
                               failures, len(group),
                               POLICY['one_sided_alpha_per_stratum'])))
    technical_passes = sum(row['technical_pass'] for row in rows)
    gate = (summary['state'] == 'complete' and
            technical_passes == len(rows) and
            all(item['simultaneous_failures'] <=
                POLICY['maximum_stratum_failures'] and
                item['failure_upper_97_5'] <=
                POLICY['maximum_joint_failure_probability']
                for item in strata))
    return dict(version='esa-generated-integrated-drift-v2-validation-report-v1',
                study_id=ID, completed=summary['completed'], total=len(rows),
                technical_passes=technical_passes, strata=strata,
                generated_gate_passed=gate,
                median_endpoint_simultaneous_half_width_m=(
                    float(np.median([
                        row['endpoint_simultaneous_half_width_m']
                        for row in rows if row['technical_pass']]))
                    if technical_passes else None),
                simultaneous_95_z=POLICY['simultaneous_95_z'],
                rows=rows, policy_sha256=policy_sha,
                manifest_sha256=hashlib.sha256(
                    (study/'manifest.json').read_bytes()).hexdigest(),
                completion_sha256=hashlib.sha256(
                    (study/'completion.json').read_bytes()).hexdigest(),
                report_source_sha256=hashlib.sha256(
                    Path(__file__).read_bytes()).hexdigest(),
                original_reads=0, protected_reads=0,
                aircraft_coverage_established=False,
                scientific_decision='abstain')


def build(root):
    import shutil
    from tempfile import TemporaryDirectory
    from .esa_integrated_drift_v2_validation import ID
    from .studies.artifacts import ArchiveStore
    root = Path(root).resolve()
    store = ArchiveStore(root)
    names = [name for name in store.catalog()['paths']
             if name.startswith('data/'+ID+'/')]
    if not names:
        return _build_study(root/'data'/ID)
    with TemporaryDirectory(prefix='lll-drift-v2-validation-audit-') as temp:
        shutil.copytree(root/'data'/ID, Path(temp)/'data'/ID)
        store.restore(temp, names=names)
        return _build_study(Path(temp)/'data'/ID)


def publish(root):
    from .studies.artifacts import atomic, encoded
    result = build(root)
    target = (Path(root).resolve() /
              'docs/prediction-observed-development/integrated-drift-v2-validation')
    atomic(target/'RESULT.json', encoded(result))
    lines = ['# Independent generated coverage result', '',
             '**{}/{}** tasks were sealed and **{}** passed their technical checks.'.format(
                 result['completed'], result['total'], result['technical_passes']),
             'The predeclared generated coverage gate **{}**.'.format(
                 'passed' if result['generated_gate_passed'] else 'failed'), '',
             '| Generated condition | Whole histories | Failures | Exact 97.5% upper failure bound |',
             '|---|---:|---:|---:|']
    for item in result['strata']:
        lines.append('| {} vibration | {} | {} | {:.2%} |'.format(
            'With' if item['vibration'] else 'Without', item['count'],
            item['simultaneous_failures'], item['failure_upper_97_5']))
    lines += ['',
        'The median per-coordinate half-width at the last withheld second',
        'was {:.2f} m. Coverage alone does not show that this range is'.format(
            result['median_endpoint_simultaneous_half_width_m'])
            if result['median_endpoint_simultaneous_half_width_m'] is not None
            else 'No complete forecast supplied a range width.',
        'narrow enough to distinguish Earth models.', '',
        'The simultaneous threshold was fixed before these seeds were',
        'generated. A technical failure counts as a failed whole history.',
        'The exact bounds assume independent histories from this declared',
        'generator. They do not quantify aircraft coverage, unknown sensor',
        'processing, fitted-law uncertainty or the chance of an incorrect',
        'Earth-model choice. The seven reserved ESA flight groups remained',
        'closed; the scientific decision is abstain.', '',
        '[Frozen plan](PLAN.md) · [machine report](RESULT.json) ·',
        '[candidate design](../INTEGRATED_DRIFT_V2_PLAN.md).', '']
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
