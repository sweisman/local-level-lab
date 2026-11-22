"""A new source freeze is required for the matching-kernel repetition."""
import pytest


def test_v2_preserves_three_finite_tasks_and_uses_new_identity():
    from lll.esa_fixed_rate_propagation_study_v2 import ID, SMOKE_ID, tasks

    assert ID == 'esa-fixed-rate-propagation-v2-20261114'
    assert SMOKE_ID != ID
    assert [row['identity'] for row in tasks(smoke=False)] == [
        'linear_points', 'left_hold', 'right_hold']
    assert all(row['limits']['native_calls'] == 1 and
               row['limits']['packet_visits'] == 360028*1200
               for row in tasks(smoke=False))


def test_v2_preparation_requires_source_qualification(tmp_path):
    from lll.esa_fixed_rate_propagation_study_v2 import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path, smoke=False)


def test_v2_rejects_changed_task_before_input_read():
    from lll.esa_fixed_rate_propagation_study_v2 import evaluate, tasks, SCOPE

    class Context:
        manifest = {'scope': SCOPE}
        def input_path(self, key):
            raise AssertionError('changed task opened input')

    altered = dict(tasks(smoke=False)[0])
    altered['payload'] = dict(altered['payload'], profile=True)
    with pytest.raises(ValueError, match='unchanged matching-kernel'):
        evaluate(altered, Context())
