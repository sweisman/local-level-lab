# SPDX-License-Identifier: AGPL-3.0-or-later
"""Choose an ESA forecast using sealed training evidence before scoring access."""

from collections import defaultdict
import json
import math

from .studies.artifacts import digest, encoded


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _verified_forecast(study, key, fit, model, times, cut):
    raw = study.artifact(key, 'forecast.json', raw=True)
    forecast = json.loads(raw)
    positions = forecast['coordinates']
    if (forecast['training_epochs'] != cut
            or forecast['prediction_epochs'] != len(times)-cut
            or forecast['times_s'] != times
            or forecast['continuous_propagation_without_gps_reset'] is not True
            or forecast['prediction_receiver_positions_used'] is not False
            or forecast['frozen_error_model'] != model
            or forecast['active_parameters'] != fit['active_parameters']
            or forecast['normalized_parameters'] != fit['normalized_parameters']
            or len(positions) != len(times)
            or any(len(row) != 3 or not all(_finite(value) for value in row) for row in positions)):
        raise ValueError('forecast does not match the sealed fit or query support')
    return digest(raw)


def select(study, *, tasks, times, training_epochs):
    """Validate the complete saved matrix and select using earlier loss only."""
    cut = training_epochs
    times = list(times)
    tasks = tuple(tasks)
    expected = {task['identity']:task for task in tasks}
    if (not tasks or len(expected) != len(tasks) or type(cut) is not int
            or not 2 <= cut < len(times) or not all(_finite(t) for t in times)
            or any(b <= a for a, b in zip(times, times[1:]))
            or study.completion['state'] not in ('complete', 'terminal')
            or set(study.rows) != set(expected)
            or {k:{a:b for a,b in v.items() if a not in ('index', 'shard')}
                for k,v in study.tasks.items()} != expected):
        raise ValueError('all predeclared forecast tasks must have sealed dispositions')
    grouped = defaultdict(list)
    for key, task in expected.items():
        spec = task['payload']
        row = study.rows[key]
        envelope = study.envelope(key)
        if (envelope['task_sha256'] != digest(encoded(study.tasks[key]))
                or envelope['status'] != row['status']
                or envelope['charged'] != row['charged']
                or row['status'] not in ('complete', 'interrupted')):
            raise ValueError('sealed task identity, status or charge differs')
        start = dict(identity=key, start=spec['start'], known=False, converged=False,
                     training_cost=None, forecast_sha256=None)
        if row['status'] == 'complete':
            result = envelope['result']
            fit = study.artifact(key, 'fit.json')
            cost = fit.get('gaussian_training_score', {}).get('negative_log_likelihood')
            if (any(result[k] != v for k,v in spec.items()) or not _finite(cost)
                    or fit['model'] != spec['model'] or type(fit['converged']) is not bool
                    or result['numerical_converged'] is not fit['converged']
                    or result['later_receiver_positions_used'] is not False
                    or fit['prediction_receiver_positions_used_in_training'] is not False
                    or (result['passed'] and not fit['converged'])):
                raise ValueError('sealed training outcome has inconsistent fit or data-use metadata')
            forecast_hash = (_verified_forecast(study, key, fit, spec['model'], times, cut)
                             if result['passed'] else None)
            start.update(known=True, converged=fit['converged'],
                         training_cost=cost, forecast_sha256=forecast_hash)
        grouped[(spec['profile'], spec['law'], spec['model'])].append(start)

    settings = defaultdict(dict)
    for (profile, law, model), candidates in grouped.items():
        best = None
        if all(row['known'] for row in candidates):
            best = min((row for row in candidates if row['converged']),
                       default=None, key=lambda row:(row['training_cost'], row['start']))
        settings[profile, law][model] = best if best and best['forecast_sha256'] else None
    return [dict(profile=profile, law=law, primaries=primaries)
            for (profile, law), primaries in sorted(settings.items())]


def score_after_seal(study, *, tasks, times, training_epochs, score):
    """Invoke the scoring provider only after selection and forecast verification."""
    return score(select(study, tasks=tasks, times=times, training_epochs=training_epochs))
