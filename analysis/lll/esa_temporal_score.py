# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score a sealed ESA temporal-transfer forecast; never refit or reselect."""

import gzip
import hashlib
import json
import math
from pathlib import Path


SOURCE_PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
LAWS = ('increment', 'point')


def build(root, *, fit_study, training_epochs, total_epochs):
    import numpy as np
    from .esa_rolling_origin_400_score import score_raw
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    if (type(training_epochs) is not int or type(total_epochs) is not int or
            not 2 <= training_epochs < total_epochs <= 800 or
            total_epochs-training_epochs != 120):
        raise ValueError('declared 120-report withheld cut required')
    fit = ClosedStudy(root, fit_study)
    parent = ClosedStudy(root, SOURCE_PARENT)
    try:
        if (fit.completion['state'] not in ('complete', 'terminal') or
                fit.summary['completed'] != 2 or set(fit.tasks) != set(LAWS)):
            raise ValueError('both sealed temporal-transfer outcomes required')
        origin = fit.input('parent_identity')
        if (origin['source_id'] != 'esa-99f1530c3eda4318' or
                origin['manifest_sha256'] != parent.completion['manifest_sha256'] or
                origin['summary_sha256'] != parent.completion['summary_sha256']):
            raise ValueError('sealed development parent differs')
        all_rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        if len(all_rows) != 800:
            raise ValueError('complete development receiver history required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']), row['height_m']]
            for row in all_rows[training_epochs:total_epochs]], dtype=float)
        scored = {}
        for law in LAWS:
            outcome = fit.envelope(law)['result']
            if (outcome.get('law') != law or
                    outcome.get('later_receiver_positions_used') is not False):
                raise ValueError('earlier-only fit outcome differs')
            if outcome.get('passed') is not True:
                scored[law] = dict(fit_passed=False, raw_score=None,
                                   reason='sealed fit did not pass')
                continue
            record = fit.artifact(law, 'fit.json')
            forecast = fit.artifact(law, 'forecast.json')
            if (record['converged'] is not True or
                    forecast['training_epochs'] != training_epochs or
                    forecast['prediction_epochs'] != 120 or
                    forecast['prediction_receiver_positions_used'] is not False or
                    len(forecast['coordinates']) != total_epochs or
                    len(forecast['times_s']) != total_epochs):
                raise ValueError('complete sealed temporal-transfer forecast required')
            scored[law] = dict(fit_passed=True,
                               evaluations=record['evaluations'],
                               active_bounds=record['active_bounds'],
                               raw_score=score_raw(
                                   forecast['coordinates'][training_epochs:],
                                   receiver))
        return dict(version='esa-temporal-raw-score-v1',
                    fit_study=fit_study,
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    fit_summary_sha256=fit.completion['summary_sha256'],
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    raw_scorer_sha256=hashlib.sha256((root/
                        'analysis/lll/esa_rolling_origin_400_score.py')
                        .read_bytes()).hexdigest(),
                    training_receiver_reports=training_epochs,
                    withheld_receiver_reports=120,
                    scored_laws=scored, original_reads=0, protected_reads=0,
                    new_fits=0, independent_validation=False,
                    error_law_qualified=False,
                    physical_adequacy_qualified=False,
                    scientific_decision='abstain')
    finally:
        parent.close()
        fit.close()


