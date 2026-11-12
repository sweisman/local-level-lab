# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known trends, training-only support and changed-role rejection."""

import pytest


def _epochs(*, later_shift=0.):
    rows=[]
    for index in range(240):
        t=float(index)
        offset=later_shift if index>=160 else 0.
        rows.append(dict(epoch=index,
                         role='training' if index<160 else 'prediction',
                         time_s=t,
                         north_direct_error_m=2.+.1*t+offset,
                         east_direct_error_m=-3.-.2*t+offset,
                         up_direct_error_m=4.+.05*t+offset))
    return rows


def test_exact_earlier_trend_predicts_later_without_using_later_for_fit():
    from lll.prediction_drift_control import evaluate

    result=evaluate(_epochs())
    assert result['selected_training_epochs']==120
    assert result['prediction_epochs']==80
    assert result['scores']['linear']['three_dimensional_rms_m']<1e-12
    assert result['scores']['constant']['horizontal_rms_m']>1
    assert result['later_values_used_for_fitting'] is False


def test_changed_later_values_cannot_change_earlier_correction():
    from lll.prediction_drift_control import evaluate

    baseline=evaluate(_epochs())
    altered=evaluate(_epochs(later_shift=50.))
    assert altered['correction']==baseline['correction']
    assert altered['scores']['linear']['horizontal_rms_m']>baseline[
        'scores']['linear']['horizontal_rms_m']


def test_unsupported_training_window_or_role_change_rejected():
    from lll.prediction_drift_control import evaluate

    rows=_epochs()
    with pytest.raises(ValueError,match='frozen earlier-only'):
        evaluate(rows,training_window_s=60.)
    rows[170]['role']='training'
    with pytest.raises(ValueError,match='later observations'):
        evaluate(rows)
