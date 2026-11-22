# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate saved generated coverage misses without replaying a simulation."""

import hashlib
import json
from pathlib import Path


def build(root):
    import numpy as np
    from scipy.stats import fisher_exact
    from .esa_integrated_drift_v2_validation import ID, POLICY
    from .studies.artifacts import ArchiveStore

    root = Path(root).resolve()
    source = (root/'docs/prediction-observed-development/'
              'integrated-drift-v2-validation/RESULT.json')
    raw = source.read_bytes()
    result = json.loads(raw)
    if (result['study_id'] != ID or result['total'] != 256 or
            result['completed'] != 256 or result['technical_passes'] != 256 or
            result['generated_gate_passed'] is not False or
            result['simultaneous_95_z'] != POLICY['simultaneous_95_z']):
        raise ValueError('verified closed generated failure result required')
    rows = result['rows']
    failures = [row for row in rows if not row['simultaneous_95_contained']]
    if (len(rows) != 256 or len(failures) != 4 or
            any(not row['technical_pass'] or not row['vibration']
                for row in failures)):
        raise ValueError('expected sealed four-vibration-failure cohort required')
    archive = ArchiveStore(root)
    catalog = archive.catalog()
    located = []
    for row in failures:
        base = f'data/{ID}/artifacts/seed-{row["seed"]}'
        outcome_raw = archive._read(base+'/outcome.json', catalog)
        forecast_raw = archive._read(base+'/conditional-forecast.json', catalog)
        if (hashlib.sha256(outcome_raw).hexdigest() !=
                row['outcome_sha256'] or
                hashlib.sha256(forecast_raw).hexdigest() !=
                row['forecast_sha256']):
            raise ValueError('archived failure artifact hash changed')
        outcome = json.loads(outcome_raw)
        forecast = json.loads(forecast_raw)
        z = np.asarray(outcome['standardized_later_error_neu'], float)
        sigma = np.asarray(forecast['future_sigma_neu_m'], float)
        residual = np.asarray(outcome['later_residual_neu_m'], float)
        mean = np.asarray(forecast['future_mean_neu_m'], float)
        if (any(value.shape != (60, 3) or not np.all(np.isfinite(value))
                for value in (z, sigma, residual, mean)) or
                np.any(sigma <= 0)):
            raise ValueError('finite aligned saved failure arrays required')
        np.testing.assert_allclose(z, (residual-mean)/sigma,
                                   rtol=1e-12, atol=1e-12)
        index = np.unravel_index(np.abs(z).argmax(), z.shape)
        maximum = float(abs(z[index]))
        if (not np.isclose(maximum,
                            row['maximum_absolute_standardized_error']) or
                maximum <= POLICY['simultaneous_95_z']):
            raise ValueError('failure maximum no longer reproduces')
        located.append(dict(seed=row['seed'],
            withheld_second=int(index[0]+POLICY['training_epochs']),
            axis='NEU'[index[1]],
            signed_standardized_error=float(z[index]),
            assigned_standard_deviation_m=float(sigma[index]),
            absolute_prediction_error_m=float(abs(residual[index]-mean[index]))))
    located.sort(key=lambda row: row['seed'])
    first_second = {False: [], True: []}
    for row in rows:
        name = f'data/{ID}/artifacts/seed-{row["seed"]}/outcome.json'
        outcome_raw = archive._read(name, catalog)
        if hashlib.sha256(outcome_raw).hexdigest() != row['outcome_sha256']:
            raise ValueError('archived outcome hash changed')
        outcome = json.loads(outcome_raw)
        z = np.asarray(outcome['standardized_later_error_neu'], float)
        if z.shape != (60, 3) or not np.all(np.isfinite(z)):
            raise ValueError('complete finite saved standardized errors required')
        first_second[row['vibration']].append(z[0])
    early = []
    for vibration in (False, True):
        values = np.asarray(first_second[vibration], float)
        if values.shape != (128, 3):
            raise ValueError('128 complete histories per stratum required')
        early.append(dict(vibration=vibration,
                          first_second_mean_z_neu=np.mean(values, axis=0).tolist(),
                          first_second_rms_z_neu=np.sqrt(
                              np.mean(values*values, axis=0)).tolist()))
    medians = {str(vibration).lower(): float(np.median([
        row['maximum_absolute_standardized_error'] for row in rows
        if row['vibration'] is vibration])) for vibration in (False, True)}
    # Exploratory association after seeing the frozen outcome, not a gate.
    association_p = float(fisher_exact([[4, 124], [0, 128]],
                                       alternative='greater').pvalue)
    return dict(version='esa-vibration-failure-diagnostic-v1',
                parent_result_sha256=hashlib.sha256(raw).hexdigest(),
                report_source_sha256=hashlib.sha256(
                    Path(__file__).read_bytes()).hexdigest(),
                failures=located,
                early_standardized_error=early,
                median_maximum_standardized_error=medians,
                exploratory_one_sided_fisher_p=association_p,
                new_simulations=0, new_fits=0, original_reads=0,
                protected_reads=0, scientific_decision='abstain')