def publish_200(root):
    from .esa_rolling_origin_200_study import ID
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root, fit_study='data/'+ID,
                   training_epochs=200, total_epochs=320)
    base = root/'docs/prediction-observed-development'
    atomic(base/'ROLLING_ORIGIN_200_RAW_RESULT.json', encoded(result))
    rows = []
    for law in LAWS:
        item = result['scored_laws'][law]
        if item['fit_passed']:
            metrics = item['raw_score']['metrics']
            rows.append('| {} | yes | {:.3f} | {:.3f} |'.format(
                law, metrics['horizontal_rms_m'], metrics['vertical_rms_m']))
        else:
            rows.append('| {} | no | — | — |'.format(law))
    page = ('# Earlier-origin raw forecast check\n\n'
        'Both fit outcomes sealed before receiver reports 200–319 were '
        'scored. These are direct forecast errors without receiver '
        'conditioning.\n\n'
        '| IMU error law | Fit passed | Horizontal RMS (m) | Height RMS (m) |\n'
        '|---|---|---:|---:|\n'+'\n'.join(rows)+'\n\n'
        'This is a different interval of the **same** development flight, '
        'not an independent replication. The signed errors, numerical '
        'dispositions and hashes are in the '
        '[machine-readable result](ROLLING_ORIGIN_200_RAW_RESULT.json). '
        'Prediction-error coverage and physical adequacy remain unqualified; '
        'the scientific decision is abstain.\n')
    atomic(base/'ROLLING_ORIGIN_200_RAW_RESULT.md', page.encode())
    return result


def build_conditioned(root, *, fit_study, conditioning_study,
                      training_epochs, total_epochs):
    import numpy as np
    from .esa_rolling_origin_400_conditioning_score import score_pair
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    raw = build(root, fit_study=fit_study,
                training_epochs=training_epochs, total_epochs=total_epochs)
    fit = ClosedStudy(root, fit_study)
    conditioned = ClosedStudy(root, conditioning_study)
    parent = ClosedStudy(root, SOURCE_PARENT)
    try:
        if (conditioned.completion['state'] not in ('complete', 'terminal') or
                conditioned.summary['completed'] != conditioned.summary['total'] or
                conditioned.input('fit_identity') != dict(
                    prefix=fit_study,
                    manifest_sha256=fit.completion['manifest_sha256'],
                    summary_sha256=fit.completion['summary_sha256'])):
            raise ValueError('all permitted conditioning outcomes must be sealed')
        rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        if len(rows) != 800:
            raise ValueError('complete source receiver history required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']), row['height_m']]
            for row in rows[training_epochs:total_epochs]], dtype=float)
        results = {}
        for law in LAWS:
            if not raw['scored_laws'][law]['fit_passed']:
                results[law] = dict(fit_passed=False,
                                    conditioned_passed=False,
                                    score=None,
                                    reason='sealed fit did not pass')
                continue
            if law not in conditioned.tasks:
                raise ValueError('passing fit missing from conditioning study')
            outcome = conditioned.envelope(law)['result']
            if outcome.get('passed') is not True:
                results[law] = dict(fit_passed=True,
                                    conditioned_passed=False,
                                    score=None,
                                    reason='sealed conditioning did not pass')
                continue
            forecast = fit.artifact(law, 'forecast.json')
            saved = conditioned.artifact(law, 'conditional-forecast.json')
            if (forecast['training_epochs'] != training_epochs or
                    forecast['prediction_epochs'] != 120 or
                    forecast['prediction_receiver_positions_used'] is not False or
                    saved['training_epochs'] != training_epochs or
                    saved['prediction_epochs'] != 120 or
                    saved['later_receiver_values_used'] is not False or
                    saved['optimization_performed'] is not False or
                    saved['raw_coordinates'] != forecast['coordinates']):
                raise ValueError('closed early-only correction differs')
            score = score_pair(
                forecast['coordinates'][training_epochs:],
                saved['conditional_receiver_mean'], receiver,
                saved['conditional_receiver_covariance'])
            if score['raw'] != raw['scored_laws'][law]['raw_score']:
                raise ValueError('raw score changed across sealed stages')
            results[law] = dict(fit_passed=True, conditioned_passed=True,
                                score=score)
        return dict(version='esa-temporal-conditional-score-v1',
                    fit_study=fit_study,
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    fit_summary_sha256=fit.completion['summary_sha256'],
                    conditioning_study=conditioning_study,
                    conditioning_manifest_sha256=conditioned.completion[
                        'manifest_sha256'],
                    conditioning_summary_sha256=conditioned.completion[
                        'summary_sha256'],
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    dependency_sha256={name:hashlib.sha256((root/name).read_bytes())
                        .hexdigest() for name in (
                        'analysis/lll/esa_rolling_origin_400_score.py',
                        'analysis/lll/esa_rolling_origin_400_conditioning_score.py')},
                    training_receiver_reports=training_epochs,
                    withheld_receiver_reports=120, laws=results,
                    original_reads=0, protected_reads=0, new_fits=0,
                    independent_validation=False,
                    confidence_calibrated=False,
                    physical_adequacy_qualified=False,
                    scientific_decision='abstain')
    finally:
        parent.close()
        conditioned.close()
        fit.close()


