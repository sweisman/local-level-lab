# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and summarize sealed dual-target generated forecasts without refitting."""

import hashlib
import json
from pathlib import Path

from .generated_esa_dual_target_pilot import (
    ID, PREFLIGHT_ID, SCOPE, PREFLIGHT_SCOPE, PLAN,
    recipe, preflight_recipe)


def build(root, *, preflight=False):
    from .generated_receiver_target_check import score
    from .generated_esa_bounded_pilot_v2_report import interval_coverage
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    name = PREFLIGHT_ID if preflight else ID
    identities = ('preflight-increment',) if preflight else ('increment','point')
    study = ClosedStudy(root, 'data/' + name)
    try:
        if (study.completion['state'] != 'complete'
                or study.manifest.get('scope') !=
                   (PREFLIGHT_SCOPE if preflight else SCOPE)
                or study.input('recipe') !=
                   (preflight_recipe() if preflight else recipe())
                or set(study.tasks) != set(identities)):
            raise ValueError('closed exact dual-target study required')
        cases = {}
        for identity in identities:
            row = study.rows.get(identity)
            if row is None or row['status'] != 'complete':
                cases[identity] = dict(technical_passed=False,
                                       status=None if row is None else row['status'])
                continue
            outcome = study.envelope(identity)['result']
            if (outcome.get('dual_target_technical_passed') is not True
                    or outcome.get('technical_pilot_only') is not True
                    or outcome.get('passed') is not True
                    or outcome.get('original_reads') != 0
                    or outcome.get('protected_reads') != 0
                    or outcome.get('scientific_decision') != 'abstain'):
                raise ValueError('dual-target technical result or scope changed')
            artifact = lambda name: study.artifact(identity,name)
            bound_physical = artifact('bounded-physical.json')
            bound_receiver = artifact('bounded-receiver.json')
            scoring = artifact('scoring-observations.json')
            scores = artifact('scores.json')
            fit = artifact('fit.json')
            receiver = score(scores['times_s'],scoring['coordinates'],
                             artifact('training-receiver.json'),
                             artifact('input-binding.json'),
                             artifact('receiver-forecast-error-diagnostic.json'),
                             bound_receiver)
            m = 6 if preflight else 600
            if (bound_physical.get('prediction_target') != 'physical_position'
                    or bound_receiver.get('prediction_target') != 'receiver_measurement'
                    or bound_physical.get('training_epochs') != m
                    or bound_receiver.get('training_epochs') != m
                    or bound_physical.get('retained_calibration_columns') != 26
                    or bound_receiver.get('retained_calibration_columns') != 26
                    or scores.get('later_receiver_noise_added') is not False):
                raise ValueError('saved paired targets or physical score changed')
            cases[identity] = dict(
                technical_passed=True,
                numerical_converged=fit['converged'],
                original_physical_passed=outcome['original_prediction_passed'],
                physical_point_future_horizontal_rms_m=
                    scores['prediction']['horizontal_rms_m'],
                descriptive_physical_interval=interval_coverage(
                    bound_physical,scoring['coordinates'][m:]),
                generated_receiver_target=receiver,
                bound_physical_sha256=hashlib.sha256(study.artifact(
                    identity,'bounded-physical.json',raw=True)).hexdigest(),
                bound_receiver_sha256=hashlib.sha256(study.artifact(
                    identity,'bounded-receiver.json',raw=True)).hexdigest())
        return dict(version='generated-esa-dual-target-report-v1',
                    study='data/' + name,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    report_source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()).hexdigest(),
                    scoring_source_sha256=hashlib.sha256(
                        (root/'analysis/lll/generated_receiver_target_check.py').read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    tasks_total=len(identities),
                    technical_passing=sum(c.get('technical_passed') is True
                                          for c in cases.values()),
                    numerical_converged=sum(c.get('numerical_converged') is True
                                            for c in cases.values()),
                    original_physical_passing=sum(c.get('original_physical_passed') is True
                                                  for c in cases.values()),
                    cases=cases, new_fits=0, original_reads=0,
                    protected_reads=0,
                    empirical_coverage_calibrated=False,
                    aircraft_error_law_qualified=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    parser.add_argument('--preflight',action='store_true')
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh verified report required')
    result = build(args.root,preflight=args.preflight)
    atomic(output,encoded(result))
    print(json.dumps({key:result[key] for key in
                      ('tasks_total','technical_passing','numerical_converged',
                       'original_physical_passing')}))


if __name__ == '__main__':
    main()
