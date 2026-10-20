# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import airquantumgrav_intervals as adapter


def row(dt=.004):
    return dict(gps_time_s=1000.,dt_s=dt,acceleration_mps2=[1.,-2.,-9.8],angular_rate_rads=[-.1,.2,-.3],temperature_c=30.)


def test_actual_interval_preserves_original_rates_and_signs():
    original=row();result=adapter.construct(original,hypothesis=adapter.HYPOTHESIS)
    np.testing.assert_array_equal(result['angle_increment_rad'],np.array(original['angular_rate_rads'])*.004)
    np.testing.assert_array_equal(result['velocity_increment_mps'],np.array(original['acceleration_mps2'])*.004)
    assert result['source_record']==original and result['constructed_not_logged_increments']
    assert result['independent_interval_interpretation_verified'] is False


@pytest.mark.parametrize('dt,reason',[(None,'no_preceding_interval'),(.006,'unsupported_gap')])
def test_unsupported_support_has_no_constructed_science_increment(dt,reason):
    result=adapter.construct(row(dt),hypothesis=adapter.HYPOTHESIS)
    assert not result['supported'] and result['reason']==reason
    assert result['angle_increment_rad'] is None


@pytest.mark.parametrize('dt',[0.,-.001,float('nan')])
def test_invalid_time_is_rejected(dt):
    with pytest.raises(ValueError):adapter.construct(row(dt),hypothesis=adapter.HYPOTHESIS)


def test_unknown_sampling_phase_is_not_inferred():
    with pytest.raises(ValueError):adapter.construct(row(),hypothesis='instrument-reported-increment')


def test_linear_rate_quadrature_error_is_explicit():
    # Independent continuous truth: integral of a+b*t over [0,dt].
    dt=.004;a=np.array([.1,-.2,.3]);b=np.array([.7,.8,-.9])
    original=row(dt);original['angular_rate_rads']=(a+b*dt).tolist()
    result=adapter.construct(original,hypothesis=adapter.HYPOTHESIS)
    exact=a*dt+b*dt**2/2
    np.testing.assert_allclose(result['angle_increment_rad']-exact,b*dt**2/2,atol=1e-19)
