# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full-input compiled packet adapter controls using generated data only."""
from fractions import Fraction as F
import numpy as np
import pytest


@pytest.fixture(scope='module')
def backend(tmp_path_factory):
    from lll.ilvis0_compiled_path_packets import load_backend
    return load_backend(tmp_path_factory.mktemp('compiled-path-packets'))[0]


def inputs(model,profile):
    from lll.ilvis0_path_jets import Jet3 as J
    config=dict(initial_c=[-.7,.4,1400.],initial_v=[190.,60.,-1.],
        initial_r=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],limits=[.001]*27,
        model=model,profile=profile,gravity=9.8,radius=6378137.)
    config['limits'][25]=.0001;config['limits'][26]=1.
    theta=np.array([[1.e-6,-2.e-6,3.e-6],[2.e-6,1.e-6,-3.e-6]])
    dv=np.array([[.001,-.002,-.049],[-.001,.003,-.049]])
    dt=np.array([.005,.005]);s=J.affine(0,[1,1],[0,0])
    p=[s*(i+1)/100 for i in range(27)]
    return config,theta,dv,dt,p


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
def test_complete_packet_path_matches_high_precision_reference(backend,monkeypatch,model,profile):
    from lll import ilvis0_path_motion as motion,ilvis0_path_packets as packets
    args=inputs(model,profile)
    # Full-input agreement for all six candidates; the cheaper disc case also
    # checks history accumulation. Multi-packet native controls test all six.
    count=2 if model==2 else 1
    start=sum(map(float,args[3][:count-1]));query=start+float(args[3][count-1])*.5
    q=lambda v:v.rounded(binary_bits=192)
    monkeypatch.setattr(motion,'_q',q);monkeypatch.setattr(packets,'_q',q)
    reference=packets.predict_branch(*args,time=query,packet_index=count-1,maximum_packets=count)
    actual=backend.predict_branch(*args,time=query,packet_index=count-1,maximum_packets=count)
    assert actual.packet_index==count-1 and actual.start==start
    for a,b in zip(actual.coordinates,reference.coordinates):
        for (lo,hi),(left,right) in zip(a.exact,b.exact):
            assert lo<=left<=right<=hi
    assert not actual.report()['clock_partition_verified']


def test_clock_and_down_lever_have_independently_known_signs(backend):
    from lll.ilvis0_path_jets import Jet3 as J
    config,theta,dv,dt,p=inputs(2,False)
    config.update(initial_c=[0.,0.,1000.],initial_v=[200.,0.,0.],limits=[1.]*27,gravity=0.0)
    # Physical positive gravity is required; cancel exactly with the increments.
    config['gravity']=8.;dv=np.array([[0.,0.,-8.*dt[0]]]);theta=np.zeros((1,3));dt=dt[:1]
    p=[J.constant(0)]*27;p[25]=J.affine(0,[1,1],[0,0]);p[8]=J.constant(.1);p[23]=J.constant(.1)
    answer=backend.predict_branch(config,theta,dv,dt,p,time=.0025,packet_index=0,maximum_packets=1)
    lo,hi=answer.coordinates[0].exact[1];assert lo<=F(200,6378137)<=hi
    lo,hi=answer.coordinates[2].exact[0];assert lo<=F(1000)-2*F(.1)<=hi


def test_common_nonzero_path_domain_contains_its_fixed_interior_points(backend):
    from lll.ilvis0_path_jets import Jet3 as J
    config,theta,dv,dt,_=inputs(0,True)
    parameters=[J.affine(0,[F(i+1,100),F(i+1,100)],[F(-1,100),F(1,100)]) for i in range(27)]
    bound=backend.predict_branch(config,theta,dv,dt,parameters,time=.0075,packet_index=1,maximum_packets=2)
    for value in (F(-1,100),F(0),F(1,100)):
        point=[J.affine(0,[F(i+1,100),F(i+1,100)],[value,value]) for i in range(27)]
        actual=backend.predict_branch(config,theta,dv,dt,point,time=.0075,packet_index=1,maximum_packets=2)
        for a,b in zip(bound.coordinates,actual.coordinates):
            for (lo,hi),(left,right) in zip(a.exact,b.exact):
                assert lo<=left<=right<=hi


def test_unsupported_inputs_limits_and_clock_branches_are_rejected(backend):
    from lll.ilvis0_path_jets import Jet3 as J
    args=list(inputs(0,False))
    for kwargs in (dict(time=.02,packet_index=1),dict(time=.0075,packet_index=1,maximum_packets=1),
            dict(time=.0075,packet_index=True),dict(time=.0075,packet_index=1,maximum_seconds=0)):
        with pytest.raises(ValueError):backend.predict_branch(*args,**kwargs)
    p=list(args[-1]);p[0]=J.constant(2)
    with pytest.raises(ValueError):backend.predict_branch(*args[:4],p,time=.0075,packet_index=1)
    bad=args.copy();bad[3]=np.array([.005,-.005])
    with pytest.raises(ValueError):backend.predict_branch(*bad,time=.0075,packet_index=1)
    bad=args.copy();bad[1]=np.array([[float('nan'),0,0],[0,0,0]])
    with pytest.raises(ValueError):backend.predict_branch(*bad,time=.0075,packet_index=1)
    bad=args.copy();bad[0]=dict(args[0],gravity=F(49,5))
    with pytest.raises(ValueError,match='binary64'):backend.predict_branch(*bad,time=.0075,packet_index=1)


def test_packet_backend_metadata_has_complete_compiled_closure(tmp_path):
    from lll.ilvis0_compiled_path_packets import load_backend
    _,metadata=load_backend(tmp_path)
    assert len(metadata['sources'])==4 and metadata['cooperative_time_limit']
    assert not metadata['full_history_qualified'] and not metadata['clock_partition_verified']
