# SPDX-License-Identifier: AGPL-3.0-or-later
"""A fresh cohort keeps the method while reserving enough measured runtime."""
import importlib
import importlib.util
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


def test_fresh_runtime_cohort_has_disjoint_seeds_and_finite_allowance():
    assert importlib.util.find_spec('lll.prediction_simultaneous_study_v3') is not None
    from lll import prediction_simultaneous_study as first
    from lll import prediction_simultaneous_study_v2 as second
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    assert third.IDENTITY == 'prediction-simultaneous-law-family-v3-runtime-20261112'
    assert third.recipe()['maximum_wall_s'] == 43200.
    assert third.recipe()['maximum_evaluations'] == 200
    assert len(third.tasks()) == 96
    seeds = [{item['payload']['noise_seed'] for item in module.tasks()}
             for module in (first, second, third)]
    assert all(len(group) == 96 for group in seeds)
    assert not (seeds[0] & seeds[2] or seeds[1] & seeds[2])
    assert third.preflight_task()['payload'] == third.tasks()[0]['payload']
    assert third.preflight_recipe()['duration_s'] == 2.
    assert third.preflight_recipe()['maximum_evaluations'] == 8


def test_changed_case_is_rejected_before_any_charge():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    case = third.tasks()[0]
    changed = dict(case, payload=dict(case['payload'], noise_seed=17))
    context = SimpleNamespace(manifest={'scope':third.SCOPE})
    try:
        third.evaluate(changed, context)
    except ValueError as error:
        assert 'changed or unqualified' in str(error)
    else:
        raise AssertionError('changed task was accepted')


def test_source_freeze_includes_new_adapter_test_and_plan():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    root = Path(__file__).resolve().parents[2]
    sources = third.qualification_sources(root)
    assert {
        'analysis/lll/prediction_simultaneous_study_v3.py',
        'analysis/tests/test_prediction_simultaneous_study_v3.py',
        'docs/prediction-simultaneous-law-family-v3/PLAN.md',
        'analysis/lll/prediction_simultaneous_study.py',
    } <= set(sources)


def test_release_tests_bind_fresh_cohort_checks():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    names = third.required_tests()
    assert 'test_fresh_runtime_cohort_has_disjoint_seeds_and_finite_allowance' in names
    assert 'test_changed_case_is_rejected_before_any_charge' in names
    assert 'test_source_freeze_includes_new_adapter_test_and_plan' in names
    assert 'test_short_generated_case_saves_two_target_scores_after_truth' in names
    assert 'test_new_study_requires_both_qualifications_before_mutation' in names
    assert 'test_short_preflight_rejects_unguarded_allocation' in names
    assert 'test_frozen_definitions_use_short_and_twelve_hour_caps' in names
    assert 'test_preflight_writes_a_separate_frozen_input_snapshot' in names
    assert 'test_full_study_refuses_an_unverified_preflight' in names
    assert 'test_software_and_recovery_qualification_requests_are_separate' in names
    assert 'test_cli_routes_new_qualification_without_creating_a_study' in names
    assert 'test_recovery_qualification_includes_the_versioned_source_list_fix' in names
    assert 'test_full_study_freezes_96_new_tasks_after_checked_preflight' in names
    assert 'test_short_frozen_worker_uses_preflight_scope_and_recipe' in names
    assert 'test_full_frozen_worker_uses_the_twelve_hour_recipe' in names


def test_new_study_requires_both_qualifications_before_mutation():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    with TemporaryDirectory() as directory:
        path = Path(directory)/'study'
        try:
            third.prepare(path, qualification=None, recovery_qualification=None)
        except ValueError as error:
            assert 'qualification' in str(error)
        else:
            raise AssertionError('unqualified study preparation was accepted')
        assert not path.exists()


def test_short_preflight_rejects_unguarded_allocation():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    with TemporaryDirectory() as directory:
        with patch('lll.airquantumgrav_inventory.environment',
                   return_value={'numerical_environment': {'unbounded': True}}):
            try:
                third.prepare_preflight(directory)
            except ValueError as error:
                assert 'guarded one-thread' in str(error)
            else:
                raise AssertionError('unguarded preflight was accepted')
        assert not (Path(directory)/'data'/third.PREFLIGHT_ID).exists()


def test_frozen_definitions_use_short_and_twelve_hour_caps():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    root = Path(__file__).resolve().parents[2]
    inputs = {'recipe':'data/inputs/recipe',
              'numerical_environment':'data/inputs/environment'}
    short = third.definition(root, preflight=True, inputs=inputs)
    full = third.definition(root, preflight=False, inputs=inputs)
    assert short['id'] == third.PREFLIGHT_ID
    assert short['workers'] == 1 and short['threads'] == 1
    assert short['maximum_wall_s'] == 600.
    assert len(short['tasks']) == 1
    assert full['id'] == third.IDENTITY
    assert full['workers'] == 4 and full['threads'] == 1
    assert full['maximum_wall_s'] == 43200.
    assert len(full['tasks']) == 96
    assert full['inputs'] == inputs
    assert 'docs/prediction-simultaneous-law-family-v3/PLAN.md' in full['sources']


