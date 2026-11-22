"""The fixed-endpoint timing check has an exact selected and finite task grid."""

from lll import ilvis0_observed_fixed_timing as study


def _layouts():
    return [dict(segment_id=study.NORTH, native_packets=48880,
                 receiver_epochs=244, training_epochs=162),
            dict(segment_id=study.SOUTH, native_packets=110879,
                 receiver_epochs=555, training_epochs=370)]


def test_fixed_timing_grid_uses_saved_maximum_pairs_and_matched_controls():
    tasks = study.tasks(_layouts())
    assert len(tasks) == 8
    assert len({task['identity'] for task in tasks}) == 8
    assert all(task['payload']['model'] == 'sphere_rotating' for task in tasks)
    assert all(task['payload']['clock'] == 'header_elapsed' for task in tasks)
    assert all(task['limits']['native_calls'] == 10 for task in tasks)
    assert sum(task['limits']['packet_visits'] for task in tasks) == 1468313700
    assert set(task['identity'] for task in tasks) == study.EXPECTED_IDENTITIES
    middle = dict(segment_id=study.parent.base.SEGMENTS[1],
                  native_packets=88478, receiver_epochs=443,
                  training_epochs=295)
    original = {task['identity']:task['payload'] for task in
                study.parent.base.tasks([_layouts()[0],middle,_layouts()[1]])}
    assert all(original[task['identity']] == task['payload'] for task in tasks)


def test_changed_task_is_rejected_before_training_input_access():
    class Context:
        manifest = {'scope': study.SCOPE}

        def input_path(self, *_):
            raise AssertionError('training input accessed before task check')

    task = study.tasks(_layouts())[0]
    task['payload']['start'] = 99
    try:
        study.evaluate(task, Context())
    except ValueError as error:
        assert 'exact selected timing endpoint' in str(error)
    else:
        raise AssertionError('changed task was accepted')
