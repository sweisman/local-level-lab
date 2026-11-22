# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only report for the fresh matched-noise vibration control."""

import math
import hashlib
import json
from pathlib import Path
from statistics import median


def summarize_pairs(rows):
    """Count matched outcomes; technical failures count against both arms."""
    if not rows or len({row.get('seed') for row in rows}) != len(rows):
        raise ValueError('nonempty unique paired seeds required')
    complete = []
    for row in rows:
        if type(row.get('seed')) is not int or type(row.get('technical_pass')) is not bool:
            raise ValueError('valid seed and technical flag required')
        if row['technical_pass']:
            if (type(row.get('contained_off')) is not bool or
                    type(row.get('contained_on')) is not bool or
                    any(type(row.get(name)) not in (int, float) or
                        not math.isfinite(row[name]) or row[name] < 0
                        for name in ('max_z_off', 'max_z_on'))):
                raise ValueError('finite complete matched scores required')
            complete.append(row)
    return dict(technical_passes=len(complete), total_pairs=len(rows),
        failure_counts={
            'off': sum(not row['technical_pass'] or
                       not row['contained_off'] for row in rows),
            'on': sum(not row['technical_pass'] or
                      not row['contained_on'] for row in rows)},
        discordant_pairs={
            'on_only': sum(row['contained_off'] and
                           not row['contained_on'] for row in complete),
            'off_only': sum(not row['contained_off'] and
                            row['contained_on'] for row in complete)},
        median_paired_max_z_difference=(
            median(row['max_z_on']-row['max_z_off'] for row in complete)
            if complete else None),
        maximum_absolute_paired_max_z_difference=(
            max(abs(row['max_z_on']-row['max_z_off'])
                for row in complete) if complete else None),
        generated_coverage_qualified=False,
        scientific_decision='abstain')


def _build_study(study):
    import numpy as np
    from .esa_paired_vibration_control import ID, POLICY, tasks
    from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
    from .ilvis0_control_shards import verify, verify_completion, runtime_environment
    from .studies.artifacts import encoded

    manifest = verify(study)
    summary = verify_completion(study)
    raw = (study/manifest['inputs']['policy']['path']).read_bytes()
    policy_sha = hashlib.sha256(raw).hexdigest()
    if (manifest['environment'] != runtime_environment() or
            manifest['inputs']['policy']['sha256'] != policy_sha or
            json.loads(raw) != POLICY or
            POLICY['generated_case_policy_sha256'] !=
                hashlib.sha256(encoded(CASE_POLICY)).hexdigest() or
            summary['total'] != 16 or len(manifest['tasks']) != 16 or
            {row['identity'] for row in manifest['tasks']} !=
                {row['identity'] for row in tasks()}):
        raise ValueError('unchanged sealed paired generated study required')
    sealed = {row['identity']: row for row in summary['results']}
    rows = []
    for task in manifest['tasks']:
        seed = task['payload']['seed']
        record = sealed.get(task['identity'])
        if record is None or not record['passed'] or record['status'] != 'complete':
            rows.append(dict(seed=seed, technical_pass=False,
                max_z_off=None, max_z_on=None,
                contained_off=False, contained_on=False))
            continue
        directory = study/'artifacts'/task['identity']
        forecast_raw = (directory/'forecasts.json').read_bytes()
        outcome_raw = (directory/'outcomes.json').read_bytes()
        forecasts = json.loads(forecast_raw)
        outcome = json.loads(outcome_raw)
        if (len(forecasts) != 2 or outcome.get('seed') != seed or
                outcome.get('policy_sha256') != policy_sha or
                outcome.get('matched_error_draws') is not True or
                outcome.get('generated_case_policy_sha256') !=
                    POLICY['generated_case_policy_sha256'] or
                outcome.get('original_reads') != 0 or
                outcome.get('protected_reads') != 0 or
                outcome.get('scientific_decision') != 'abstain' or
                len(outcome.get('outcomes', [])) != 2):
            raise ValueError('saved paired lineage changed')
        maxima = []
        contained = []
        for vibration, (forecast, score) in enumerate(
                zip(forecasts, outcome['outcomes'], strict=True)):
            if (score['vibration'] is not bool(vibration) or
                    forecast['later_receiver_positions_used'] is not False):
                raise ValueError('matched forecast order changed')
            residual = np.asarray(score['later_residual_neu_m'], float)
            z = np.asarray(score['standardized_later_error_neu'], float)
            mean = np.asarray(forecast['future_mean_neu_m'], float)
            sigma = np.asarray(forecast['future_sigma_neu_m'], float)
            if (any(array.shape != (60, 3) or
                    not np.all(np.isfinite(array))
                    for array in (residual, z, mean, sigma)) or
                    np.any(sigma <= 0)):
                raise ValueError('finite saved paired arrays required')
            np.testing.assert_allclose(z, (residual-mean)/sigma,
                                       rtol=1e-12, atol=1e-12)
            maximum = float(np.max(np.abs(z)))
            inside = maximum <= POLICY['simultaneous_95_z']
            if (not np.isclose(maximum,
                               score['maximum_absolute_standardized_error']) or
                    inside != score['simultaneous_95_contained']):
                raise ValueError('saved paired score changed')
            maxima.append(maximum)
            contained.append(inside)
        rows.append(dict(seed=seed, technical_pass=True,
            max_z_off=maxima[0], max_z_on=maxima[1],
            contained_off=contained[0], contained_on=contained[1],
            forecast_sha256=hashlib.sha256(forecast_raw).hexdigest(),
            outcome_sha256=hashlib.sha256(outcome_raw).hexdigest()))
    rows.sort(key=lambda row: row['seed'])
    if [row['seed'] for row in rows] != POLICY['seeds']:
        raise ValueError('exact paired seed set required')
    result = summarize_pairs(rows)
    result.update(version='esa-generated-paired-vibration-report-v1',
        study_id=ID, study_state=summary['state'],
        completed=summary['completed'], rows=rows,
        policy_sha256=policy_sha,
        manifest_sha256=hashlib.sha256(
            (study/'manifest.json').read_bytes()).hexdigest(),
        completion_sha256=hashlib.sha256(
            (study/'completion.json').read_bytes()).hexdigest(),
        report_source_sha256=hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
        new_simulation_pairs=16, new_earth_model_fits=0,
        original_reads=0, protected_reads=0)
    return result


