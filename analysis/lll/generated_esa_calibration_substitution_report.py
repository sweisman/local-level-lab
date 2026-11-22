# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report closed known-calibration native ablations without refitting."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_calibration_substitution_study import (
    ID, PLAN, SCOPE, original_cases, recipe, tasks)
from .generated_esa_bounded_pilot_v2_report import build as verified_pilot


LABELS = ('baseline', 'sensor', 'gravity_clock', 'all14')


def deltas(labels, scores):
    if (tuple(labels) != LABELS or not isinstance(scores, list)
            or len(scores) != 4):
        raise ValueError('exact four ordered native variants required')
    fields = ('training_horizontal_rms_m', 'later_horizontal_rms_m',
              'training_vertical_rms_m', 'later_vertical_rms_m')
    rows = {}
    for label, score in zip(labels, scores, strict=True):
        if (not isinstance(score, dict)
                or any(type(score.get(name)) not in (int, float)
                       or not math.isfinite(score[name]) or score[name] < 0
                       for name in fields if name in score)
                or not {'training_horizontal_rms_m',
                        'later_horizontal_rms_m'} <= set(score)):
            raise ValueError('finite matched native physical scores required')
        rows[label] = {name: float(score[name]) for name in fields
                       if name in score}
    baseline = rows['baseline']
    for label in LABELS[1:]:
        for section in ('training', 'later'):
            key = section + '_horizontal_rms_m'
            rows[label][section + '_horizontal_change_m'] = (
                rows[label][key] - baseline[key])
    return rows


def build(root):
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    original = verified_pilot(root)
    cases = original_cases(root)
    if (original['tasks_total'] != 2
            or original['technical_passing'] != 2
            or original['original_physical_passing'] != 0):
        raise ValueError('sealed two-case generated source required')
    study = ClosedStudy(root, 'data/' + ID)
    try:
        expected = {task['identity']: task for task in tasks()}
        actual = {name: {key: value for key, value in task.items()
                         if key not in ('index', 'shard')}
                  for name, task in study.tasks.items()}
        if (study.completion['state'] not in ('complete', 'terminal')
                or study.manifest.get('scope') != SCOPE
                or study.input('recipe') != recipe()
                or actual != expected or not set(study.rows) <= set(expected)):
            raise ValueError('closed exact substitution study required')
        rows = {}
        for law in ('increment', 'point'):
            status = study.rows.get(law)
            if (status is None or status['status'] != 'complete'
                    or status['passed'] is not True):
                rows[law] = dict(technical_passed=False,
                                 status='not_completed' if status is None else
                                        status['status'])
                continue
            outcome = study.envelope(law)['result']
            if (outcome.get('technical_only') is not True
                    or outcome.get('native_forecasts') != 4
                    or outcome.get('original_reads') != 0
                    or outcome.get('protected_reads') != 0
                    or outcome.get('scientific_decision') != 'abstain'):
                raise ValueError('technical native outcome changed')
            reference = cases[law]['reference']
            truth = cases[law]['truth']
            if (study.input('case-'+law) != reference
                    or study.input('truth-'+law) != truth):
                raise ValueError('source-fit input binding changed')
            raw_scores = study.artifact(law, 'physical-scores.json', raw=True)
            scores = json.loads(raw_scores)
            substitution = study.artifact(law, 'substitution.json')
            forward = study.artifact(law, 'forward-results.json')
            reconstructed = study.artifact(law, 'reconstructed-binding.json')
            if (scores.get('labels') != list(LABELS)
                    or scores.get('source_sha256') != truth['source_sha256']
                    or scores.get('diagnostic_only') is not True
                    or scores.get('scientific_decision') != 'abstain'
                    or substitution.get('labels') != list(LABELS)
                    or substitution.get('no_refit') is not True
                    or len(substitution.get('normalized_points', [])) != 4
                    or forward.get('original_forecast_matched') is not True
                    or reconstructed.get('original_manifest_sha256') !=
                       reference['original_manifest_sha256']):
                raise ValueError('saved native replay or labels changed')
            measurements = deltas(scores['labels'], scores['scores'])
            if (not math.isclose(
                    measurements['baseline']['later_horizontal_rms_m'],
                    original['laws'][law]['future_horizontal_rms_m'],
                    rel_tol=1e-6, abs_tol=1e-5)
                    or not math.isclose(
                        measurements['baseline']['training_horizontal_rms_m'],
                        original['laws'][law]['training_horizontal_rms_m'],
                        rel_tol=1e-6, abs_tol=1e-5)):
                raise ValueError('saved native baseline physical score differs')
            rows[law] = dict(technical_passed=True, scores=measurements,
                             physical_scores_artifact_sha256=hashlib.sha256(
                                 raw_scores).hexdigest(),
                             original_fit_sha256=reference['fit_sha256'])
        return dict(version='generated-esa-calibration-substitution-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=2,
                    technical_passing=sum(row['technical_passed'] is True
                                          for row in rows.values()),
                    laws=rows, new_fits=0, original_reads=0,
                    protected_reads=0, aircraft_calibration_identified=False,
                    scientific_decision='abstain')
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
        raise ValueError('fresh native-substitution report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({law: row.get('scores', {})
                      for law, row in result['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
