"""The finite timing probe stays tied to the saved case and declared grid."""
import math

import pytest


def test_timing_grid_brackets_packet_boundary_without_duplicating_points():
    from lll.bounded_noisy_timing_probe import timing_grid
    # Two receiver queries are 40 ns after their corresponding packet ends.
    times = [0.10000004, 0.20000004]
    ends = [0.1, 0.2, 0.3]
    grid = timing_grid(times, ends, center_offset_s=0.,
                       full_time_step_s=-.0009, time_limit_s=.01)
    assert len(grid) == 8
    assert len({item['label'] for item in grid}) == 8
    assert grid[0]['label'] == 'saved_point'
    assert grid[0]['changed_packet_epochs'] == 0
    assert grid[1]['changed_packet_epochs'] == 2
    assert grid[2]['changed_packet_epochs'] == 0
    assert grid[-1]['label'] == 'full_timing_component'
    assert grid[-1]['physical_offset_s'] == pytest.approx(-.0009)
    assert all(math.isfinite(item['physical_offset_s']) for item in grid)


def test_timing_grid_rejects_unmatched_or_out_of_support_queries():
    from lll.bounded_noisy_timing_probe import timing_grid
    with pytest.raises(ValueError):
        timing_grid([.10000004, .202], [.1, .2, .3], 0., -.0009, .01)
    with pytest.raises(ValueError):
        timing_grid([.1, .2], [.1, .2], 0., -.0009, .01)


def test_failed_case_preflight_matches_sealed_inputs_without_native_work():
    from lll.bounded_noisy_timing_probe import preflight
    # The closed parent is local evidence and is absent from a source checkout.
    # A missing parent must never count as a passing source-bound qualification.
    try:
        preflight('.')
    except ValueError as error:
        if str(error) == 'closed study required':
            pytest.skip('historical closed parent is not in the source checkout')
        if str(error) == 'frozen generated source mismatch':
            return
        raise
    pytest.fail('current source unexpectedly matched the historical freeze')
