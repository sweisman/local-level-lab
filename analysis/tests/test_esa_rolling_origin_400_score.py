"""Earlier-origin receiver scores require all 120 held-out positions."""

import numpy as np
import pytest


def test_rolling_raw_score_uses_complete_neu_receiver_difference():
    from lll.esa_rolling_origin_400_score import score_raw

    receiver=np.tile([0.5,0.1,1000.],(120,1))
    predicted=receiver.copy()
    predicted[:,2]+=2.
    result=score_raw(predicted,receiver)
    assert result['epochs']==120
    assert result['metrics']['horizontal_rms_m']==0.
    assert result['metrics']['vertical_rms_m']==pytest.approx(2.)
    assert np.allclose(np.asarray(result['neu_errors_m'])[:,2],2.)


def test_rolling_raw_score_rejects_incomplete_or_nonfinite_future():
    from lll.esa_rolling_origin_400_score import score_raw

    receiver=np.tile([0.5,0.1,1000.],(120,1))
    with pytest.raises(ValueError,match='120 complete'):
        score_raw(receiver[:119],receiver[:119])
    damaged=receiver.copy();damaged[0,0]=float('nan')
    with pytest.raises(ValueError,match='120 complete'):
        score_raw(damaged,receiver)
