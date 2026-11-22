"""Retrospective horizon scores retain the original error vectors."""

import numpy as np
import pytest


def test_saved_prefix_errors_use_original_signed_axes():
    from lll.esa_saved_horizon_report import prefix_errors
    values=np.array([[3.,4.,-2.],[0.,12.,6.]])
    result=prefix_errors(values,(1,2))
    assert result['1']['horizontal_rms_m']==5.
    assert result['2']['horizontal_rms_m']==np.sqrt(84.5)
    assert result['2']['vertical_rms_m']==np.sqrt(20.)
    assert result['2']['final_vertical_error_m']==6.


def test_saved_prefix_errors_require_complete_ordered_support():
    from lll.esa_saved_horizon_report import prefix_errors
    with pytest.raises(ValueError,match='finite north/east/up'):
        prefix_errors([[1.,2.,float('nan')]],(1,))
    with pytest.raises(ValueError,match='ordered horizons'):
        prefix_errors([[1.,2.,3.]],(2,))


def test_saved_horizon_matches_historical_conditional_score_key():
    from lll.esa_saved_horizon_report import matching_full_score
    old={'laws':{'increment':{'score':{
        'conditional':{'horizontal_rms_m':3.25}}}}}
    assert matching_full_score(old,'increment','conditioned')==3.25