def test_preflight_writes_a_separate_frozen_input_snapshot():
    import json
    from lll.compute_budget import environment as numerical_environment
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    env = {'numerical_environment': numerical_environment(workers=1, threads=1),
           'fixture':'preflight'}
    captured = []

    def fake_definition(value, root):
        captured.append(value)
        return SimpleNamespace(prepare=lambda _: {'allocation': {'workers':1}})

    with TemporaryDirectory() as directory:
        with patch('lll.airquantumgrav_inventory.environment', return_value=env), \
             patch.object(third, 'qualification_sources',
                          return_value=['analysis/lll/prediction_simultaneous_study_v3.py']), \
             patch('lll.studies.runtime.Definition.from_dict',
                   side_effect=fake_definition):
            result = third.prepare_preflight(directory)
        source = Path(directory)/'data'/(third.PREFLIGHT_ID+'-inputs')
        assert result['path'] == 'data/'+third.PREFLIGHT_ID
        assert result['total'] == 1
        assert captured[0]['maximum_wall_s'] == 600.
        assert json.loads((source/'recipe').read_bytes()) == third.preflight_recipe()
        assert json.loads((source/'numerical_environment').read_bytes()) == env


def test_full_study_refuses_an_unverified_preflight():
    from lll.compute_budget import environment as numerical_environment
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    env = {'numerical_environment': numerical_environment(workers=4, threads=1)}
    with TemporaryDirectory() as directory:
        with patch('lll.airquantumgrav_inventory.environment', return_value=env), \
             patch.object(third, 'qualification_sources', return_value=[]), \
             patch.object(third, 'recovery_sources', return_value=[], create=True), \
             patch('lll.studies.qualification.checked',
                   return_value=(b'request', b'report')), \
             patch('lll.ilvis0_control_shards.verify_completion',
                   return_value={'passed':False, 'completed':0}):
            try:
                third.prepare(directory, qualification='software',
                              recovery_qualification='recovery')
            except ValueError as error:
                assert 'preflight' in str(error)
            else:
                raise AssertionError('unverified preflight was accepted')
        assert not (Path(directory)/'data'/third.IDENTITY).exists()


def test_software_and_recovery_qualification_requests_are_separate():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    captured = []

    def capture(root, **kwargs):
        captured.append(kwargs)
        return kwargs['output']

    with TemporaryDirectory() as directory:
        with patch('lll.studies.qualification.request', side_effect=capture), \
             patch('lll.airquantumgrav_inventory.environment', return_value={'source':True}), \
             patch('lll.ilvis0_control_shards.runtime_environment',
                   return_value={'recovery':True}), \
             patch.object(third, 'qualification_sources', return_value=['adapter']), \
             patch.object(third, 'recovery_sources', return_value=['recovery']):
            third.request_qualification(directory)
            third.request_qualification(directory, recovery=True)
    assert captured[0]['sources'] == ['adapter']
    assert captured[0]['environment'] == {'source':True}
    assert captured[0]['output'].endswith('/request.json')
    assert captured[1]['sources'] == ['recovery']
    assert captured[1]['environment'] == {'recovery':True}
    assert captured[1]['output'].endswith('/recovery-request.json')


def test_cli_routes_new_qualification_without_creating_a_study():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    with TemporaryDirectory() as directory:
        with patch.object(third, 'request_qualification',
                          return_value={'request':'frozen'}) as requested:
            result = third.main(['request', '--root', directory])
        requested.assert_called_once_with(directory)
        assert result == {'request':'frozen'}
        assert not (Path(directory)/'data').exists()


def test_recovery_qualification_includes_the_versioned_source_list_fix():
    from lll.studies.task_resume_sourcefix import SOURCE, TEST, TEST_NAME
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    root = Path(__file__).resolve().parents[2]
    sources = third.recovery_sources(root)
    assert len(sources) == len(set(sources))
    assert SOURCE in sources and TEST in sources
    assert TEST_NAME in third.recovery_required_tests()


