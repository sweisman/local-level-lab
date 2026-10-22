# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


@pytest.fixture(scope='module')
def backend(tmp_path_factory):
    from lll.ilvis0_clock_path_packets import load_backend
    return load_backend(tmp_path_factory.mktemp('clock-path'))[0]


def fixture():
    from lll.ilvis0_path_jets import Jet3 as J
    config=dict(initial_c=[0.,0.,1000.],initial_v=[200.,0.,0.],initial_r=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],
        limits=[1.]*27,model=2,profile=False,gravity=8.,radius=6378137.)
    return config,[[0.,0.,0.]]*4,[[0.,0.,-.8]]*4,[.1]*4,[J.constant(0)]*27


def test_rounded_endpoint_overshoot_is_integrated_without_clipping(backend):
    args=fixture();time=.1+.1+.1
    answer=backend.predict_branch(*args,time=time,packet_index=2,maximum_packets=4)
    assert answer.fraction.exact[0][1]>1
    lo,hi=answer.coordinates[0].exact[0]
    assert lo<=200*F(time)/6378137<=hi
    report=answer.report()
    assert report['partial_fraction_guard']=='nonnegative to native upper guard'
    assert report['state']['endpoint_encoding']=='outward binary64'
    assert 'dyadic_bits' not in report['state']
    assert not report['clock_partition_verified']


def test_one_sided_boundary_formula_requires_an_explicit_request(backend):
    args=fixture();time=.1+.1+.1
    with pytest.raises(ValueError):backend.predict_branch(*args,time=time,packet_index=3)
    right=backend.predict_branch(*args,time=time,packet_index=3,allow_one_sided=True)
    assert right.report()['one_sided_branch_requested']
    assert right.fraction.exact[0][0]<=0<=right.fraction.exact[0][1]
    expected=200*3*F(.1)/6378137
    lo,hi=right.coordinates[0].exact[0];assert lo<=expected<=hi


def test_wrong_packet_ownership_is_not_accepted_just_because_the_fraction_is_close(backend):
    import math
    args=fixture();time=math.nextafter(.1+.1+.1,math.inf)
    with pytest.raises(ValueError):backend.predict_branch(*args,time=time,packet_index=2)
    valid=backend.predict_branch(*args,time=time,packet_index=3)
    assert valid.packet_index==3
    with pytest.raises(ValueError):backend.predict_branch(*args,time=.8,packet_index=3)


def test_supported_smooth_path_keeps_previous_values(backend,tmp_path):
    from lll.ilvis0_compiled_path_packets import load_backend
    old,_=load_backend(tmp_path)
    args=fixture()
    previous=old.predict_branch(*args,time=.25,packet_index=2)
    current=backend.predict_branch(*args,time=.25,packet_index=2)
    assert [v.exact for v in previous.coordinates]==[v.exact for v in current.coordinates]


def test_successor_metadata_keeps_individual_scientific_limits(tmp_path):
    from lll.ilvis0_clock_path_packets import load_backend
    _,metadata=load_backend(tmp_path)
    assert len(metadata['sources'])==4
    assert not metadata['full_history_qualified'] and not metadata['clock_partition_verified']
    assert metadata['native_fraction_guard_supported']
