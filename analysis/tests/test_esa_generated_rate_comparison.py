"""Generated rate comparison preserves increments, periods and the prefix."""

import io

import numpy as np
import pytest


def _archive(*, bad_period=False, later_amplitude=0.):
    data = io.BytesIO()
    dt = np.full(270000, 1/300)
    if bad_period:
        dt[12] = 0
    theta = np.column_stack((dt*2, dt*3, dt*4))
    dv = np.column_stack((dt*5, dt*6, dt*7))
    theta[180000:] += later_amplitude
    dv[180000:] += later_amplitude
    np.savez(data, theta=theta, dv=dv, dt=dt, times=np.arange(900.))
    return data.getvalue()


def test_generated_rate_summary_uses_earlier_increment_over_actual_period():
    from lll.esa_generated_rate_comparison import generated_rate_summary

    result = generated_rate_summary(_archive())
    assert result['points'] == 180000
    assert result['mean_native_units'] == pytest.approx([2, 3, 4, 5, 6, 7])
    assert [row['stride'] for row in result['contrasts']] == [1, 3, 30, 300]
    assert all(max(row['rms_native_units']) < 1e-8
        for row in result['contrasts'])


def test_generated_rate_summary_rejects_nonpositive_period():
    from lll.esa_generated_rate_comparison import generated_rate_summary

    with pytest.raises(ValueError, match='finite generated'):
        generated_rate_summary(_archive(bad_period=True))


def test_generated_rate_summary_does_not_score_later_samples():
    from lll.esa_generated_rate_comparison import generated_rate_summary

    baseline = generated_rate_summary(_archive())
    changed = generated_rate_summary(_archive(later_amplitude=100.))
    assert changed == baseline
