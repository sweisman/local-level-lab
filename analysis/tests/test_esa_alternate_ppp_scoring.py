# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common-epoch PPP rescoring and two-stage ordering controls."""

import math

import numpy as np
import pytest

from lll.esa_alternate_ppp_scoring import rank_setting, score_errors


def test_other_minus_reference_is_subtracted_from_prediction_error():
    base=np.array([[1.,0.,0.],[2.,0.,0.],[9.,0.,0.]])
    difference=np.array([[.5,0.,0.],[1.,0.,0.],[-50.,0.,0.]])
    result=score_errors(base,difference,[0,1])
    assert result['matched_epochs']==2
    assert math.isclose(result['rms_neu_m'][0],math.sqrt((.5**2+1.**2)/2))


def test_shape_precedes_conditional_field_ordering():
    base=lambda cost:dict(total_rms_m=cost,accuracy=True)
    scores=dict(sphere_rotating=base(1.),sphere_still=base(2.),flat_still=base(4.))
    result=rank_setting(scores)
    assert result['shape_lower_error_family']=='globe'
    assert result['field_lower_error_model']=='specified_field'
    scores['flat_still']=base(.5)
    assert rank_setting(scores)['field_lower_error_model'] is None


def test_missing_candidate_and_nonfinite_score_rejected():
    with pytest.raises(ValueError,match='three complete'):
        rank_setting({'sphere_rotating':dict(total_rms_m=1.)})
    with pytest.raises(ValueError,match='finite nonnegative'):
        rank_setting({name:dict(total_rms_m=float('nan')) for name in
                      ('sphere_rotating','sphere_still','flat_still')})
