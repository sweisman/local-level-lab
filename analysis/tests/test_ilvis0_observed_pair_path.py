"""The complete-vector connection has six exact finite tasks."""

from lll import ilvis0_observed_pair_path as study


def _layouts():
    return [dict(segment_id=study.NORTH,native_packets=48880,
                 receiver_epochs=244,training_epochs=162),
            dict(segment_id=study.SOUTH,native_packets=110879,
                 receiver_epochs=555,training_epochs=370)]


def test_six_joint_quarter_points_and_exact_caps():
    grid=study.tasks(_layouts())
    assert len(grid)==6
    assert len({task['identity'] for task in grid})==6
    assert sum(task['limits']['native_calls'] for task in grid)==12
    assert sum(task['limits']['packet_visits'] for task in grid)==220247055
    assert {task['payload']['quarter'] for task in grid}=={1,2,3}
    assert all(task['payload']['origin']=='inner' for task in grid)


def test_changed_fraction_is_rejected_before_input_access():
    class Context:
        manifest={'scope':study.SCOPE}
        def input_path(self,*_):raise AssertionError('input accessed first')
    task=study.tasks(_layouts())[0]
    task['payload']['quarter']=4
    try:study.evaluate(task,Context())
    except ValueError as error:
        assert 'exact selected complete-vector path' in str(error)
    else:raise AssertionError('changed task accepted')