def build(root):
    import shutil
    from tempfile import TemporaryDirectory
    from .esa_paired_vibration_control import ID
    from .studies.artifacts import ArchiveStore

    root = Path(root).resolve()
    study = root/'data'/ID
    store = ArchiveStore(root)
    names = [name for name in store.catalog()['paths']
             if name.startswith('data/'+ID+'/')]
    if not names:
        return _build_study(study)
    with TemporaryDirectory(prefix='lll-paired-vibration-audit-') as temp:
        if study.exists():
            shutil.copytree(study, Path(temp)/'data'/ID)
        store.restore(temp, names=names)
        return _build_study(Path(temp)/'data'/ID)


def publish(root):
    from .esa_paired_vibration_control import HERE
    from .studies.artifacts import atomic, encoded

    result = build(root)
    target = Path(root).resolve()/HERE
    atomic(target/'RESULT.json', encoded(result))
    lines = ['# Paired generated vibration result', '',
        '**{}/{}** pairs are sealed; **{}** passed technical checks.'.format(
            result['completed'], result['total_pairs'],
            result['technical_passes']), '',
        '| Motion | Whole-history range failures |', '|---|---:|',
        '| Without vibration | {} |'.format(result['failure_counts']['off']),
        '| With vibration | {} |'.format(result['failure_counts']['on']), '',
        'Discordant pairs: {} failed only with vibration; {} failed only'.format(
            result['discordant_pairs']['on_only'],
            result['discordant_pairs']['off_only']),
        'without vibration. The median paired difference in maximum',
        'standardized error (on minus off) is {:+.6f}; the largest'.format(
            result['median_paired_max_z_difference'])
            if result['median_paired_max_z_difference'] is not None
            else 'No complete pair supplied a standardized-error difference.',
        'absolute paired difference is {:.6f}.'.format(
            result['maximum_absolute_paired_max_z_difference'])
            if result['maximum_absolute_paired_max_z_difference'] is not None
            else '',
        '', 'In this generator, the 10 Hz vibration repeats at every integer',
        'second when the receiver reports. Its position perturbation is a',
        'constant 0.0002 m north offset and its pitch perturbation is zero',
        'at those reports. This helps explain why this matched control offers',
        'little vibration stress at the scored receiver times.', '',
        'The two motion cases used identical generated sensor and receiver',
        'error draws within each seed. This post-outcome diagnostic cannot',
        'replace the failed 256-case coverage gate or establish aircraft',
        'prediction coverage. No Earth model was fitted; the decision is',
        '**abstain**.', '',
        '[Study plan](PLAN.md) · [machine report](RESULT.json).', '']
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
        'completed', 'technical_passes', 'failure_counts',
        'discordant_pairs', 'scientific_decision')}, sort_keys=True))


if __name__ == '__main__':
    main()
