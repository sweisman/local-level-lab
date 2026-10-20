# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll.ilvis0_source_norm_preflight import body_bound,point_oracle
from lll.ilvis0_transform_native import make_reference
from test_ilvis0_native_box_bounds import configuration


def fixture():
    config=configuration();dt=np.full(13,.005);theta=np.tile([1e-5,-2e-5,3e-6],(13,1));dv=np.tile([0.,0.,-.04905],(13,1))
    case=dict(configuration=config,dt=dt.tolist(),theta=theta.tolist(),dv=dv.tolist())
    lo=np.full(27,-.2);hi=np.full(27,.5);center=np.full(27,.1)
    reference=make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    return case,reference,lo,hi


def test_frozen_body_prefix_covers_independent_calibration_and_clock_corners():
    case,reference,lo,hi=fixture();bound,visits=body_bound(case,reference,lo,hi,.04)
    assert 0<visits<=13
    for point in (lo,hi,(lo+hi)/2):
        a,b,used=point_oracle(case,point,.04)
        assert used<=13 and np.all(np.isfinite(a))
        assert np.all(abs(b-bound.center)<=bound.change+1e-12)


def test_prefix_rejects_extrapolation_beyond_original_packets():
    case,reference,lo,hi=fixture()
    with pytest.raises(ValueError,match='support'):body_bound(case,reference,lo,hi,1.)
