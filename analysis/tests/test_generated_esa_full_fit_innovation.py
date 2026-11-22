"""Finite generated 600-report full-fit innovation pilot wiring."""

from unittest.mock import patch

import pytest


def test_full_pilot_has_two_600_report_tasks_and_finite_limits():
    from lll import generated_esa_full_fit_innovation as study

    recipe = study.recipe()
    assert recipe['duration_s'] == 900.
    assert recipe['rate_hz'] == 300
    assert recipe['queries'] == 900
    assert recipe['maximum_evaluations'] == 200
    assert recipe['workers'] == 2
    assert recipe['threads'] == 1
    tasks = study.tasks(recipe)
    assert [task['identity'] for task in tasks] == ['increment', 'point']
    assert all(task['limits']['native_calls'] > 0 for task in tasks)
    assert all(task['limits']['packet_visits'] > 0 for task in tasks)
    assert study.preflight_recipe()['maximum_evaluations'] == 8
    assert study.preflight_task()['identity'] == 'preflight-increment'


def test_evaluator_refuses_changed_task_before_shared_worker():
    from lll import generated_esa_full_fit_innovation as study

    class Context:
        manifest = {'scope': study.SCOPE}

        def input_path(self, key):
            raise AssertionError('changed task must fail before input read')

    task = dict(study.tasks()[0], identity='changed')
    with patch.object(study, 'run_case') as worker:
        with pytest.raises(ValueError):
            study.evaluate(task, Context())
        worker.assert_not_called()


def test_frozen_definition_counts_preflight_and_full():
    from lll import generated_esa_full_fit_innovation as study

    pre = study.definition('.', preflight=True, inputs={'recipe': 'x'})
    full = study.definition('.', preflight=False, inputs={'recipe': 'x'})
    assert len(pre['tasks']) == 1
    assert pre['workers'] == 1
    assert pre['maximum_wall_s'] == 600.
    assert len(full['tasks']) == 2
    assert full['workers'] == 2
    assert full['maximum_wall_s'] == 21600.


def test_preflight_pass_means_artifacts_even_if_short_fit_does_not_converge(tmp_path):
    import json
    from lll import generated_esa_full_fit_innovation as study
    from lll.airquantumgrav_inventory import environment

    (tmp_path / 'recipe').write_text(json.dumps(study.preflight_recipe()))
    (tmp_path / 'environment').write_text(json.dumps(environment()))

    class Context:
        manifest = {'scope': study.PREFLIGHT_SCOPE}

        def input_path(self, key):
            return tmp_path / key

    result = dict(passed=False, forecast_saved_before_scoring=True,
                  training_epochs=6, prediction_epochs=3,
                  scientific_decision='abstain')
    with patch.object(study, 'run_case', return_value=result):
        answer = study.evaluate(study.preflight_task(), Context())
    assert answer['passed'] is True
    assert answer['original_prediction_passed'] is False
    assert answer['preflight_only'] is True


def test_cli_passes_project_relative_qualification_paths():
    from lll import generated_esa_full_fit_innovation as study

    with patch.object(study, 'prepare', return_value={'path': 'prepared'}) as go:
        study.main(['prepare-preflight', '--root', '.'])
    assert isinstance(go.call_args.kwargs['qualification'], str)
    assert isinstance(go.call_args.kwargs['recovery_qualification'], str)
