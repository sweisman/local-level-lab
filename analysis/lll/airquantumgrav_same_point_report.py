# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the sealed ESA same-point tangent diagnosis without refitting."""
import json
from pathlib import Path


def render(report):
    if (report.get('verified') is not True or report.get('complete') != 3 or
            report.get('total') != 3 or len(report.get('rows', ())) != 3 or
            report.get('charged', {}).get('native_calls') != 12 or
            report['charged'].get('packet_visits') != 2302723200 or
            report.get('original_reads') != 0 or report.get('protected_reads') != 0 or
            report.get('method_substitution_requalified') is not False or
            any(row.get('complete') is not True or
                set(row.get('comparisons', ())) != {'wide', 'hybrid'}
                for row in report['rows'])):
        raise ValueError('complete verified nonfitting three-task report required')
    lines = ['# ESA same-point derivative check', '',
             '**12 of 12 charged native evaluations completed. The faster method remains unqualified.**',
             '',
             'Both tangent methods were evaluated at each of the two saved fit',
             'points in each of the three failed pairs. All six same-point',
             'position predictions are bitwise identical, and boundary counts',
             'match. The differences below are in the derivatives that guide',
             'the optimizer, expressed as metres of predicted position per',
             'one normalized parameter unit.', '',
             '| Failed pair | Saved point | Largest column | Largest difference |',
             '|---|---|---|---:|']
    for row in report['rows']:
        for point in ('wide', 'hybrid'):
            comparison = row['comparisons'][point]
            if (comparison.get('values_bitwise_identical') is not True or
                    comparison.get('boundary_counts_identical') is not True or
                    comparison.get('maximum_position_difference_m') != 0.):
                raise ValueError('same-point value and boundary agreement required')
            largest = comparison['largest_column']
            lines.append(f"| {row['identity']} | {point} | {largest['name']} | "
                         f"{largest['maximum_difference_m_per_normalized_unit']:.3g} m |")
    lines += ['', 'The largest derivative differences are about one micrometre',
              'per normalized parameter unit. This diagnostic makes no new fits',
              'and does not show that a revised optimizer would pass the original',
              '24-pair substitution gate. The saved fits have weak numerical',
              'directions; tiny derivative changes may alter which point the',
              'optimizer reaches. That explanation still needs a separately',
              'qualified method test.', '',
              'The first three-task diagnostic ended with direct-loader errors',
              'before any native calculation. Its zero-call failure is retained;',
              'this result comes from a new frozen allowance with corrected',
              'source and an added direct-loader test.', '',
              '[Original failed substitution](../combined/README.md) · '
              '[Saved-fit comparison](../FAILURE_DIAGNOSTIC.md) · '
              '[Detailed verified measurements](verified-report.json).', '']
    return '\n'.join(lines)


def build(root):
    from .airquantumgrav_same_point_study import inspect
    from .airquantumgrav_observed_hybrid_failure_diagnostic import inspect as fit_inspect
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    report = inspect(root, 'data/esa-same-point-tangent-20261111-v2')
    baseline = fit_inspect(root)
    first = ClosedStudy(root, 'data/esa-same-point-tangent-20261111')
    try:
        if (first.completion['state'] != 'terminal' or
                first.summary['charged']['native_calls'] != 0 or
                len(first.rows) != 3 or
                any(first.envelope(identity)['result'].get('error_type') != 'ImportError'
                    for identity in first.rows)):
            raise ValueError('preserved zero-call direct-loader failure required')
        first_completion = first.completion['summary_sha256']
    finally:
        first.close()
    report.update(source_sha256=digest(Path(__file__).read_bytes()),
                  saved_fit_diagnostic_source_sha256=baseline['source_sha256'],
                  saved_fit_diagnostic_report_sha256=digest((
                      root/'docs/esa-observed-hybrid/FAILURE_DIAGNOSTIC.json').read_bytes()),
                  first_terminal_summary_sha256=first_completion,
                  new_fits=0)
    render(report)
    return report


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/esa-observed-hybrid/same-point-result'
    atomic(target/'verified-report.json', encoded(report))
    atomic(target/'README.md', render(report).encode())
    return dict(published=str(target.relative_to(root)),
                completed=report['complete'], native_calls=report['charged']['native_calls'])


def verify(root):
    from .studies.artifacts import encoded
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/esa-observed-hybrid/same-point-result'
    if ((target/'verified-report.json').read_bytes() != encoded(report) or
            (target/'README.md').read_bytes() != render(report).encode()):
        raise ValueError('published same-point result differs from verified evidence')
    return dict(verified=True, completed=report['complete'],
                native_calls=report['charged']['native_calls'])


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('publish', 'verify'))
    parser.add_argument('--project', default='.')
    args = parser.parse_args()
    value = publish(args.project) if args.action == 'publish' else verify(args.project)
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    main()