def publish(root):
    from .studies.artifacts import atomic, encoded
    result = build(root)
    target = (Path(root).resolve() /
              'docs/prediction-observed-development/integrated-drift-v2-validation')
    atomic(target/'VIBRATION_DIAGNOSTIC.json', encoded(result))
    lines = ['# Saved vibration-failure diagnosis', '',
             'The [frozen generated check](RESULT.md) had four whole-history',
             'exceedances, all in its 128-case vibration stratum. This report',
             'reads only their archived forecasts and scores. It makes no new',
             'simulation or fit.', '',
             '| Seed | Second | Axis | Signed standardized error | Assigned σ | Absolute error |',
             '|---|---:|---|---:|---:|---:|']
    for row in result['failures']:
        lines.append('| {} | {} | {} | {:+.3f} | {:.4f} m | {:.4f} m |'.format(
            row['seed'], row['withheld_second'], row['axis'],
            row['signed_standardized_error'],
            row['assigned_standard_deviation_m'],
            row['absolute_prediction_error_m']))
    lines += ['',
        'Three maxima occur at the first withheld second (61); the fourth',
        'at second 69. The largest standardized error is concentrated near',
        'the forecast boundary, not at the 120-second endpoint. The median',
        'whole-history maximum is {:.3f} without vibration and {:.3f} with'.format(
            result['median_maximum_standardized_error']['false'],
            result['median_maximum_standardized_error']['true']),
        'vibration. A one-sided Fisher comparison of four versus zero tail',
        'counts gives p ≈ {:.3f}; this exploratory, post-outcome comparison'.format(
            result['exploratory_one_sided_fisher_p']),
        'does not establish vibration as the cause. The fixed error law',
        'still failed its predeclared generated coverage gate.', '',
        'At the first withheld second, standardized error RMS is close to',
        'one in each coordinate for both 128-case strata:', '',
        '| Physical vibration | North RMS | East RMS | Up RMS |',
        '|---|---:|---:|---:|']
    for row in result['early_standardized_error']:
        lines.append('| {} | {:.3f} | {:.3f} | {:.3f} |'.format(
            'on' if row['vibration'] else 'off',
            *row['first_second_rms_z_neu']))
    lines += ['',
        'This does not show a broad first-second variance deficit. Four',
        'tail events still prevented the frozen confidence gate from',
        'certifying a failure probability below 5% for the vibration',
        'stratum. A true rate below 5% remains compatible with these data.', '',
        'The separate [clean 100 Hz control](CLEAN_PROPAGATION.md) finds',
        'integration error below 0.0004 m in both motion modes. Next: use',
        'fresh paired noise controls to examine the vibration association',
        'and assess whether the accepted range can distinguish models.',
        'Any changed law needs its own source freeze and new seeds.',
        'Aircraft coverage remains unqualified.', '',
        '[Machine report](VIBRATION_DIAGNOSTIC.json) · [frozen plan](PLAN.md).', '']
    atomic(target/'VIBRATION_DIAGNOSTIC.md', '\n'.join(lines).encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'publish'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root) if args.action == 'publish' else build(args.root)
    print(json.dumps({key: result[key] for key in (
        'new_simulations', 'new_fits', 'exploratory_one_sided_fisher_p',
        'scientific_decision')}, sort_keys=True))


if __name__ == '__main__':
    main()
