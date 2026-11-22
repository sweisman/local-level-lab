"""Fixed-window summaries of logged iMAR rates, with no field subtraction."""

import math

import pytest


def row(time, x=0.0, *, gap=False):
    return dict(gps_time_s=time, angular_rate_rads=[x, 0.0, 0.0],
                gap_above_1p5_nominal_periods=gap)


def test_constant_rate_has_zero_allan_deviation():
    from lll.esa_ground_rate_scale import summarize_scales
    records = [row(i / 300, .001) for i in range(900)]
    report = summarize_scales(records, windows={'ground': (0.0, 3.0)},
                              widths=(1,))['ground']['1']
    assert report['complete_bins'] == 3
    assert report['mean_xyz_deg_per_hour'][0] == pytest.approx(
        .001 * 180 / math.pi * 3600)
    assert report['allan_xyz_deg_per_hour'] == pytest.approx([0, 0, 0], abs=1e-8)


def test_step_changes_adjacent_bin_allan_deviation():
    from lll.esa_ground_rate_scale import summarize_scales
    records = [row(i / 300, 0.0 if i < 300 else .001)
               for i in range(600)]
    report = summarize_scales(records, windows={'ground': (0.0, 2.0)},
                              widths=(1,))['ground']['1']
    assert report['complete_bins'] == 2
    assert report['allan_xyz_deg_per_hour'][0] == pytest.approx(
        .001 * 180 / math.pi * 3600 / math.sqrt(2))


def test_incomplete_tail_is_not_used_as_complete_bin():
    from lll.esa_ground_rate_scale import summarize_scales
    records = [row(i / 300) for i in range(645)]
    report = summarize_scales(records, windows={'ground': (0.0, 2.2)},
                              widths=(1,))['ground']['1']
    assert report['complete_bins'] == 2
    assert report['omitted_partial_bins'] == 1


def test_selected_gap_is_rejected_but_gap_between_stops_is_allowed():
    from lll.esa_ground_rate_scale import summarize_scales
    records = [row(i / 300) for i in range(300)]
    records += [row(100.0 + i / 300) for i in range(300)]
    summary = summarize_scales(records, windows={'a': (0.0, 1.0),
                                                   'b': (100.0, 101.0)},
                               widths=(1,))
    assert summary['a']['1']['complete_bins'] == 1
    assert summary['b']['1']['complete_bins'] == 1
    records[2] = row(2 / 300, gap=True)
    with pytest.raises(ValueError, match='gap'):
        summarize_scales(records, windows={'a': (0.0, 1.0)}, widths=(1,))


def test_overlapping_windows_and_invalid_scale_are_rejected():
    from lll.esa_ground_rate_scale import summarize_scales
    with pytest.raises(ValueError, match='overlap'):
        summarize_scales([], windows={'a': (0.0, 2.0), 'b': (1.0, 3.0)})
    with pytest.raises(ValueError, match='width'):
        summarize_scales([], windows={'a': (0.0, 2.0)}, widths=(0,))
