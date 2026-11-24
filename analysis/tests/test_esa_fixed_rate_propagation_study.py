"""Freeze the no-refit rate comparison's identities and input boundaries."""
import pytest


def test_rate_propagation_tasks_have_three_finite_no_fit_calls():
    from lll.esa_fixed_rate_propagation_study import tasks

    rows = tasks(smoke=False)
    assert [row['identity'] for row in rows] == [
        'linear_points', 'left_hold', 'right_hold']
    assert all(row['native_kind'] == 'tangent' for row in rows)
    assert all(row['payload'] == dict(method=row['identity'],
                                     model='sphere_rotating', profile=False)
               for row in rows)
    assert all(row['limits'] == dict(
        native_calls=1, packet_visits=360028*1200,
        bound_calls=0, bound_steps=0) for row in rows)


def test_rate_propagation_preparation_requires_qualification(tmp_path, monkeypatch):
    from lll.compute_budget import environment
    from lll.esa_fixed_rate_propagation_study import prepare

    for key, value in environment(threads=1).items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path, smoke=False)


def test_rate_propagation_rejects_changed_task_before_input_read():
    from lll.esa_fixed_rate_propagation_study import evaluate, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE}
        def input_path(self, key):
            raise AssertionError('changed task opened a sealed input')

    row = dict(tasks(smoke=False)[0])
    row['payload'] = dict(row['payload'], model='flat_still')
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(row, Context())
