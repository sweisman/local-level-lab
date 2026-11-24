import pytest

from lll.esa_apron_imu_ranges import clock_offsets, motion_summary


def _clock_line(second, offset):
    return f'> 2023 07 06 10 57 {second:010.7f} 0 25 {offset}\n'.encode()


def test_clock_offsets_require_every_epoch_and_reject_steps():
    first = _clock_line(0, '0.000001')
    assert clock_offsets(first + _clock_line(.5, '0.000002')) == [1e-6, 2e-6]
    with pytest.raises(ValueError):
        clock_offsets(first + _clock_line(.5, '0.000004'))
    with pytest.raises(ValueError):
        clock_offsets(first + _clock_line(.5, 'nan'))


def _rates(indices):
    return [dict(gps_time_s=i/10, angular_rate_rads=[i/10, 0, 0],
                 gap_above_1p5_nominal_periods=False) for i in indices]


def test_motion_bins_exclude_the_end_epoch_without_a_partial_bin():
    summary = motion_summary(_rates(range(21)), start=0, end=2, rate_hz=10)
    assert summary['selected_samples'] == 20
    assert [row['count'] for row in summary['complete_bin_means']] == [10, 10]
    assert summary['complete_bin_means'][0]['mean_xyz_deg_per_hour'][0] == pytest.approx(92819.16281119337)


def test_motion_rejects_a_gap_or_incomplete_boundary_bin():
    with pytest.raises(ValueError):
        motion_summary(_rates([*range(4), *range(5, 21)]), start=0, end=2, rate_hz=10)
    with pytest.raises(ValueError):
        motion_summary(_rates(range(2, 21)), start=0, end=2, rate_hz=10)


def test_inertial_intake_uses_the_runner_bound_journal(tmp_path):
    from lll import esa_apron_imu_ranges as study
    from lll import ilvis0_control_shards as runner

    source = tmp_path/'project'
    entry = source/'analysis/tests/ilvis0_control_shards.py'
    entry.parent.mkdir(parents=True)
    entry.write_text('# fixture runner\n')
    (source/'adapter.py').write_text('# fixture adapter\n')
    (source/'input').write_text('fixture data\n')
    output = tmp_path/'study'
    runner.prepare(output, project_root=source, tasks=[study.TASK],
                   sources=['adapter.py', 'analysis/tests/ilvis0_control_shards.py'],
                   inputs={'air': 'input'}, adapter='adapter.py', workers=1, threads=1,
                   maximum_wall_s=60, environment=runner.runtime_environment())
    context = runner.TaskContext(output, 0, study.TASK['identity'])
    study.reserve_setup(context)
    assert runner._counts(context.journal, context.task) == dict(
        native_calls=0, packet_visits=0, bound_calls=1, bound_steps=75_001)
