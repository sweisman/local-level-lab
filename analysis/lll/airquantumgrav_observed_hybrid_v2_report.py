# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish the sealed three-pair revised-tangent development comparison."""
import argparse
import csv
import hashlib
import io
from pathlib import Path

from lll.studies.artifacts import atomic, encoded
from lll.studies.closed import ClosedStudy
from lll.airquantumgrav_observed_hybrid_report import compare_pair
from lll.airquantumgrav_observed_hybrid_v2 import (
    IDENTITY, SCOPE, FAILED, SAVED_POINT_PARENT,
    SAVED_POINT_MANIFEST, SAVED_POINT_SUMMARY)


def pair_row(identity, result, saved):
    """Replay the fixed physical comparison where both fits qualify."""
    if result is None:
        return dict(identity=identity, returned=False, passed=False,
                    wide_passed=None, revised_passed=None,
                    maximum_position_difference_m=None,
                    reason='task not returned within finite allowance')
    if (result.get('original_reads') not in (None, 0) or
            result.get('protected_reads') not in (None, 0) or
            result.get('scientific_decision') not in (None, 'abstain')):
        raise ValueError('development-only saved result required')
    wide = result.get('wide')
    revised = result.get('hybrid')
    comparison = result.get('comparison')
    if not isinstance(wide, dict) or not isinstance(revised, dict) or not isinstance(comparison, dict):
        return dict(identity=identity, returned=True, passed=False,
                    wide_passed=None, revised_passed=None,
                    maximum_position_difference_m=None,
                    reason=result.get('error', 'incomplete paired result'))
    if (result.get('original_reads') != 0 or
            result.get('protected_reads') != 0 or
            result.get('scientific_decision') != 'abstain'):
        raise ValueError('complete paired result lacks protected-read evidence')
    both = wide.get('passed') is True and revised.get('passed') is True
    if both:
        replay = compare_pair(
            wide, revised, saved('wide-fit.json'), saved('hybrid-fit.json'),
            saved('wide-forecast.json'), saved('hybrid-forecast.json'),
            tolerance_m=.01)
        if replay != comparison:
            raise ValueError('saved paired comparison differs from replay')
    elif comparison.get('passed') is not False:
        raise ValueError('nonqualifying fit cannot pass paired gate')
    if result.get('passed') is not comparison.get('passed'):
        raise ValueError('task pass flag differs from paired comparison')
    return dict(identity=identity, returned=True,
                passed=bool(comparison['passed']),
                wide_passed=bool(wide.get('passed')),
                revised_passed=bool(revised.get('passed')),
                maximum_position_difference_m=comparison.get('maximum_position_difference_m'),
                reason=(comparison.get('reason') or
                        ('paired method gate failed' if not comparison['passed'] else '')))


def build(root='.'):
    root = Path(root).resolve()
    reporter_sha = hashlib.sha256(
        (root/'analysis/lll/airquantumgrav_observed_hybrid_v2_report.py').read_bytes()).hexdigest()
    study = ClosedStudy(root, 'data/'+IDENTITY)
    try:
        if (study.manifest['scope'] != SCOPE or
                set(study.tasks) != FAILED or
                study.manifest['allocation']['total'] != 3 or
                'analysis/lll/ilvis0_hybrid_tangent_v2.py' not in study.manifest['sources'] or
                study.manifest['sources'].get(
                    'analysis/lll/airquantumgrav_observed_hybrid_v2_report.py') != reporter_sha or
                not {'v2-recovery-request', 'v2-recovery-report'} <=
                set(study.manifest['inputs']) or
                study.input('v2-saved-point-proof') != dict(
                    parent=SAVED_POINT_PARENT,
                    manifest_sha256=SAVED_POINT_MANIFEST,
                    summary_sha256=SAVED_POINT_SUMMARY,
                    passing_pairs=3) or
                study.summary['charged']['native_calls'] > 1206):
            raise ValueError('exact closed finite revised-tangent study required')
        rows = []
        for identity in sorted(FAILED):
            if identity not in study.rows:
                rows.append(pair_row(identity, None, None))
                continue
            envelope = study.envelope(identity)
            for path, sha in envelope['artifacts'].items():
                study.read(path, sha, raw=True)
            rows.append(pair_row(identity, envelope['result'],
                                 lambda name: study.artifact(identity, name)))
        return dict(verified=True, study='data/'+IDENTITY,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    reporter_sha256=reporter_sha,
                    tasks=3, returned=sum(row['returned'] for row in rows),
                    passing_pairs=sum(row['passed'] for row in rows),
                    native_calls=study.summary['charged']['native_calls'],
                    original_reads=0, protected_reads=0,
                    substitution_qualified=False, scientific_decision='abstain',
                    rows=rows)
    finally:
        study.close()


def render(report):
    lines = ['# Revised fast tangent: three development pairs', '',
             f"**{report['passing_pairs']}/3 paired comparisons pass.**",
             f"{report['returned']}/3 tasks returned under the finite allowance.",
             'This checks a calculation method on one development recording.',
             'It does not replace the wide method or make an Earth-model decision.',
             '', '| Case | Wide fit | Revised fit | Difference | Paired gate |',
             '|---|---|---|---:|---|']
    for row in report['rows']:
        difference = row['maximum_position_difference_m']
        lines.append('| {identity} | {wide_passed} | {revised_passed} | {difference} | {passed} |'.format(
            identity=row['identity'], wide_passed=row['wide_passed'],
            revised_passed=row['revised_passed'],
            difference='—' if difference is None else f'{difference:.5g} m',
            passed='pass' if row['passed'] else 'unresolved'))
    lines += ['', 'A pair with an unqualified wide or revised fit remains',
              'unresolved. The [full outcome table](pair-results.csv) retains',
              'the reason. All input and result artifacts are hash-checked.',
              '', '[Frozen plan](../../mixed-tangent-hybrid/V2_PAIRED_PLAN.md) ·',
              '[Earlier paired result](../combined/README.md)']
    return '\n'.join(lines)+'\n'


def csv_bytes(report):
    fields = ['identity', 'returned', 'passed', 'wide_passed', 'revised_passed',
              'maximum_position_difference_m', 'reason']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(report['rows'])
    return stream.getvalue().encode()


def publish(root='.'):
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/esa-observed-hybrid/three-pair-v2'
    atomic(target/'README.md', render(report).encode())
    atomic(target/'pair-results.csv', csv_bytes(report))
    atomic(target/'verified-report.json', encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = publish(args.root)
    print(f"{report['passing_pairs']}/3 pairs pass; {report['returned']}/3 returned")


if __name__ == '__main__':
    main()
