# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed receiver-visible generated motion pairs without refitting."""

import hashlib
import json
from pathlib import Path


def _build_study(study):
    import numpy as np
    from .esa_nonaliased_motion_pilot import ID, POLICY, tasks
    from .esa_integrated_drift_v2_pilot import POLICY as CASE_POLICY
    from .esa_paired_vibration_report import summarize_pairs
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
            summary['total'] != len(tasks()) or
            {row['identity'] for row in manifest['tasks']} !=
                {row['identity'] for row in tasks()}):
        raise ValueError('unchanged sealed nonaliased pilot required')
    sealed = {row['identity']: row for row in summary['results']}
    rows = []
    for task in manifest['tasks']:
        seed = task['payload']['seed']
        record = sealed.get(task['identity'])
        if record is None or not record['passed'] or record['status'] != 'complete':
            rows.append(dict(seed=seed, technical_pass=False,
                max_z_off=None, max_z_on=None,
                contained_off=False, contained_on=False,
                receiver_position_variation_m=None))
            continue
        directory = study/'artifacts'/task['identity']
        forecast_raw = (directory/'forecasts.json').read_bytes()
        outcome_raw = (directory/'outcomes.json').read_bytes()
        forecasts = json.loads(forecast_raw)
        outcome = json.loads(outcome_raw)
        variation = outcome.get('receiver_position_variation_m')
        if (len(forecasts) != 2 or outcome.get('seed') != seed or
                outcome.get('policy_sha256') != policy_sha or
                outcome.get('matched_error_draws') is not True or
                outcome.get('generated_case_policy_sha256') !=
                    POLICY['generated_case_policy_sha256'] or
                type(variation) not in (int, float) or
                not np.isfinite(variation) or
                variation <= POLICY['minimum_receiver_position_variation_m'] or
                outcome.get('original_reads') != 0 or
                outcome.get('protected_reads') != 0 or
                outcome.get('scientific_decision') != 'abstain' or
                len(outcome.get('outcomes', [])) != 2):
            raise ValueError('saved nonaliased pair lineage changed')
        maxima, contained = [], []
        for motion, (forecast, score) in enumerate(
                zip(forecasts, outcome['outcomes'], strict=True)):
            if (score['vibration'] is not bool(motion) or
                    forecast['later_receiver_positions_used'] is not False):
                raise ValueError('paired forecast order changed')
            residual = np.asarray(score['later_residual_neu_m'], float)
            z = np.asarray(score['standardized_later_error_neu'], float)
            mean = np.asarray(forecast['future_mean_neu_m'], float)
            sigma = np.asarray(forecast['future_sigma_neu_m'], float)
            if (any(array.shape != (60, 3) or
                    not np.all(np.isfinite(array))
                    for array in (residual, z, mean, sigma)) or
                    np.any(sigma <= 0)):
                raise ValueError('finite saved nonaliased forecast required')
            np.testing.assert_allclose(z, (residual-mean)/sigma,
                                       rtol=1e-12, atol=1e-12)
            maximum = float(np.max(np.abs(z)))
            inside = maximum <= POLICY['simultaneous_95_z']
            if (not np.isclose(maximum,
                               score['maximum_absolute_standardized_error']) or
                    inside != score['simultaneous_95_contained']):
                raise ValueError('saved nonaliased score changed')
            maxima.append(maximum)
            contained.append(inside)
        rows.append(dict(seed=seed, technical_pass=True,
            max_z_off=maxima[0], max_z_on=maxima[1],
            contained_off=contained[0], contained_on=contained[1],
            receiver_position_variation_m=float(variation),
            forecast_sha256=hashlib.sha256(forecast_raw).hexdigest(),
            outcome_sha256=hashlib.sha256(outcome_raw).hexdigest()))
    rows.sort(key=lambda row: row['seed'])
    if [row['seed'] for row in rows] != POLICY['seeds']:
        raise ValueError('exact fresh nonaliased seed set required')
    result = summarize_pairs(rows)
    result.update(version='esa-generated-nonaliased-motion-report-v1',
        study_id=ID, study_state=summary['state'],
        completed=summary['completed'], rows=rows,
        minimum_receiver_position_variation_m=(
            float(min(row['receiver_position_variation_m']
                      for row in rows if row['technical_pass']))
            if result['technical_passes'] else None),
        policy_sha256=policy_sha,
        manifest_sha256=hashlib.sha256(
            (study/'manifest.json').read_bytes()).hexdigest(),
        completion_sha256=hashlib.sha256(
            (study/'completion.json').read_bytes()).hexdigest(),
        report_source_sha256=hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
        original_reads=0, protected_reads=0, new_earth_model_fits=0)
    return result


def build(root):
    import shutil
    from tempfile import TemporaryDirectory
    from .esa_nonaliased_motion_pilot import ID
    from .studies.artifacts import ArchiveStore

    root = Path(root).resolve()
    study = root/'data'/ID
    store = ArchiveStore(root)
    names = [name for name in store.catalog()['paths']
             if name.startswith('data/'+ID+'/')]
    if not names:
        return _build_study(study)
    with TemporaryDirectory(prefix='lll-nonaliased-motion-audit-') as temp:
        if study.exists():
            shutil.copytree(study, Path(temp)/'data'/ID)
        store.restore(temp, names=names)
        return _build_study(Path(temp)/'data'/ID)


def publish(root):
    from .esa_nonaliased_motion_pilot import HERE
    from .studies.artifacts import atomic, encoded

    result = build(root)
    target = Path(root).resolve()/HERE
    atomic(target/'PILOT_RESULT.json', encoded(result))
    lines = ['# Receiver-visible motion pilot', '',
        '**{}/{}** pairs sealed; **{}** passed technical checks.'.format(
            result['completed'], result['total_pairs'],
            result['technical_passes']), '',
        '| Motion | Whole-history range failures |', '|---|---:|',
        '| Off | {} |'.format(result['failure_counts']['off']),
        '| On | {} |'.format(result['failure_counts']['on']), '',
        'The motion changes receiver-time north position by at least',
        '{:.3f} m peak-to-peak across the tested pairs.'.format(
            result['minimum_receiver_position_variation_m'])
            if result['minimum_receiver_position_variation_m'] is not None
            else 'No technically complete pair measured receiver-time motion.',
        'Discordant pairs: {} fail only with motion; {} fail only'.format(
            result['discordant_pairs']['on_only'],
            result['discordant_pairs']['off_only']),
        'without it. The median on-minus-off change in maximum',
        'standardized error is {:+.4f}; the largest absolute paired'.format(
            result['median_paired_max_z_difference'])
            if result['median_paired_max_z_difference'] is not None
            else 'No complete pair supplied a standardized-error difference.',
        'change is {:.4f}.'.format(
            result['maximum_absolute_paired_max_z_difference'])
            if result['maximum_absolute_paired_max_z_difference'] is not None
            else '', '',
        'This 16-pair generated pilot is descriptive. It does not replace',
        'the failed 256-history coverage gate, calibrate an aircraft error',
        'range, or decide an Earth model. The seven reserved ESA groups',
        'remain closed.', '',
        '[Frozen pilot plan](PILOT_PLAN.md) ·',
        '[machine report](PILOT_RESULT.json).', '']
    atomic(target/'PILOT_RESULT.md', '\n'.join(lines).encode())
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
