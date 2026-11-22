"""The fixed-vector aircraft sensitivity grid is finite and preselected."""

from lll import ilvis0_observed_calibration_swap as study


def _layouts():
    return [dict(segment_id=study.NORTH,native_packets=48880,
                 receiver_epochs=244,training_epochs=162),
            dict(segment_id=study.SOUTH,native_packets=110879,
                 receiver_epochs=555,training_epochs=370)]


def test_exact_two_pairs_bidirectional_six_variant_grid_and_charges():
    grid=study.tasks(_layouts())
    assert len(grid)==24
    assert len({row['identity'] for row in grid})==24
    assert sum(row['limits']['native_calls'] for row in grid)==48
    assert sum(row['limits']['packet_visits'] for row in grid)==880988220
    assert {row['payload']['variant'] for row in grid}==set(study.VARIANTS)
    assert {row['payload']['segment_id'] for row in grid}=={study.NORTH,study.SOUTH}
    assert all(row['payload']['origin']=='inner' for row in grid)


def test_changed_vector_task_rejected_before_input_access():
    class Context:
        manifest={'scope':study.SCOPE}
        def input_path(self,*_):raise AssertionError('input accessed first')
    task=study.tasks(_layouts())[0]
    task['payload']['variant']='unlisted'
    try:study.evaluate(task,Context())
    except ValueError as error:
        assert 'exact selected calibration swap' in str(error)
    else:raise AssertionError('changed task accepted')
