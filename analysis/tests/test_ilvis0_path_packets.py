# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def configuration():
    return dict(initial_c=[0,0,1000],initial_v=[200,0,0],
        initial_r=[[1,0,0],[0,1,0],[0,0,1]],limits=[1]*27,
        model=2,profile=False,gravity=F(49,5),radius=6000000)


def test_clock_derivative_in_a_supported_packet_matches_straight_motion():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_packets import predict_branch
    p=[J.constant(0)]*27;p[25]=J.affine(0,[1,1],[0,0])
    answer=predict_branch(configuration(),[[0,0,0]],[[0,0,F(-49,1000)]],
        [F(1,200)],p,time=F(1,400),packet_index=0)
    lo,hi=answer.coordinates[0].exact[1]
    assert lo<=F(1,30000)<=hi and hi-lo<F(1,10**20)
    lo,hi=answer.coordinates[0].exact[0]
    assert lo<=F(1,12000000)<=hi
    assert not answer.report()['clock_partition_verified']


def test_entire_prior_history_is_preserved_before_the_partial_packet():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_packets import predict_branch
    p=[J.constant(0)]*27;dt=[F(1,200)]*2
    # Start is the exact value of the native floating cumulative timestamp.
    query=F(float(dt[0]))+F(1,400)
    answer=predict_branch(configuration(),[[0,0,0]]*2,[[0,0,F(-49,1000)]]*2,
        dt,p,time=query,packet_index=1)
    lo,hi=answer.coordinates[0].exact[0]
    assert lo<=F(1,4000000)<=hi and hi-lo<F(1,10**20)


def test_initial_position_and_receiver_lever_arm_keep_down_sign():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_packets import predict_branch
    config=configuration();config['initial_v']=[0,0,0]
    p=[J.constant(0)]*27;p[8]=J.constant(F(1,10));p[23]=J.constant(F(1,10))
    answer=predict_branch(config,[[0,0,0]],[[0,0,F(-49,1000)]],[F(1,200)],p,
        time=F(1,400),packet_index=0)
    lo,hi=answer.coordinates[2].exact[0]
    assert lo<=F(4999,5)<=hi and hi-lo<F(1,10**20)


def test_missing_columns_wrong_branches_and_reversed_periods_are_rejected():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_packets import predict_branch
    p=[J.constant(0)]*27
    args=(configuration(),[[0,0,0]],[[0,0,F(-49,1000)]],[F(1,200)])
    with pytest.raises(ValueError):predict_branch(*args,p[:26],time=0,packet_index=0)
    with pytest.raises(ValueError):predict_branch(*args,p,time=F(1,100),packet_index=0)
    with pytest.raises(ValueError):predict_branch(configuration(),[[0,0,0]],[[0,0,0]],[-1],p,time=0,packet_index=0)
    outside=list(p);outside[0]=J.constant(2)
    with pytest.raises(ValueError):predict_branch(*args,outside,time=0,packet_index=0)
