"""The ESA rate refit has six finite, training-only task identities."""
import pytest


def test_rate_refit_tasks_cover_three_methods_and_both_laws():
    from lll.esa_rate_refit_study import tasks

    rows = tasks(smoke=False)
    assert len(rows) == 6
    assert {row['identity'] for row in rows} == {
        f'{method}-{law}' for method in
        ('linear_points', 'left_hold', 'right_hold')
        for law in ('increment', 'point')}
    assert all(row['native_kind'] == 'tangent' and
               row['limits'] == dict(native_calls=700000,
                                     packet_visits=45000000000,
                                     bound_calls=0, bound_steps=0)
               for row in rows)


def test_rate_refit_requires_qualification_before_observed_preparation(tmp_path, monkeypatch):
    from lll.compute_budget import environment
    from lll.esa_rate_refit_study import prepare

    for key, value in environment(workers=3, threads=1).items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path, smoke=False)


def test_rate_refit_rejects_changed_task_before_input_read():
    from lll.esa_rate_refit_study import evaluate, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE}
        def input_path(self, key):
            raise AssertionError('changed task opened a sealed input')

    altered = dict(tasks(smoke=False)[0])
    altered['payload'] = dict(altered['payload'], model='flat_still')
    with pytest.raises(ValueError, match='unchanged finite'):
        evaluate(altered, Context())
