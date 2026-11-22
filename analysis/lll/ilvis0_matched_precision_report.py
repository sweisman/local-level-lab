# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only report for the fixed-point matched-field precision check."""

from contextlib import closing
from pathlib import Path

from . import ilvis0_matched_precision as study
from .ilvis0_solver_refinement import POLICY
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


def build(root):
    with closing(ClosedStudy(root, 'data/' + study.ID)) as precision, closing(
            ClosedStudy(root, 'data/' + study.parent.ID)) as baseline:
        bound = precision.input('parent_receipt')
        if (len(precision.tasks) != 33 or set(precision.tasks) != set(precision.rows)
                or precision.completion['state'] != 'complete'
                or precision.summary['charged']['native_calls'] != 132
                or bound['manifest_sha256'] != baseline.completion['manifest_sha256']
                or bound['summary_sha256'] != baseline.completion['summary_sha256']):
            raise ValueError('exact complete probe study and sealed parent required')
        rows = []
        limit = POLICY['relative_cost_tolerance']
        source = 'analysis/lll/ilvis0_solver_refinement.py'
        if digest((Path(root) / source).read_bytes()) != precision.manifest['sources'][source]:
            raise ValueError('exact frozen cost threshold source required')
        for identity in sorted(precision.tasks):
            envelope = precision.envelope(identity)
            result = envelope['result']
            original = baseline.artifact(identity, 'fit.json')
            binding = precision.input(identity)
            task = study.task(identity)
            if (binding['fit'] != original or binding['spec'] != task['payload']
                    or any(result[key] != value for key, value in task['payload'].items())
                    or envelope['charged']['native_calls'] != 4
                    or envelope['charged']['packet_visits'] != task['limits']['packet_visits']
                    or result['passed'] is not True or result['fit_starts'] != 0
                    or result['later_receiver_positions_used'] is not False
                    or original['converged'] is not False):
                raise ValueError('changed precision result binding: ' + identity)
            original_costs = [original['residual_sum_squares'],
                              original['evaluation_trace'][-1]['cost']]
            for label in ('binary64', 'wide'):
                value = result[label]
                before, after = value['endpoint_cost'], value['probe_cost']
                if (value['cost_delta'] != after - before or
                        value['relative_cost_change'] != abs(after - before) / max(before, after, 1.)):
                    raise ValueError('inconsistent saved cost calculation')
                if label == 'binary64' and any(abs(x-y) > 1e-12+1e-9*abs(x)
                                               for x, y in zip(original_costs, (before, after))):
                    raise ValueError('binary64 result does not reproduce its original costs')
            rows.append(dict(identity=identity, **result))
        return dict(version='ilvis0-matched-precision-report-v1', study='data/' + study.ID,
                    manifest_sha256=precision.completion['manifest_sha256'],
                    parent_manifest_sha256=baseline.completion['manifest_sha256'],
                    charged=precision.summary['charged'], fit_starts=0, threshold=limit,
                    wide_below_limit=sum(row['wide']['relative_cost_change'] <= limit for row in rows),
                    wide_cost_increases=sum(row['wide']['cost_delta'] > 0. for row in rows),
                    rows=rows, scientific_decision='abstain')


def publish(root):
    report = build(root)
    folder = Path(root) / study.parent.DOCS
    exceptions = [row for row in report['rows']
                  if row['wide']['relative_cost_change'] > report['threshold']]
    lines = ['# Precision check on the 33 unfinished fits', '',
             'All 33 fixed-point pairs reproduced their saved binary64 costs.',
             f"With wider arithmetic, **{report['wide_below_limit']}/33** "
             'had a cost change within the original limit. '
             f"The cost still rose in {report['wide_cost_increases']}/33 pairs.", '',
             '| Generated case | Fitted model | Gyro cap | Removal profiled | Wide cost change |',
             '|---|---|---:|---|---:|']
    for row in exceptions:
        lines.append(f"| {row['truth_model']} | {row['model']} | ±{row['cap_dph']:g}°/h | "
                     f"{'yes' if row['profile'] else 'no'} | {row['wide']['cost_delta']:+.3g} |")
    lines.extend(['', 'All endpoints and probe steps were held fixed. These are cost '
                  'checks, with no new optimization and no later receiver observations. '
                  'All original stopping labels remain unchanged. Wider arithmetic '
                  'addresses most of the cost failures at the saved points. '
                  'The two exceptions and the wider solver still require separate checks.', '',
                  '[Frozen plan](MATCHED_PRECISION_PLAN.md) · '
                  '[Per-fit results](matched-precision-report.json)', ''])
    atomic(folder / 'matched-precision-report.json', encoded(report))
    atomic(folder / 'MATCHED_PRECISION_RESULT.md', '\n'.join(lines).encode())
    return report


if __name__ == '__main__':
    result = publish(Path.cwd())
    print(f"{result['wide_below_limit']}/33 cost changes within the original limit")
