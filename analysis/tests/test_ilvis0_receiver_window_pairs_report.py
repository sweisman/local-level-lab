"""Saved-only paired-window publication arithmetic."""

import pytest

from lll.ilvis0_receiver_window_pairs_report import summarize


def _record():
    return dict(pair_id='pair', left_task='left', right_task='right',
                matched_epochs=100, targets=2, both_accept=1, both_reject=0,
                disagree=1, same_width_when_both_accept=1,
                vertical_velocity_difference_median_mps=0.,
                vertical_velocity_difference_mad_mps=.01,
                vertical_velocity_difference_rms_mps=.02,
                target_details=[dict(target_gps_s=1., left_half_window_s=5.,
                                     right_half_window_s=5.,
                                     left_reasons=[None]*3,
                                     right_reasons=[None]*3),
                                dict(target_gps_s=11., left_half_window_s=5.,
                                     right_half_window_s=None,
                                     left_reasons=[None]*3,
                                     right_reasons=['vertical_rate_span']*3)],
                interpolated_measurements=False,
                imu_observations_used=False,
                fused_navigation_used=False,
                earth_model_fits=0,
                scientific_decision='abstain')


def test_paired_report_counts_differences_without_model_claim():
    rows, targets, total = summarize([_record()])
    assert len(rows) == 1
    assert len(targets) == 2
    assert total['disagree'] == 1
    assert total['both_accept'] == 1
    assert total['earth_model_fits'] == 0


def test_paired_report_rejects_inconsistent_target_count():
    bad = _record()
    bad['targets'] = 3
    with pytest.raises(ValueError, match='target'):
        summarize([bad])
