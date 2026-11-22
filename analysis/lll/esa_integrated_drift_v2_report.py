# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of the fresh-seed changing-gyro-bias pilot."""

import hashlib
import json
from pathlib import Path


def _build_study(study):
    import numpy as np
    from .esa_integrated_drift_v2_pilot import ID, POLICY, tasks
    from . import ilvis0_control_shards as runner

    manifest = runner.verify(study)
    summary = runner.verify_completion(study)
    if (summary['state'] != 'complete' or
            summary['completed'] != summary['total'] or
            summary['total'] != len(tasks()) or
            summary['passed'] is not True or
            manifest['environment'] != runner.runtime_environment()):
        raise ValueError('complete unchanged generated pilot required')
    policy_raw = (study/manifest['inputs']['policy']['path']).read_bytes()
    policy_hash = hashlib.sha256(policy_raw).hexdigest()
    if (json.loads(policy_raw) != POLICY or
            manifest['inputs']['policy']['sha256'] != policy_hash):
        raise ValueError('unchanged fixed candidate policy required')
    selected = tasks()
    rows = []
    for task in manifest['tasks']:
        requested = {key: value for key, value in task.items()
                     if key not in ('index', 'shard')}
        if requested not in selected:
            raise ValueError('declared task set changed')
        directory = study/'artifacts'/task['identity']
        forecast_path = directory/'conditional-forecast.json'
        outcome_path = directory/'outcome.json'
        forecast_raw = forecast_path.read_bytes()
        outcome_raw = outcome_path.read_bytes()
        forecast = json.loads(forecast_raw)
        outcome = json.loads(outcome_raw)
        if (forecast['later_receiver_positions_used'] is not False or
                forecast['forecast_epochs'] != POLICY['forecast_epochs'] or
                outcome['forecast_epochs'] != POLICY['forecast_epochs'] or
                outcome['seed'] != task['payload']['seed'] or
                outcome['vibration'] != task['payload']['vibration'] or
                outcome['policy_sha256'] != policy_hash or
                outcome['scientific_decision'] != 'abstain'):
            raise ValueError('saved forecast or outcome lineage changed')
        shape = (POLICY['forecast_epochs'], 3)
        residual = np.asarray(outcome['later_residual_neu_m'], float)
        standardized = np.asarray(outcome['standardized_later_error_neu'], float)
        mean = np.asarray(forecast['future_mean_neu_m'], float)
        sigma = np.asarray(forecast['future_sigma_neu_m'], float)
        if (any(value.shape != shape or not np.all(np.isfinite(value))
                for value in (residual, standardized, mean, sigma)) or
                np.any(sigma <= 0)):
            raise ValueError('complete finite saved future comparison required')
        np.testing.assert_allclose(standardized, (residual-mean)/sigma,
                                   rtol=1e-12, atol=1e-12)
        maximum = float(np.max(np.abs(standardized)))
        fraction = np.mean(np.abs(standardized) <= POLICY['nominal_z_95'],
                           axis=0)
        marginal = maximum <= POLICY['nominal_z_95']
        simultaneous = maximum <= POLICY['simultaneous_95_z']
        if (not np.isclose(maximum,
                            outcome['maximum_absolute_standardized_error']) or
                not np.allclose(fraction, outcome['marginal_95_fraction_neu']) or
                marginal != outcome['whole_period_marginal_95_contained'] or
                simultaneous != outcome['simultaneous_95_contained']):
            raise ValueError('saved score does not reproduce')
        rows.append(dict(seed=outcome['seed'],
                         vibration=outcome['vibration'],
                         maximum_absolute_standardized_error=maximum,
                         weakest_axis_marginal_95_fraction=float(min(fraction)),
                         whole_period_marginal_95_contained=marginal,
                         simultaneous_95_contained=simultaneous,
                         forecast_sha256=hashlib.sha256(forecast_raw).hexdigest(),
                         outcome_sha256=hashlib.sha256(outcome_raw).hexdigest()))
    rows.sort(key=lambda row: row['seed'])
    if [row['seed'] for row in rows] != POLICY['seeds']:
        raise ValueError('one result per preassigned generated seed required')
    return dict(version='esa-generated-integrated-drift-v2-report-v1',
                study_id=ID, completed=len(rows), total=len(selected),
                technical_passes=summary['completed'],
                whole_period_marginal_95_contained=sum(
                    row['whole_period_marginal_95_contained'] for row in rows),
                simultaneous_95_contained=sum(
                    row['simultaneous_95_contained'] for row in rows),
                simultaneous_95_z=POLICY['simultaneous_95_z'],
                maximum_absolute_standardized_error=max(
                    row['maximum_absolute_standardized_error'] for row in rows),
                rows=rows, policy_sha256=policy_hash,
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
    """Verify saved receipts, restoring compacted evidence only into scratch."""
    import shutil
    from tempfile import TemporaryDirectory
    from .esa_integrated_drift_v2_pilot import ID
    from .studies.artifacts import ArchiveStore
    root = Path(root).resolve()
    store = ArchiveStore(root)
    prefix = 'data/'+ID+'/'
    names = [name for name in store.catalog()['paths'] if name.startswith(prefix)]
    if not names:
        return _build_study(root/'data'/ID)
    with TemporaryDirectory(prefix='lll-drift-v2-audit-') as temporary:
        shutil.copytree(root/'data'/ID, Path(temporary)/'data'/ID)
        store.restore(temporary, names=names)
        return _build_study(Path(temporary)/'data'/ID)


def publish(root):
    from .studies.artifacts import atomic, encoded
    result = build(root)
    target = (Path(root).resolve() /
              'docs/prediction-observed-development/integrated-drift-v2-pilot')
    atomic(target/'RESULT.json', encoded(result))
    lines = [
        '# Fresh-seed changing-gyro-bias pilot result', '',
        'All **{}/{}** frozen technical tasks completed.'.format(
            result['completed'], result['total']),
        'Whole-period containment was **{}/{}** under nominal marginal'.format(
            result['whole_period_marginal_95_contained'], result['total']),
        '95% ranges and **{}/{}** under the predeclared conservative'.format(
            result['simultaneous_95_contained'], result['total']),
        'simultaneous 95% bound. The latter uses a {:.3f}-standard-deviation'.format(
            result['simultaneous_95_z']),
        'threshold across 180 future coordinates.', '',
        '| Seed | Vibration | Largest standardized error | Weakest marginal fraction | Simultaneous bound? |',
        '|---|---|---:|---:|---|']
    for row in result['rows']:
        lines.append('| {} | {} | {:.2f} | {:.1%} | {} |'.format(
            row['seed'], 'yes' if row['vibration'] else 'no',
            row['maximum_absolute_standardized_error'],
            row['weakest_axis_marginal_95_fraction'],
            'inside' if row['simultaneous_95_contained'] else 'outside'))
    lines += ['',
        'These are independent generated histories with true initial',
        'inertial state supplied. The snap intensity was fixed from the',
        'generator’s declared gyro-bias diffusion before these seeds were',
        'scored. Sixteen histories do not calibrate a coverage rate, test',
        'aircraft error, or decide among Earth models. The seven reserved',
        'ESA flight groups remained closed. Numerical and scientific',
        'outcomes are kept separate.', '',
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
        'completed', 'simultaneous_95_contained',
        'maximum_absolute_standardized_error', 'scientific_decision')},
        sort_keys=True))


if __name__ == '__main__':
    main()
