"""Receiver-only development windows preserve order and covariance meaning."""

import pytest


def rows(n=161):
    return [dict(sequence=i,time_s=float(i),gps_week=2269,
        latitude_deg=55.+i*1e-5,longitude_deg=0.,height_m=1000.,
        north_mps=1.,east_mps=0.,up_mps=0.,
        position_variance_m2=[.01,.04,.09],
        position_cross_covariance_m2=[0.,0.,0.],
        velocity_covariance_export=[.01,.04,.09,0.,0.,0.])
        for i in range(n)]


def test_eight_fixed_windows_use_every_report_once():
    from lll.esa_full_receiver_consistency import windows
    groups=windows(rows())
    assert len(groups)==8
    assert [len(x) for x in groups]==[21]+[20]*7
    assert [r['sequence'] for group in groups for r in group]==list(range(161))


def test_short_or_reversed_input_is_rejected():
    from lll.esa_full_receiver_consistency import windows
    with pytest.raises(ValueError):windows(rows(80))
    bad=rows();bad[10]['time_s']=bad[9]['time_s']
    with pytest.raises(ValueError):windows(bad)


def test_receiver_summary_keeps_internal_consistency_distinct_from_accuracy():
    from lll.esa_full_receiver_consistency import summarize
    result=summarize(rows())
    assert result['reports']==161
    assert len(result['windows'])==8
    assert all(x['position_negative_eigenvalue_epochs']==0 for x in result['windows'])
    assert all(x['internal_contrast_rms_mps'][0]>=0 for x in result['windows'])
    assert all(x['position_sd_median_m']==[.1,.2,.3] for x in result['windows'])
    assert result['empirical_position_coverage_calibrated'] is False
    assert result['uses_imu'] is False
