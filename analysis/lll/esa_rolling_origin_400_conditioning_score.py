# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score closed 400/120 forecasts after early-only conditioning is sealed."""

import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_rolling_origin_400_conditioning import ID as CONDITION_ID
from .esa_rolling_origin_400_score import PARENT, score_raw
from .esa_rolling_origin_400_study import ID as FIT_ID, LAWS


def score_pair(raw, conditional, receiver, covariance):
    from .esa_conditional_coverage_report import describe_coverage

    return dict(raw=score_raw(raw, receiver),
                conditional=score_raw(conditional, receiver),
                coverage=describe_coverage(conditional, receiver, covariance),
                confidence_calibrated=False,
                physical_adequacy_gate_frozen=False,
                scientific_decision='abstain')


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    conditioned = ClosedStudy(root, 'data/' + CONDITION_ID)
    parent = ClosedStudy(root, PARENT)
    try:
        if (fit.completion['state'] not in ('complete', 'terminal') or
                fit.summary['completed'] != 2 or
                conditioned.completion['state'] not in ('complete', 'terminal') or
                conditioned.summary['completed'] != conditioned.summary['total'] or
                conditioned.input('fit_identity') != dict(
                    prefix='data/' + FIT_ID,
                    manifest_sha256=fit.completion['manifest_sha256'],
                    summary_sha256=fit.completion['summary_sha256'])):
            raise ValueError('both fit outcomes and all conditioning outcomes must be sealed')
        origin = fit.input('parent_identity')
        if (origin['source_id'] != 'esa-99f1530c3eda4318' or
                origin['manifest_sha256'] != parent.completion['manifest_sha256'] or
                origin['summary_sha256'] != parent.completion['summary_sha256']):
            raise ValueError('sealed development parent differs')
        rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        if len(rows) != 800:
            raise ValueError('complete source receiver history required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']), row['height_m']]
            for row in rows[400:520]], dtype=float)
        result = {}
        for law in LAWS:
            fit_outcome = fit.envelope(law)['result']
            if (fit_outcome.get('law') != law or
                    fit_outcome.get('later_receiver_positions_used') is not False):
                raise ValueError('unchanged earlier-only fit outcome required')
            if fit_outcome.get('passed') is not True:
                result[law] = dict(fit_passed=False,
                                   conditioned_passed=False,
                                   score=None,
                                   reason='sealed fit did not pass')
                continue
            if law not in conditioned.tasks:
                raise ValueError('passing fit missing from conditioning study')
            outcome = conditioned.envelope(law)['result']
            if outcome.get('passed') is not True:
                result[law] = dict(fit_passed=True,
                                   conditioned_passed=False,
                                   score=None,
                                   reason='sealed conditioning did not pass')
                continue
            forecast = fit.artifact(law, 'forecast.json')
            saved = conditioned.artifact(law, 'conditional-forecast.json')
            if (forecast['training_epochs'] != 400 or
                    forecast['prediction_epochs'] != 120 or
                    forecast['prediction_receiver_positions_used'] is not False or
                    saved['training_epochs'] != 400 or
                    saved['prediction_epochs'] != 120 or
                    saved['later_receiver_values_used'] is not False or
                    saved['optimization_performed'] is not False or
                    saved['raw_coordinates'] != forecast['coordinates']):
                raise ValueError('closed early-only forecast and correction required')
            result[law] = dict(fit_passed=True, conditioned_passed=True,
                               score=score_pair(
                                   forecast['coordinates'][400:],
                                   saved['conditional_receiver_mean'], receiver,
                                   saved['conditional_receiver_covariance']))
        return dict(version='esa-rolling-origin-400-conditional-score-v1',
            fit_study='data/' + FIT_ID,
            fit_manifest_sha256=fit.completion['manifest_sha256'],
            fit_summary_sha256=fit.completion['summary_sha256'],
            conditioning_study='data/' + CONDITION_ID,
            conditioning_manifest_sha256=conditioned.completion['manifest_sha256'],
            conditioning_summary_sha256=conditioned.completion['summary_sha256'],
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            training_receiver_reports=400, withheld_receiver_reports=120,
            laws=result, original_reads=0, protected_reads=0, new_fits=0,
            independent_validation=False, confidence_calibrated=False,
            physical_adequacy_qualified=False, scientific_decision='abstain')
    finally:
        parent.close()
        conditioned.close()
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'ROLLING_ORIGIN_400_CONDITIONAL_RESULT.json', encoded(result))
    rows = []
    for law in LAWS:
        item = result['laws'][law]
        if item['score'] is None:
            rows.append(f'| {law} | no | — | — | — |')
            continue
        score = item['score']
        raw = score['raw']['metrics']['horizontal_rms_m']
        corrected = score['conditional']['metrics']['horizontal_rms_m']
        height = score['conditional']['metrics']['vertical_rms_m']
        rows.append(f'| {law} | yes | {raw:.3f} | {corrected:.3f} | {height:.3f} |')
    available = [result['laws'][law]['score'] for law in LAWS
                 if result['laws'][law]['score'] is not None]
    if available:
        coverage = available[0]['coverage']
        axis_coverage = ', '.join(
            f"{axis} {round(120*coverage['axes'][axis]['nominal_95_fraction'])}/120"
            for axis in ('north', 'east', 'up'))
        lag_range = [coverage['axes'][axis]['lag_one_normalized_correlation']
                     for axis in ('north', 'east', 'up')]
        coverage_note = (
            f'Nominal 95% marginal ranges contain the later reports '
            f'({axis_coverage}). The normalized errors remain strongly '
            f'time-correlated (lag-one correlations {min(lag_range):.3f}–'
            f'{max(lag_range):.3f}); 120 reports therefore do not constitute '
            '120 independent checks. The two assumed IMU error laws give '
            'nearly identical forecasts and this comparison does not choose '
            'between them.\n\n')
    else:
        coverage_note = 'No conditioning task passed, so no later score is reported.\n\n'
    page = ('# Earlier-origin conditional forecast check\n\n'
        'The two fit outcomes and all available early-only conditioning tasks '
        'were sealed before the later 120 receiver positions were scored.\n\n'
        '| IMU error law | Both steps passed | Raw horizontal RMS (m) | '
        'Conditioned horizontal RMS (m) | Conditioned height RMS (m) |\n'
        '| --- | --- | ---: | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        + coverage_note +
        'The machine-readable result also gives signed errors and covariance '
        'details. This one selected development recording does '
        'not calibrate coverage or establish physical adequacy; the scientific '
        'decision is abstain. Seven reserved flight groups remain unopened.\n\n'
        '[Detailed result](ROLLING_ORIGIN_400_CONDITIONAL_RESULT.json).\n')
    atomic(base / 'ROLLING_ORIGIN_400_CONDITIONAL_RESULT.md', page.encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root)
    print(json.dumps({law: row['conditioned_passed']
                      for law, row in result['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