def publish_conditioned_200(root):
    from .esa_rolling_origin_200_conditioning import ID as CONDITION_ID
    from .esa_rolling_origin_200_study import ID as FIT_ID
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build_conditioned(
        root, fit_study='data/'+FIT_ID,
        conditioning_study='data/'+CONDITION_ID,
        training_epochs=200, total_epochs=320)
    base = root/'docs/prediction-observed-development'
    atomic(base/'ROLLING_ORIGIN_200_CONDITIONAL_RESULT.json', encoded(result))
    rows = []
    for law in LAWS:
        item = result['laws'][law]
        if item['score'] is None:
            rows.append(f'| {law} | no | — | — | — |')
        else:
            score = item['score']
            rows.append('| {} | yes | {:.3f} | {:.3f} | {:.3f} |'.format(
                law, score['raw']['metrics']['horizontal_rms_m'],
                score['conditional']['metrics']['horizontal_rms_m'],
                score['conditional']['metrics']['vertical_rms_m']))
    available = [result['laws'][law]['score'] for law in LAWS
                 if result['laws'][law]['score'] is not None]
    if available:
        coverage = available[0]['coverage']
        covered = ', '.join('{} {}/120'.format(axis, round(120*coverage[
            'axes'][axis]['nominal_95_fraction']))
            for axis in ('north', 'east', 'up'))
        dependence = [coverage['axes'][axis]['lag_one_normalized_correlation']
                      for axis in ('north', 'east', 'up')]
        note = ('Nominal 95% ranges contain the later reports ({}). '
                'Lag-one normalized-error correlations range from {:.3f} '
                'to {:.3f}; these 120 reports are not independent coverage '
                'trials.\n\n').format(covered, min(dependence), max(dependence))
    else:
        note = 'No conditioning task passed; no later score is reported.\n\n'
    page = ('# Earlier-origin conditional forecast check\n\n'
        'Both fits and all permitted conditioning tasks sealed before '
        'receiver reports 200–319 were scored.\n\n'
        '| IMU error law | Both steps passed | Raw horizontal RMS (m) | '
        'Conditioned horizontal RMS (m) | Conditioned height RMS (m) |\n'
        '|---|---|---:|---:|---:|\n'+'\n'.join(rows)+'\n\n'+note+
        'This is a second start time in the **same opened flight**. It '
        'checks temporal transfer but does not calibrate prediction-error '
        'coverage on independent aircraft or select an Earth model. The '
        '[machine-readable result](ROLLING_ORIGIN_200_CONDITIONAL_RESULT.json) '
        'retains signed errors, numerical dispositions and hashes. Seven '
        'reserved ESA flight groups remain closed.\n')
    atomic(base/'ROLLING_ORIGIN_200_CONDITIONAL_RESULT.md', page.encode())
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check-400', 'check-conditioned-400',
                                           'publish-200', 'publish-conditioned-200'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'check-400':
        result = build(args.root,
            fit_study='data/esa-rolling-origin-400-development-v1-20261115',
            training_epochs=400, total_epochs=520)
    elif args.action == 'check-conditioned-400':
        result = build_conditioned(args.root,
            fit_study='data/esa-rolling-origin-400-development-v1-20261115',
            conditioning_study='data/esa-rolling-origin-400-conditioning-v1-20261115',
            training_epochs=400, total_epochs=520)
    elif args.action == 'publish-200':
        result = publish_200(args.root)
    else:
        result = publish_conditioned_200(args.root)
    entries = result.get('scored_laws', result.get('laws'))
    print(json.dumps({law: row['fit_passed'] for law, row in
                      entries.items()}, sort_keys=True))


if __name__ == '__main__':
    main()
