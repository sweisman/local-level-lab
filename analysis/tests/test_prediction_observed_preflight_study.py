"""Frozen task and preparation gates for the no-fit ESA preflight."""

from pathlib import Path

import pytest


def test_observed_preflight_has_four_finite_target_law_tasks():
    from lll.prediction_observed_preflight_study import recipe, tasks
    r = recipe()
    work = tasks(r)
    assert len(work) == 4
    assert {row['identity'] for row in work} == {
        f'{law}-{target}' for law in ('increment', 'point')
        for target in ('physical_position', 'receiver_measurement')}
    assert all(row['limits']['native_calls'] == 601895 for row in work)
    assert all(row['limits']['packet_visits'] == 601895 for row in work)
    assert r['workers'] * r['threads'] == 4
    assert r['maximum_wall_s'] == 14400.
    assert r['model'] == 'sphere_rotating'
    assert r['profile'] is False
    assert r['policy_id'] == 'reported-short-v1'


def test_observed_preflight_requires_qualification_before_archive_reads(tmp_path):
    from lll.prediction_observed_preflight_study import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None, recovery_qualification=None)
    assert not (tmp_path/'data').exists()


def test_observed_preflight_source_freeze_includes_adapter_and_plan():
    from lll.prediction_observed_preflight_study import qualification_sources
    paths = set(qualification_sources(Path.cwd()))
    assert {'analysis/lll/prediction_observed_material.py',
            'analysis/lll/prediction_observed_preflight.py',
            'analysis/lll/prediction_observed_native.py',
            'analysis/lll/prediction_observed_preflight_study.py',
            'analysis/tests/test_prediction_observed_preflight.py',
            'analysis/tests/test_prediction_observed_preflight_study.py',
            'docs/prediction-observed-law-preflight/PLAN.md'} <= paths


def test_observed_preflight_definition_has_no_scoring_artifact():
    from lll.prediction_observed_preflight_study import definition
    inputs = {name: f'data/prepared/{name}' for name in
              ('interval', 'training', 'layout', 'frozen-hashes', 'context',
               'recipe', 'numerical_environment', 'parent-binding',
               'qualification-request', 'qualification-report',
               'recovery-request', 'recovery-report')}
    frozen = definition(Path.cwd(), inputs=inputs)
    assert frozen['inputs'] == inputs
    assert 'scoring' not in frozen['inputs']
    assert frozen['workers'] == 4
    assert frozen['threads'] == 1
    assert frozen['maximum_wall_s'] == 14400.
    assert len(frozen['tasks']) == 4
    with pytest.raises(ValueError, match='scoring'):
        definition(Path.cwd(), inputs=dict(inputs, scoring='forbidden'))


def test_observed_preflight_rejects_changed_task_before_input_read():
    from lll.prediction_observed_preflight_study import evaluate, tasks

    class Context:
        manifest = {'scope': 'wrong'}

        def input_path(self, name=None):
            raise AssertionError('input opened before scope validation')

    with pytest.raises(ValueError, match='frozen'):
        evaluate(tasks()[0], Context())


def test_observed_preflight_smoke_is_short_finite_and_has_no_scoring():
    from lll.prediction_observed_preflight_study import (
        smoke_definition, smoke_recipe, smoke_task)
    r = smoke_recipe()
    task = smoke_task()
    assert r['duration_s'] == 2.
    assert task['limits']['native_calls'] == 637
    assert task['limits']['packet_visits'] == 637
    definition = smoke_definition(Path.cwd(), inputs={'interval': 'data/smoke/interval'})
    assert definition['workers'] == definition['threads'] == 1
    assert definition['maximum_wall_s'] == 600.
    assert definition['tasks'] == [task]
    assert 'scoring' not in definition['inputs']


def test_observed_preflight_launch_checks_disk_before_worker_start(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from lll import ilvis0_control_shards
    from lll import prediction_observed_preflight_study as study
    monkeypatch.setattr('shutil.disk_usage', lambda path: SimpleNamespace(free=34*1024**3))
    monkeypatch.setattr(ilvis0_control_shards, 'launch',
                        lambda *args, **kwargs: pytest.fail('worker started before disk gate'))
    with pytest.raises(ValueError, match='35 GiB'):
        study.launch(tmp_path)


def test_observed_preflight_cli_passes_relative_qualification_paths(monkeypatch, tmp_path):
    from lll import prediction_observed_preflight_study as study
    calls = []
    monkeypatch.setattr(study, 'prepare', lambda root, **kwargs:
                        calls.append(kwargs) or {'prepared': True})
    study.main(['prepare', '--root', str(tmp_path)])
    assert calls == [dict(
        qualification='docs/prediction-observed-law-preflight/qualification-v2/request.json',
        recovery_qualification='docs/prediction-observed-law-preflight/qualification-v2/recovery-request.json')]


def test_observed_preflight_parent_hashes_map_source_validation_name():
    from lll.prediction_observed_preflight_study import parent_hashes_match
    values = {name: {'sha256': name} for name in
              ('interval', 'training', 'context', 'source-validation')}
    bound = {name.replace('-', '_'): name for name in values}
    assert parent_hashes_match(values, bound)
    changed = dict(values, **{'source-validation': {'sha256': 'changed'}})
    assert not parent_hashes_match(changed, bound)


