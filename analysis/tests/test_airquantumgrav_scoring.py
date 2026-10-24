# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import math

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_scoring') is not None,'common receiver scoring missing'
    return importlib.import_module('lll.airquantumgrav_scoring')


def test_common_receiver_chart_preserves_height_and_wraps_longitude():
    gps=np.array([[0.,math.pi-1e-7,1000.],[0.,0.,1000.]])
    predicted=np.array([[0.,-math.pi+1e-7,1010.],[0.,0.,990.]])
    errors=library().receiver_errors(predicted,gps)
    assert errors[0,0]==0 and errors[0,2]==10 and errors[1,2]==-10
    assert errors[0,1]==pytest.approx(2e-7*(6378137.+1000.),abs=1e-8)
    assert errors[1,0]==errors[1,1]==0


def test_prediction_accuracy_requires_height_and_preserves_inadequacy():
    errors=np.array([[0.,0.,0.],[0.,0.,0.],[.1,.2,100.],[.1,.2,200.]])
    sections=library().sections(errors,2)
    assert sections['training']['accuracy']['passed']
    assert not sections['prediction']['accuracy']['passed']
    assert sections['prediction']['horizontal_rms_m']<1
    assert sections['prediction']['maximum_absolute_up_m']==200


@pytest.mark.parametrize('fault',['shape','nonfinite','pole','height','split'])
def test_unsupported_scoring_fails_without_discarding_bad_epochs(fault):
    gps=np.array([[0.,0.,1000.],[0.,0.,1000.]]);predicted=gps.copy()
    if fault=='shape':predicted=predicted[:1]
    elif fault=='nonfinite':predicted[0,0]=np.nan
    elif fault=='pole':gps[0,0]=math.pi/2
    elif fault=='height':gps[0,2]=-6378137.
    if fault=='split':
        with pytest.raises(ValueError):library().sections(np.zeros((2,3)),2)
    else:
        with pytest.raises(ValueError):library().receiver_errors(predicted,gps)
