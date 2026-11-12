# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only parameter and forecast comparison for failed ESA tangent pairs."""
import json
from pathlib import Path


def summarize(rows, fit, forecast):
    """Describe failed pairs using only their sealed fit and forecast artifacts."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    if not isinstance(rows, list) or not rows:
        raise ValueError('nonempty verified paired rows required')
    failed = [row for row in rows if row.get('passed') is False]
    if not failed or len({row.get('identity') for row in failed}) != len(failed):
        raise ValueError('distinct failed paired identities required')
    pairs = []
    for row in failed:
        identity = row['identity']
        fitted = {name: fit(identity, name) for name in ('wide', 'hybrid')}
        forecasts = {name: forecast(identity, name) for name in ('wide', 'hybrid')}
        active = fitted['wide'].get('active_parameters')
        if (not isinstance(active, list) or not active or
                any(fitted[name].get('active_parameters') != active or
                    forecasts[name].get('active_parameters') != active
                    for name in ('wide', 'hybrid'))):
            raise ValueError('identical active parameter columns required')
        points = {name: np.asarray(fitted[name].get('normalized_parameters'), float)
                  for name in ('wide', 'hybrid')}
        if any(point.shape != (len(active),) or not np.all(np.isfinite(point))
               for point in points.values()):
            raise ValueError('complete finite saved parameter points required')
        times = forecasts['wide'].get('times_s')
        if times != forecasts['hybrid'].get('times_s') or not isinstance(times, list):
            raise ValueError('matching saved forecast times required')
        difference = receiver_errors(forecasts['hybrid']['coordinates'],
                                     forecasts['wide']['coordinates'])
        if len(times) != len(difference):
            raise ValueError('forecast time and coordinate lengths differ')
        norm = np.linalg.norm(difference, axis=1)
        maximum_epoch = int(np.argmax(norm))
        parameter_difference = np.abs(points['hybrid'] - points['wide'])
        parameter_index = int(np.argmax(parameter_difference))
        pairs.append(dict(
            identity=identity,
            wide=dict(converged=fitted['wide']['converged'],
                      termination=fitted['wide']['termination'],
                      evaluations=fitted['wide']['evaluations'],
                      training_cost=fitted['wide']['residual_sum_squares']),
            hybrid=dict(converged=fitted['hybrid']['converged'],
                        termination=fitted['hybrid']['termination'],
                        evaluations=fitted['hybrid']['evaluations'],
                        training_cost=fitted['hybrid']['residual_sum_squares']),
            same_active_bounds=fitted['wide']['active_bounds'] ==
                               fitted['hybrid']['active_bounds'],
            maximum_parameter_difference=dict(
                name=active[parameter_index],
                normalized=float(parameter_difference[parameter_index])),
            median_forecast_difference_m=float(np.median(norm)),
            p95_forecast_difference_m=float(np.percentile(norm, 95)),
            maximum_forecast_difference_m=float(norm[maximum_epoch]),
            maximum_epoch=maximum_epoch,
            maximum_time_s=float(times[maximum_epoch]),
            final_neu_difference_m=difference[-1].tolist()))
    return dict(version='esa-hybrid-failure-diagnostic-v1',
                failed_pairs=len(pairs), pairs=pairs,
                new_fits=0, original_reads=0, protected_reads=0,
                method_substitution_requalified=False,
                scientific_decision='abstain')


def inspect(root):
    """Verify the 24-case publication and read only selected sealed artifacts."""
    from .airquantumgrav_observed_hybrid_combined_audit import (
        CombinedStudy, verify_publication)
    from .studies.combined_task_evidence import inspect as inspect_lineage
    from .studies.artifacts import digest

    root = Path(root).resolve()
    receipt = verify_publication(root)
    raw = (root/'docs/esa-observed-hybrid/combined/verified-report.json').read_bytes()
    report = json.loads(raw)
    if (report.get('verified') is not True or report.get('total') != 24 or
            report.get('returned') != 24 or report.get('qualified') is not False or
            len(report.get('rows', ())) != 24 or report.get('passed') != 21):
        raise ValueError('complete unqualified 24-case ESA report required')
    ledger = inspect_lineage(root, root/'data/esa-observed-hybrid-continuation-20261111')
    view = CombinedStudy(root, ledger)
    try:
        result = summarize(
            report['rows'],
            lambda identity, variant: view.artifact(identity, variant+'-fit.json'),
            lambda identity, variant: view.artifact(identity, variant+'-forecast.json'))
    finally:
        view.close()
    result.update(combined_report_sha256=digest(raw),
                  combined_receipt_sha256=receipt['receipt_sha256'],
                  source_sha256=digest(Path(__file__).read_bytes()))
    return result


def main():
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    args = parser.parse_args()
    root = Path(args.project).resolve()
    result = inspect(root)
    target = root/'docs/esa-observed-hybrid'
    atomic(target/'FAILURE_DIAGNOSTIC.json', encoded(result))
    lines = ['# Saved-fit ESA method failures', '',
             'The faster tangent method remains unqualified: 21 of 24 paired',
             'cases passed its original gate. This diagnostic reads only sealed',
             'fit and forecast artifacts; it makes no new fits or scientific',
             'decision.', '',
             '| Case | Wide / faster evaluations | Largest parameter difference | Largest forecast difference |',
             '|---|---:|---|---:|']
    for row in result['pairs']:
        parameter = row['maximum_parameter_difference']
        lines.append(f"| {row['identity']} | {row['wide']['evaluations']} / "
                     f"{row['hybrid']['evaluations']} | {parameter['name']} "
                     f"({parameter['normalized']:.6g} normalized) | "
                     f"{row['maximum_forecast_difference_m']:.6g} m |")
    lines += ['', 'Parameter differences describe the optimizer outcomes; they',
              'do not identify which derivative column caused them. A same-point',
              'column comparison is still needed before revising the method.', '',
              '[Original gate](combined/README.md) · '
              '[Machine-readable measurements](FAILURE_DIAGNOSTIC.json).', '']
    atomic(target/'FAILURE_DIAGNOSTIC.md', '\n'.join(lines).encode())
    print(json.dumps(dict(failed_pairs=result['failed_pairs'], new_fits=0)))


if __name__ == '__main__':
    main()
