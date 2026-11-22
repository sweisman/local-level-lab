# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and summarize closed generated weak-direction native forecasts."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_weak_perturbation_study import ID, PLAN, SCOPE, recipe


def build(root):
    from .generated_esa_bounded_pilot_v2_report import build as original_pilot
    from .generated_esa_weak_direction_report import build as weak_audit
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    original = original_pilot(root)
    audit = weak_audit(root)
    study = ClosedStudy(root, 'data/' + ID)
    try:
        if (study.completion['state'] != 'complete'
                or study.manifest.get('scope') != SCOPE
                or study.input('recipe') != recipe()
                or set(study.tasks) != {'increment', 'point'}
                or original['original_physical_passing'] != 0
                or audit['tasks_total'] != 2):
            raise ValueError('closed exact nonlinear generated study required')
        rows = {}
        for law in ('increment', 'point'):
            envelope = study.envelope(law)
            outcome = envelope['result']
            if (study.rows[law]['status'] != 'complete'
                    or outcome.get('passed') is not True
                    or outcome.get('technical_only') is not True
                    or outcome.get('scientific_decision') != 'abstain'
                    or outcome.get('native_forecasts') != 4
                    or outcome.get('training_epochs') != 600
                    or outcome.get('prediction_epochs') != 300
                    or outcome.get('original_reads') != 0
                    or outcome.get('protected_reads') != 0
                    or envelope['charged'] != dict(
                        native_calls=4, packet_visits=972000000,
                        bound_calls=0, bound_steps=0)):
                raise ValueError('nonlinear task or charges changed')
            case = study.input('case-' + law)
            truth = study.input('truth-' + law)
            forward_raw = study.artifact(law, 'forward-results.json', raw=True)
            score_raw = study.artifact(law, 'physical-scores.json', raw=True)
            forward = json.loads(forward_raw)
            score = json.loads(score_raw)
            comparison = forward.get('comparisons', [])
            physical = score.get('scores', [])
            if (forward.get('original_forecast_matched') is not True
                    or forward.get('sign') not in (-1, 1)
                    or forward.get('steps') != [0., .05, .1, .2]
                    or score.get('steps') != forward['steps']
                    or score.get('source_sha256') != truth['source_sha256']
                    or score.get('diagnostic_only') is not True
                    or len(comparison) != 3 or len(physical) != 4
                    or [item.get('step') for item in comparison] !=
                       [.05, .1, .2]
                    or case.get('fit_sha256') !=
                       audit['laws'][law]['fit_artifact_sha256']
                    or len(forward.get('baseline_coordinates', [])) != 900):
                raise ValueError('saved perturbations or source binding changed')
            baseline = physical[0]
            previous = original['laws'][law]
            if (not math.isclose(baseline['training_horizontal_rms_m'],
                                 previous['training_horizontal_rms_m'],
                                 rel_tol=1e-8, abs_tol=1e-6)
                    or not math.isclose(baseline['later_horizontal_rms_m'],
                                        previous['future_horizontal_rms_m'],
                                        rel_tol=1e-8, abs_tol=1e-6)):
                raise ValueError('saved baseline physical score differs')
            last = comparison[-1]
            rows[law] = dict(
                baseline_forecast_matched=True,
                perturbation_sign=forward['sign'],
                baseline_training_truth_miss_horizontal_rms_m=(
                    baseline['training_horizontal_rms_m']),
                baseline_later_truth_miss_horizontal_rms_m=(
                    baseline['later_horizontal_rms_m']),
                largest_step_later_change_horizontal_rms_m=(
                    last['later_change_horizontal_rms_m']),
                largest_step_later_remainder_horizontal_rms_m=(
                    last['later_remainder_horizontal_rms_m']),
                comparisons=comparison,
                physical_scores=physical,
                forward_artifact_sha256=hashlib.sha256(forward_raw).hexdigest(),
                score_artifact_sha256=hashlib.sha256(score_raw).hexdigest())
        return dict(version='generated-esa-weak-nonlinear-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=2, technical_passing=2,
                    native_forecasts=8, new_fits=0,
                    original_reads=0, protected_reads=0,
                    original_physical_passing=0,
                    laws=rows, scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh saved nonlinear report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps(dict(tasks_total=result['tasks_total'],
                          technical_passing=result['technical_passing'],
                          original_physical_passing=result[
                              'original_physical_passing']), sort_keys=True))


if __name__ == '__main__':
    main()
