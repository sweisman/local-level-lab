# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of the finite generated changing-drift pilot."""

import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist


def _build_study(study):
    import numpy as np
    from .esa_integrated_drift_pilot import ID, POLICY, tasks
    from . import ilvis0_control_shards as runner

    manifest = runner.verify(study)
    summary = runner.verify_completion(study)
    if (summary['state'] != 'complete' or summary['completed'] !=
            summary['total'] or summary['total'] != len(tasks()) or
            summary['passed'] is not True or
            manifest['environment'] != runner.runtime_environment() or
            len(manifest['tasks']) != len(tasks())):
        raise ValueError('complete unchanged generated pilot required')
    policy_raw = (study/manifest['inputs']['policy']['path']).read_bytes()
    policy_hash = hashlib.sha256(policy_raw).hexdigest()
    if (json.loads(policy_raw) != POLICY or
            manifest['inputs']['policy']['sha256'] != policy_hash):
        raise ValueError('unchanged fixed candidate policy required')
    # Union bound: 60 future epochs × 3 coordinates × 2 Gaussian tails.
    # This is a saved-data diagnostic, not the frozen pilot's acceptance rule.
    simultaneous_z = NormalDist().inv_cdf(
        1 - .05/(2*POLICY['forecast_epochs']*3))
    rows = []
    for task in manifest['tasks']:
        if {k: v for k, v in task.items() if k not in ('index', 'shard')} not in tasks():
            raise ValueError('declared task set changed')
        directory = study/'artifacts'/task['identity']
        forecast_path = directory/'conditional-forecast.json'
        outcome_path = directory/'outcome.json'
        forecast = json.loads(forecast_path.read_bytes())
        outcome = json.loads(outcome_path.read_bytes())
        if (forecast['later_receiver_positions_used'] is not False or
                forecast['forecast_epochs'] != POLICY['forecast_epochs'] or
                outcome['forecast_epochs'] != POLICY['forecast_epochs'] or
                outcome['seed'] != task['payload']['seed'] or
                outcome['vibration'] != task['payload']['vibration'] or
                outcome['policy_sha256'] != policy_hash or
                outcome['scientific_decision'] != 'abstain'):
            raise ValueError('saved forecast or outcome lineage changed')
        residual = np.asarray(outcome['later_residual_neu_m'], float)
        standardized = np.asarray(outcome['standardized_later_error_neu'], float)
        mean = np.asarray(forecast['future_mean_neu_m'], float)
        sigma = np.asarray(forecast['future_sigma_neu_m'], float)
        shape = (POLICY['forecast_epochs'], 3)
        if (any(value.shape != shape or not np.all(np.isfinite(value))
                for value in (residual, standardized, mean, sigma)) or
                np.any(sigma <= 0)):
            raise ValueError('complete finite saved future comparison required')
        np.testing.assert_allclose(standardized, (residual-mean)/sigma,
                                   rtol=1e-12, atol=1e-12)
        inside = np.abs(standardized) <= POLICY['nominal_z_95']
        maximum = float(np.max(np.abs(standardized)))
        fractions = np.mean(inside, axis=0)
        if (not np.isclose(maximum,
                            outcome['maximum_absolute_standardized_error']) or
                not np.allclose(fractions, outcome['marginal_95_fraction_neu']) or
                bool(np.all(inside)) != outcome['whole_period_95_contained']):
            raise ValueError('saved score does not reproduce')
        rows.append(dict(seed=outcome['seed'],
                         vibration=outcome['vibration'],
                         maximum_absolute_standardized_error=maximum,
                         marginal_95_fraction_neu=fractions.tolist(),
                         whole_period_95_contained=bool(np.all(inside)),
                         bonferroni_95_contained=maximum <= simultaneous_z,
                         forecast_sha256=hashlib.sha256(
                             forecast_path.read_bytes()).hexdigest(),
                         outcome_sha256=hashlib.sha256(
                             outcome_path.read_bytes()).hexdigest()))
    rows.sort(key=lambda row: row['seed'])
    if [row['seed'] for row in rows] != POLICY['seeds']:
        raise ValueError('one result per preassigned generated seed required')
    return dict(version='esa-generated-integrated-drift-pilot-report-v1',
                study_id=ID, completed=len(rows), total=len(tasks()),
                technical_passes=summary['completed'],
                whole_period_95_contained=sum(
                    row['whole_period_95_contained'] for row in rows),
                bonferroni_simultaneous_z=simultaneous_z,
                bonferroni_95_contained=sum(
                    row['bonferroni_95_contained'] for row in rows),
                bonferroni_exceedance_count=sum(
                    not row['bonferroni_95_contained'] for row in rows),
                bonferroni_eight_case_tail_bound=sum(
                    math.comb(len(rows), k)*.05**k*.95**(len(rows)-k)
                    for k in range(2, len(rows)+1)),
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
                law_adequacy_qualified=False,
                aircraft_coverage_established=False,
                scientific_decision='abstain')


