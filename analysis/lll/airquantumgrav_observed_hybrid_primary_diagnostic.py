# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only cross-start check after the ESA tangent substitution failed."""
import json
from pathlib import Path


def summarize(rows, primary_checks, forecast):
    """Compare forecasts selected independently by two fitted methods."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    if not isinstance(rows, list) or not isinstance(primary_checks, list):
        raise ValueError('complete saved rows and primary checks required')
    groups = []
    for check in primary_checks:
        if check.get('same') is not False:
            continue
        key = (check['model'], check['profile'], check['policy_id'])
        candidates = [row for row in rows if
                      (row['model'], row['profile'], row['policy_id']) == key]
        if (len(candidates) != 2 or {row['start'] for row in candidates} != {0, 1}
                or any(row.get('returned') is not True
                       or row['wide'].get('passed') is not True
                       or row['hybrid'].get('passed') is not True
                       for row in candidates)):
            raise ValueError('two complete passing starts required for primary comparison')
        chosen = {}
        gaps = {}
        for variant in ('wide', 'hybrid'):
            ordered = sorted(candidates, key=lambda row:
                             (row[variant]['training_cost'], row['start']))
            chosen[variant] = ordered[0]['identity']
            gaps[variant] = float(ordered[1][variant]['training_cost']
                                  - ordered[0][variant]['training_cost'])
            if chosen[variant] != check[variant] or not np.isfinite(gaps[variant]) or gaps[variant] < 0:
                raise ValueError('saved primary selection or cost gap differs')
        wide = forecast(chosen['wide'], 'wide')
        hybrid = forecast(chosen['hybrid'], 'hybrid')
        if wide.get('times_s') != hybrid.get('times_s'):
            raise ValueError('cross-start forecast times differ')
        difference = receiver_errors(hybrid['coordinates'], wide['coordinates'])
        maximum = float(np.max(np.linalg.norm(difference, axis=1)))
        groups.append(dict(model=key[0], profile=key[1], policy_id=key[2],
                           wide_selected=chosen['wide'], hybrid_selected=chosen['hybrid'],
                           wide_training_cost_gap=gaps['wide'],
                           hybrid_training_cost_gap=gaps['hybrid'],
                           maximum_cross_start_difference_m=maximum))
    return dict(version='esa-hybrid-primary-diagnostic-v1',
                disagreeing_groups=len(groups), groups=groups,
                new_fits=0, original_reads=0, protected_reads=0,
                method_substitution_requalified=False,
                scientific_decision='abstain')


def inspect(root):
    """Read only the verified publication and sealed study artifacts."""
    from .airquantumgrav_observed_hybrid_combined_audit import (
        CombinedStudy, verify_publication)
    from .studies.combined_task_evidence import inspect as inspect_lineage
    from .studies.artifacts import digest

    root = Path(root).resolve()
    receipt = verify_publication(root)
    report_path = root/'docs/esa-observed-hybrid/combined/verified-report.json'
    raw = report_path.read_bytes()
    report = json.loads(raw)
    if (report.get('verified') is not True or report.get('total') != 24
            or report.get('returned') != 24 or report.get('qualified') is not False
            or len(report.get('primary_checks', ())) != 10):
        raise ValueError('closed unqualified 24-case ESA report required')
    ledger = inspect_lineage(root, root/'data/esa-observed-hybrid-continuation-20261111')
    view = CombinedStudy(root, ledger)
    try:
        result = summarize(report['rows'], report['primary_checks'],
                           lambda identity, variant:
                           view.artifact(identity, variant+'-forecast.json'))
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
    atomic(target/'PRIMARY_DIAGNOSTIC.json', encoded(result))
    lines = ['# ESA primary-start sensitivity', '',
             'The verified 24-case substitution study did not qualify. In three',
             'complete groups, the wide and faster methods chose different starts',
             'by training cost. This post-run check compares their saved forecasts;',
             'it does not refit or change the failed gate.', '',
             '| Model | Processing | Error policy | Wide cost gap | Faster cost gap | Maximum forecast difference |',
             '|---|---|---|---:|---:|---:|']
    for row in result['groups']:
        lines.append(f"| {row['model']} | {int(row['profile'])} | {row['policy_id']} | "
                     f"{row['wide_training_cost_gap']:.6g} | "
                     f"{row['hybrid_training_cost_gap']:.6g} | "
                     f"{row['maximum_cross_start_difference_m']:.6g} m |")
    lines += ['', 'These are numerical sensitivity measurements, not a new',
              'Earth-model comparison or a basis for changing the 0.01 m gate.', '',
              '[Verified paired report](combined/README.md) · '
              '[Machine-readable diagnostic](PRIMARY_DIAGNOSTIC.json).', '']
    atomic(target/'PRIMARY_DIAGNOSTIC.md', '\n'.join(lines).encode())
    print(json.dumps(dict(groups=result['disagreeing_groups'],
                          maximum_cross_start_difference_m=max(
                              (row['maximum_cross_start_difference_m'] for row in result['groups']),
                              default=0.))))


if __name__ == '__main__':
    main()
