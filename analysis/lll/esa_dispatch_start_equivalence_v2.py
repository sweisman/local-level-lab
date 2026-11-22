# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retrospective start-stability audit of sealed ESA method pairs.

This reads no aircraft originals and cannot change the frozen observed gate.
"""

import hashlib
import json
from pathlib import Path

from .ilvis0_start_equivalence_v2 import compare_start_sets_v2


STUDY = 'data/esa-observed-model-dispatch-globe-pairs-v2'
RELATIVE_COST_TOLERANCE = 1e-8
FORECAST_TOLERANCE_M = 0.01


def audit(root):
    from .airquantumgrav_scoring import receiver_errors
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    public = root / 'docs/esa-observed-model-dispatch-v2'
    receipt = json.loads((public / 'evidence-receipt.json').read_bytes())
    if (receipt.get('version') != 'esa-dispatch-publication-v2'
            or receipt.get('qualified') is not False
            or receipt.get('cases') != 24
            or receipt.get('scientific_decision') != 'abstain'
            or set(receipt.get('artifacts', {})) != {
                'README.md', 'auditor-source.py', 'pair-results.csv',
                'verified-report.json'}):
        raise ValueError('unchanged historical publication receipt required')
    for name, sha in receipt['artifacts'].items():
        if digest((public / name).read_bytes()) != sha:
            raise ValueError('historical publication artifact changed')
    original = json.loads((public / 'verified-report.json').read_bytes())
    if (original.get('verified') is not True
            or original.get('qualified') is not False
            or original.get('globe_pairs_passed') != 16
            or original.get('primary_groups_agree') != 5
            or original.get('manifest_sha256') != receipt['manifest_sha256']
            or original.get('summary_sha256') != receipt['summary_sha256']):
        raise ValueError('expected complete, failed, sealed observed gate')
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['manifest_sha256'] != receipt['manifest_sha256']
                or study.completion['summary_sha256'] != receipt['summary_sha256']
                or study.completion['state'] != 'complete'
                or len(study.rows) != 16):
            raise ValueError('sealed study differs from historical publication')
        groups = []
        for model in ('sphere_rotating', 'sphere_still'):
            for profile in (False, True):
                for policy in ('reported-short-v1', 'reported-persistent-v1'):
                    cases = []
                    for start in (0, 1):
                        identity = f'{model}-{int(profile)}-{policy}-{start}'
                        if identity not in study.rows:
                            raise ValueError('missing sealed start')
                        result = study.envelope(identity)['result']
                        if (result.get('passed') is not True
                                or result.get('comparison', {}).get('passed') is not True
                                or study.artifact(identity, 'comparison.json')
                                != result['comparison']):
                            raise ValueError('passing sealed pair required')
                        cases.append(dict(identity=identity, start=start,
                            wide_passed=result['wide']['passed'],
                            selected_passed=result['hybrid']['passed'],
                            wide_training_cost=result['wide']['training_cost'],
                            selected_training_cost=result['hybrid']['training_cost']))
                    if len(cases) != 2 or {row['start'] for row in cases} != {0, 1}:
                        raise ValueError('complete matched starts required')
                    cases.sort(key=lambda row: row['start'])
                    baseline = study.artifact(cases[0]['identity'],
                                              'wide-forecast.json')['coordinates']
                    methods = {}
                    for method, cost_key in (('wide', 'wide_training_cost'),
                                             ('hybrid', 'selected_training_cost')):
                        rows = []
                        for case in cases:
                            identity = case['identity']
                            forecast = study.artifact(identity, method+'-forecast.json')
                            binding = study.artifact(identity,
                                                     method+'-input-binding.json')
                            rows.append(dict(
                                start=case['start'],
                                training_cost=case[cost_key],
                                passed=case[method+'_passed' if method == 'wide'
                                            else 'selected_passed'],
                                binding=digest(encoded(dict(
                                    input=binding, times_s=forecast['times_s']))),
                                forecast=receiver_errors(
                                    forecast['coordinates'], baseline).tolist()))
                        methods[method] = rows
                    rule = compare_start_sets_v2(
                        methods['wide'], methods['hybrid'],
                        relative_cost_tolerance=RELATIVE_COST_TOLERANCE,
                        absolute_cost_tolerance=0,
                        forecast_tolerance_m=FORECAST_TOLERANCE_M)
                    groups.append(dict(model=model, profile=profile,
                                       policy_id=policy, rule=rule))
        return dict(version='esa-saved-start-equivalence-v2-diagnostic',
                    verified=True, frozen_qualified=False,
                    retrospective_only=True, new_fits=0, original_reads=0,
                    protected_reads=0, study=STUDY,
                    manifest_sha256=original['manifest_sha256'],
                    summary_sha256=original['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    groups=groups,
                    retrospective_passing_groups=sum(
                        row['rule']['equivalent'] for row in groups),
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh diagnostic output required')
    result = audit(args.project)
    atomic(output, encoded(result))
    print(json.dumps(dict(verified=True,
        passing=result['retrospective_passing_groups'],
        total=len(result['groups']), retrospective_only=True), sort_keys=True))


if __name__ == '__main__':
    main()