def build(root):
    """Verify saved receipts, restoring compacted evidence only into scratch."""
    import shutil
    from tempfile import TemporaryDirectory
    from .esa_integrated_drift_pilot import ID
    from .studies.artifacts import ArchiveStore
    root = Path(root).resolve()
    store = ArchiveStore(root)
    prefix = 'data/'+ID+'/'
    names = [name for name in store.catalog()['paths'] if name.startswith(prefix)]
    if not names:
        return _build_study(root/'data'/ID)
    with TemporaryDirectory(prefix='lll-drift-pilot-audit-') as temporary:
        shutil.copytree(root/'data'/ID, Path(temporary)/'data'/ID)
        store.restore(temporary, names=names)
        return _build_study(Path(temporary)/'data'/ID)


def publish(root):
    from .studies.artifacts import atomic, encoded
    result = build(root)
    target = Path(root).resolve()/'docs/prediction-observed-development/integrated-drift-pilot'
    atomic(target/'RESULT.json', encoded(result))
    lines = [
        '# Generated changing-drift pilot result', '',
        'All **8/8** frozen software tasks completed without a technical error.',
        'The fixed candidate contained every withheld coordinate inside its',
        'nominal 95% marginal range in **{}/8** generated histories. This is'.format(
            result['whole_period_95_contained']),
        'a development stress result, not a calibrated 95% coverage rate.', '',
        'A separate, conservative simultaneous 95% Gaussian union bound for',
        'the 180 later coordinates has a {:.3f}-standard-deviation threshold.'.format(
            result['bonferroni_simultaneous_z']),
        '**{}/8** histories remain inside it; two exceed it. Even if the'.format(
            result['bonferroni_95_contained']),
        'law were correct and the eight generated seeds independent, a',
        'two-or-more-exceedance count has probability bounded by {:.1%}.'.format(
            result['bonferroni_eight_case_tail_bound']),
        'This check was added after the frozen pilot, and does not establish',
        'a formal rejection or an aircraft coverage claim.', '',
        '| Seed | Physical vibration | Largest standardized later error | Weakest axis: fraction inside nominal range | Whole period inside? |',
        '|---|---|---:|---:|---|']
    for row in result['rows']:
        lines.append('| {} | {} | {:.2f} | {:.1%} | {} |'.format(
            row['seed'], 'yes' if row['vibration'] else 'no',
            row['maximum_absolute_standardized_error'],
            min(row['marginal_95_fraction_neu']),
            'yes' if row['whole_period_95_contained'] else 'no'))
    lines += ['',
        'The generator supplied the true starting state and the candidate used',
        'its **declared** white-force, changing-force and receiver-error scales.',
        'The generated gyro-bias walk is not fully represented by this law;',
        'physical vibration and channel coupling are also present. The',
        'observed misses leave the fixed candidate unqualified for this',
        'generated mixture. Nominal marginal intervals did not promise',
        '95% simultaneous containment, and eight draws do not calibrate',
        'a coverage rate. They do not identify which omitted component caused',
        'each miss. No parameter was changed after looking at these eight draws.', '',
        'A revised candidate needs a separate frozen seed cohort and must',
        'retain the original failed result. The seven reserved ESA flight',
        'groups were not opened. No Earth-model decision is made.', '',
        '[Frozen plan](PLAN.md) · [machine report](RESULT.json) ·',
        '[error-law roadmap](../OBSERVED_ERROR_PLAN.md).', '']
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
        'completed', 'whole_period_95_contained',
        'maximum_absolute_standardized_error', 'scientific_decision')},
        sort_keys=True))


if __name__ == '__main__':
    main()
