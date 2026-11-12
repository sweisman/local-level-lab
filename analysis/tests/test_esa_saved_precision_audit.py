"""Saved ESA prediction errors must join the same receiver epochs exactly."""
import math

import pytest


def _fixture():
    rows=[dict(time_s=10.+i,latitude_deg=0.,longitude_deg=0.,height_m=100.,
               position_variance_m2=[1.,4.,9.]) for i in range(3)]
    scores=dict(times_s=[0.,1.,2.],
                receiver_coordinates=[[0.,0.,100.]]*3,
                errors_neu_m=[[0.,0.,0.],[3.,4.,6.],[4.,2.,3.]])
    return scores,rows


def test_saved_esa_precision_summary_uses_only_later_matched_epochs():
    from lll.esa_saved_precision_audit import summarize
    scores,rows=_fixture()
    result=summarize(scores,rows,training_epochs=1)
    assert result['prediction_epochs']==2
    assert result['north']['error_rms_m']==pytest.approx(math.sqrt(12.5))
    assert result['north']['median_receiver_sigma_m']==1.
    assert result['north']['median_abs_error_over_sigma']==3.5
    assert result['east']['median_abs_error_over_sigma']==1.5
    assert result['height']['median_abs_error_over_sigma']==1.5
    assert result['scientific_decision']=='abstain'


def test_saved_esa_precision_rejects_changed_time_or_receiver_position():
    from lll.esa_saved_precision_audit import summarize
    scores,rows=_fixture()
    rows[2]['time_s']+=.1
    with pytest.raises(ValueError,match='time'):
        summarize(scores,rows,training_epochs=1)
    rows[2]['time_s']-=.1
    rows[2]['height_m']+=.01
    with pytest.raises(ValueError,match='coordinate'):
        summarize(scores,rows,training_epochs=1)
