# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the sealed generated source before replaying any later observations."""

from pathlib import Path

SOURCE = 'data/generated-matched-one-sided-v2-20261117'
CASE = 'straight-level'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')


def verify_source(root, *, expected_environment=None):
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    source = ClosedStudy(root, SOURCE)
    try:
        if source.completion['state'] != 'complete' or source.summary['completed'] != 2:
            raise ValueError('complete two-case sealed source required')
        if expected_environment is not None and source.input('environment') != expected_environment:
            raise ValueError('frozen numerical environment differs')
        changed = [name for name, sha in source.manifest['sources'].items()
                   if digest((root / name).read_bytes()) != sha]
        if changed:
            raise ValueError('frozen source differs: ' + changed[0])
        task = source.tasks[CASE]
        if (task['payload'].get('route') != 'straight'
                or task['payload'].get('height_profile') != 'level'
                or task['payload'].get('truth_model') != 'sphere_rotating'
                or not source.rows[CASE]['passed']):
            raise ValueError('exact passed straight-level source task required')
        recipe = source.input('recipe')
        binding = source.artifact(CASE, 'noise-binding.json')
        training = source.artifact(CASE, 'training-receiver.json')
        if (len(training) < 2 or len(training) >= recipe['queries']
                or digest(encoded(training)) != binding['noisy_training_receiver_sha256']):
            raise ValueError('training receiver binding differs')
        candidates = {}
        for model in MODELS:
            fit = source.artifact(CASE, f'candidates/{model}/fit.json')
            forecast = source.artifact(CASE, f'candidates/{model}/forecast.json')
            training_operator = source.artifact(CASE,
                f'candidates/{model}/training-error-operator.json')
            if (fit['model'] != model or forecast['frozen_error_model'] != model
                    or fit['active_parameters'] != forecast['active_parameters']
                    or len(fit['active_parameters']) != 26
                    or fit['normalized_parameters'] != forecast['normalized_parameters']
                    or forecast['training_epochs'] != len(training)
                    or forecast['prediction_epochs'] <= 0
                    or len(forecast['coordinates']) != len(forecast['times_s'])
                    or len(forecast['coordinates']) != recipe['queries']
                    or training_operator['model'] != model
                    or training_operator['operator_configuration'] != forecast['error_training_configuration']):
                raise ValueError('sealed candidate fit, forecast or error binding differs: ' + model)
            candidates[model] = dict(fit=fit, forecast=forecast,
                                     training_operator=training_operator)
        return dict(source_completion_sha256=digest(encoded(source.completion)),
                    source_manifest_sha256=source.completion['manifest_sha256'],
                    recipe=recipe, task=task, binding=binding, training=training,
                    candidates=candidates)
    finally:
        source.close()
