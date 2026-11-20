# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify saved ESA code-comparison tables without study or receiver inputs."""

import json
import math
from pathlib import Path
from zipfile import ZipFile

from .airquantumgrav_geographic_report import _same_metrics, error_metrics
from .esa_alternate_ppp_scoring import rank_setting
from .esa_rinex_code_comparison import BASE, FOLDER, METHODS
from .ilvis0_prediction_observed import accuracy_screen
from .studies.artifacts import digest, encoded


def audit(folder):
    receipt = json.loads((folder / 'esa-rinex-code-comparison-result.json').read_bytes())
    ppp_bytes = (folder / 'esa-alternate-ppp-scoring-result.json').read_bytes()
    with ZipFile(folder / 'esa-rinex-code-comparison-freeze.zip') as archive:
        freeze_bytes = archive.read(BASE + 'comparison-freeze.json')
    frozen = json.loads(freeze_bytes)
    result = receipt['result']
    if (digest(encoded(result)) != receipt['result_sha256']
            or digest(freeze_bytes) != receipt['freeze_sha256']
            or digest(ppp_bytes) != frozen['prior_ppp']):
        raise ValueError('comparison result, freeze or parent score hash differs')
    if (frozen['observed_groups'] != ['187'] or result['protected_reads'] != 0
            or result['new_fits'] != 0 or result['new_forecast_propagations'] != 0
            or result['scientific_decision'] != 'abstain'):
        raise ValueError('unexpected comparison scope')

    later = result['later_epochs']
    total = result['matched_epochs']
    indices = result['matched_code_indices']
    if (len(indices) != total or indices != sorted(set(indices))
            or not 0 < later < total):
        raise ValueError('unexpected epoch coverage')
    receiver_checks = {}
    for method in METHODS:
        comparison = result['code_minus_receiver'][method]
        samples = comparison['signed_errors_neu_m']
        if len(samples) != total:
            raise ValueError('incomplete signed receiver errors')
        receiver_checks[method] = {}
        for label, portion in (('earlier', samples[:-later]), ('later', samples[-later:])):
            metrics = error_metrics(portion)
            means = [math.fsum(axis) / len(portion) for axis in zip(*portion, strict=True)]
            _same_metrics(dict(metrics, signed_mean_neu_m=means), comparison[label])
            receiver_checks[method][label] = metrics

    parent = json.loads(ppp_bytes)
    parent_scores = {(row['profile'], row['law']): row['by_receiver']['air1']
                     for row in parent['settings']}
    matched_settings = [(row['profile'], row['law']) for row in result['forecast_comparisons']]
    if len(matched_settings) != len(parent_scores) or set(matched_settings) != set(parent_scores):
        raise ValueError('incomplete matched forecast settings')
    tables = []
    for row, setting in zip(result['forecast_comparisons'], matched_settings, strict=True):
        if set(row['by_code']) != set(METHODS):
            raise ValueError('incomplete code forecast methods')
        reports = {'air1': parent_scores[setting], **row['by_code']}
        totals = {}
        for name, report in reports.items():
            scores = report['scores']
            if (any(score['matched_epochs'] != later
                    or score['accuracy'] != accuracy_screen(score)['passed']
                    for score in scores.values())
                    or rank_setting(scores) != report['ranking']):
                raise ValueError('forecast table differs from the saved scores')
            totals[name] = {model: score['total_rms_m'] for model, score in scores.items()}
        tables.append(dict(profile=setting[0], law=setting[1], total_rms_m=totals))
    return tables, receiver_checks


if __name__ == '__main__':
    forecasts, receivers = audit(Path(FOLDER))
    print(encoded(dict(forecast_tables=forecasts, receiver_errors=receivers)).decode(), end='')
