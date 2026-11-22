"""Printed GNSS covariances and earlier-only matching remain distinct evidence."""

import math

import numpy as np
import pytest


def test_covariance_layout_and_non_psd_detection():
    from lll.esa_gnss_covariance_audit import covariance_matrix, audit_training

    matrix = covariance_matrix([4.0, 9.0, 16.0, 1.0, 2.0, 3.0])
    assert np.array_equal(matrix, [[4.0, 1.0, 2.0],
                                   [1.0, 9.0, 3.0],
                                   [2.0, 3.0, 16.0]])
    rows = []
    for t in range(30):
        rows.append(dict(time_s=float(t), latitude_deg=0.0,
            longitude_deg=0.0, height_m=100.0,
            north_mps=math.sin(t/10), east_mps=0.0, up_mps=0.0,
            position_variance_m2=[1.0, 1.0, 1.0],
            position_cross_covariance_m2=[0.0, 0.0, 0.0],
            velocity_covariance_export=[0.04, 0.04, 0.04, 0.0, 0.0, 0.0]))
    report = audit_training(rows)
    assert report['position_negative_eigenvalue_epochs'] == 0
    assert report['velocity_negative_eigenvalue_epochs'] == 0
    assert report['position_diagonal_root_median'] == pytest.approx([1, 1, 1])
    assert report['velocity_diagonal_root_median'] == pytest.approx([.2, .2, .2])
    assert report['contrast_lag_correlations']['north']['1'] > .9
    rows[0]['velocity_covariance_export'][3] = 1.0
    assert audit_training(rows)['velocity_negative_eigenvalue_epochs'] == 1


def test_matcher_stops_before_future_and_rejects_changed_record():
    from lll.esa_gnss_covariance_audit import match_training

    def row(t):
        return dict(time_s=float(t), sequence=t, gps_week=1,
                    latitude_deg=60.0, longitude_deg=10.0,
                    height_m=100.0, north_mps=70.0,
                    east_mps=5.0, up_mps=0.0,
                    position_variance_m2=[1, 1, 1],
                    position_cross_covariance_m2=[0, 0, 0],
                    velocity_covariance_export=[1, 1, 1, 0, 0, 0])

    sealed = [row(2), row(3)]
    def source():
        yield row(1)
        yield row(2)
        yield row(3)
        raise AssertionError('future row was decoded')
    assert [x['sequence'] for x in match_training(source(), sealed)] == [2, 3]
    changed = [row(2), row(3)]
    changed[0]['north_mps'] = 71.0
    with pytest.raises(ValueError, match='sealed training'):
        match_training(source(), changed)