def test_full_study_freezes_96_new_tasks_after_checked_preflight():
    import json
    from lll.compute_budget import environment as numerical_environment
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    env = {'numerical_environment': numerical_environment(workers=4, threads=1)}
    captured = []

    def fake_definition(value, root):
        captured.append(value)
        return SimpleNamespace(prepare=lambda _: {'allocation': {'workers':4}})

    with TemporaryDirectory() as directory:
        with patch('lll.airquantumgrav_inventory.environment', return_value=env), \
             patch.object(third, 'qualification_sources', return_value=['adapter']), \
             patch.object(third, 'recovery_sources', return_value=['recovery']), \
             patch('lll.studies.qualification.checked',
                   return_value=(b'request', b'report')), \
             patch('lll.ilvis0_control_shards.verify_completion',
                   return_value={'passed':True, 'completed':1}), \
             patch('lll.studies.runtime.Definition.from_dict',
                   side_effect=fake_definition):
            result = third.prepare(directory, qualification='software',
                                   recovery_qualification='recovery')
        source = Path(directory)/'data'/(third.IDENTITY+'-inputs')
        assert result['path'] == 'data/'+third.IDENTITY
        assert result['total'] == 96
        assert captured[0]['maximum_wall_s'] == 43200.
        assert len(captured[0]['tasks']) == 96
        assert json.loads((source/'recipe').read_bytes()) == third.recipe()
        assert (source/'qualification_request').read_bytes() == b'request'
        assert (source/'recovery_report').read_bytes() == b'report'


def test_short_frozen_worker_uses_preflight_scope_and_recipe():
    import json
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    env = {'fixture':'preflight'}
    with TemporaryDirectory() as directory:
        files = {'recipe':Path(directory)/'recipe',
                 'numerical_environment':Path(directory)/'environment'}
        files['recipe'].write_text(json.dumps(third.preflight_recipe()))
        files['numerical_environment'].write_text(json.dumps(env))
        context = SimpleNamespace(manifest={'scope':third.PREFLIGHT_SCOPE},
                                  input_path=lambda key:files[key])
        with patch('lll.airquantumgrav_inventory.environment', return_value=env), \
             patch.object(third.base, 'run_case',
                          return_value={'technical_pair_complete':True}) as run:
            result = third.evaluate(third.preflight_task(), context)
        assert result['technical_pair_complete'] is True
        assert run.call_args.kwargs['r']['maximum_evaluations'] == 8
        with patch('lll.airquantumgrav_inventory.environment', return_value=env), \
             patch.object(third.base, 'run_case',
                          return_value={'technical_pair_complete':False}):
            try:
                third.evaluate(third.preflight_task(), context)
            except ValueError as error:
                assert 'preflight' in str(error)
            else:
                raise AssertionError('incomplete preflight was accepted')


def test_full_frozen_worker_uses_the_twelve_hour_recipe():
    import json
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    env = {'fixture':'full'}
    with TemporaryDirectory() as directory:
        files = {'recipe':Path(directory)/'recipe',
                 'numerical_environment':Path(directory)/'environment'}
        files['recipe'].write_text(json.dumps(third.recipe()))
        files['numerical_environment'].write_text(json.dumps(env))
        context = SimpleNamespace(manifest={'scope':third.SCOPE},
                                  input_path=lambda key:files[key])
        with patch('lll.airquantumgrav_inventory.environment', return_value=env), \
             patch.object(third.base, 'run_case',
                          return_value={'technical_pair_complete':True}) as run:
            third.evaluate(third.tasks()[0], context)
        assert run.call_args.kwargs['r']['maximum_wall_s'] == 43200.
        assert run.call_args.kwargs['r']['maximum_evaluations'] == 200


def test_launch_refuses_less_than_35_gib_free_before_worker_start():
    third = importlib.import_module('lll.prediction_simultaneous_study_v3')
    with TemporaryDirectory() as directory:
        with patch('shutil.disk_usage',
                   return_value=SimpleNamespace(free=34*1024**3)), \
             patch('lll.ilvis0_control_shards.launch') as worker:
            try:
                third.launch(directory)
            except ValueError as error:
                assert '35 GiB' in str(error)
            else:
                raise AssertionError('low-space launch was accepted')
        worker.assert_not_called()


if __name__ == '__main__':
    test_fresh_runtime_cohort_has_disjoint_seeds_and_finite_allowance()
    test_changed_case_is_rejected_before_any_charge()
    test_source_freeze_includes_new_adapter_test_and_plan()
    test_release_tests_bind_fresh_cohort_checks()
    test_new_study_requires_both_qualifications_before_mutation()
    test_short_preflight_rejects_unguarded_allocation()
    test_frozen_definitions_use_short_and_twelve_hour_caps()
    test_preflight_writes_a_separate_frozen_input_snapshot()
    test_full_study_refuses_an_unverified_preflight()
    test_software_and_recovery_qualification_requests_are_separate()
    test_cli_routes_new_qualification_without_creating_a_study()
    test_recovery_qualification_includes_the_versioned_source_list_fix()
    test_full_study_freezes_96_new_tasks_after_checked_preflight()
    test_short_frozen_worker_uses_preflight_scope_and_recipe()
    test_full_frozen_worker_uses_the_twelve_hour_recipe()
    test_launch_refuses_less_than_35_gib_free_before_worker_start()
