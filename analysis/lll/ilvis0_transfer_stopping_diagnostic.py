# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the saved stopping probes of the four-group transfer study.

This is a read-only numerical diagnosis. It cannot qualify a failed fit or
change the published transfer assessment.
"""
import argparse
import hashlib
from pathlib import Path

from lll.ilvis0_group_transfer_report import MANIFEST_SHA256, STUDY
from lll.ilvis0_solver_refinement import POLICY as STOPPING
from lll.studies.artifacts import atomic, encoded
from lll.studies.closed import ClosedStudy


POLICY_SOURCES = (
    'analysis/lll/ilvis0_solver_refinement.py',
    'analysis/lll/ilvis0_solver_position.py',
)


def frozen_policy_sources(root, manifest):
    """Require the original stopping-policy code, not a later revision."""
    sources = manifest['sources']
    bound = {}
    for name in POLICY_SOURCES:
        expected = sources.get(name)
        actual = hashlib.sha256((root/name).read_bytes()).hexdigest()
        if expected != actual:
            raise ValueError('original stopping-policy source changed: ' + name)
        bound[name] = actual
    return bound


def failed_gates(fit):
    """Name the original fixed conditions that a saved failed probe misses."""
    probe = fit['stability_probe']
    if probe['passed'] is not False:
        raise ValueError('failed stability probe required')
    if probe.get('reason') == 'not_stationary':
        return ['stationarity_before_probe']
    if probe.get('reason') != 'fresh_position_probe_not_stable':
        raise ValueError('unknown saved stopping reason')
    policy = fit['stability_policy']
    values = (probe['actual_cost_change'], probe['fresh_stationarity'],
              probe['position_rms_neu_m'], probe['position_max_abs_neu_m'])
    if (policy['position_rms_tolerance_m'] != .001 or
            policy['position_max_tolerance_m'] != .01 or
            fit['stationarity_tolerance'] != STOPPING['stationarity_tolerance'] or
            len(values[2]) != 3 or len(values[3]) != 3):
        raise ValueError('unexpected original stopping limits')
    gates = []
    if values[0] > STOPPING['relative_cost_tolerance']:
        gates.append('relative_cost_change')
    if values[1] > STOPPING['stationarity_tolerance']:
        gates.append('fresh_stationarity')
    if max(values[2]) > policy['position_rms_tolerance_m']:
        gates.append('position_rms')
    if max(values[3]) > policy['position_max_tolerance_m']:
        gates.append('position_maximum')
    if not gates:
        raise ValueError('saved failed probe has no failed original gate')
    return gates


def build(root='.'):
    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.summary['completed'] != 16 or len(study.tasks) != 16 or
                len(study.rows) != 16):
            raise ValueError('complete exact transfer study required')
        policy_sources = frozen_policy_sources(root, study.manifest)
        rows = []
        for identity in sorted(study.tasks):
            envelope = study.envelope(identity)
            result = envelope['result']
            fit = study.artifact(identity, 'fit.json')
            passed = study.rows[identity]['passed']
            if (result['passed'] is not passed or
                    fit['converged'] is not passed or
                    fit['stability_verified'] is not passed):
                raise ValueError('saved fit and sealed result disagree')
            rows.append(dict(identity=identity,
                             segment_id=study.tasks[identity]['payload']['segment_id'],
                             origin=study.tasks[identity]['payload']['origin'],
                             passed=passed,
                             failed_gates=[] if passed else failed_gates(fit),
                             saved_message=fit['message'],
                             evaluations=fit['evaluations']))
        if sum(row['passed'] for row in rows) != 6:
            raise ValueError('sealed transfer outcome changed')
        source = root/'analysis/lll/ilvis0_transfer_stopping_diagnostic.py'
        return dict(version='ilvis0-transfer-stopping-diagnostic-v1',
                    study=STUDY, verified=True, tasks=16,
                    passing=6, nonpassing=10,
                    relative_cost_tolerance=STOPPING['relative_cost_tolerance'],
                    stationarity_tolerance=STOPPING['stationarity_tolerance'],
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    policy_sources=policy_sources,
                    original_outcomes_unchanged=True,
                    scientific_decision='abstain', rows=rows)
    finally:
        study.close()


def render(report):
    if report['tasks'] != 16 or report['nonpassing'] != 10:
        raise ValueError('complete diagnostic required')
    alone = sum(row['failed_gates'] == ['relative_cost_change']
                for row in report['rows'])
    both = sum(row['failed_gates'] ==
               ['relative_cost_change', 'fresh_stationarity']
               for row in report['rows'])
    early = sum(row['failed_gates'] == ['stationarity_before_probe']
                for row in report['rows'])
    if (alone, both, early) != (7, 2, 1):
        raise ValueError('saved stopping categories changed')
    return '\n'.join([
        '# Why ten transfer fits abstained', '',
        'The [four-group transfer study](RESULT.md) sealed all 16 starts. Six',
        'passed its original numerical stopping check; ten did not. Reading',
        'their saved probes gives:', '',
        '| Failed fixed check | Fits |', '|---|---:|',
        '| Cost change only | 7 |',
        '| Cost change and stationarity | 2 |',
        '| Stationarity before the full probe | 1 |', '',
        'The seven cost-only fits already met the fixed position and',
        'stationarity checks. Their fresh cost changes still exceeded the',
        f"original relative limit of {report['relative_cost_tolerance']:g}.",
        'The failed fits remain failed. Close costs from different starts',
        'cannot replace a passed stopping check, and this diagnostic makes',
        'no model or uncertainty decision.', '',
        '[All starts and costs](fit-audit.csv) · [Transfer result](RESULT.md)',
        ''])


def publish(root='.'):
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/prediction-group-transfer'
    atomic(target/'STOPPING_DIAGNOSTIC.md', render(report).encode())
    atomic(target/'stopping-diagnostic.json', encoded(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = publish(args.root)
    print(f"{report['passing']}/16 passed; 7 cost-only, 2 cost-and-stationarity, 1 early-stationarity failures")


if __name__ == '__main__':
    main()
