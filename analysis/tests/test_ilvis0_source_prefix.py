# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def source():
    return dict(configuration=dict(initial_r=np.eye(3),limits=np.full(27,.01)),
        theta=np.array([[1,2,-1],[-2,1,3],[2,-3,1],[1,1,-2]],float)/1024,
        dv=np.tile([.001,-.002,-.05],(4,1)),dt=np.array([.004,.006,.005,.007]))


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_source_prefix import load_kernels
    return load_kernels(tmp_path_factory.mktemp('source-prefix'))[0]


def stream(kernels,kind,time):
    from lll.ilvis0_source_prefix import make_stream
    z=np.zeros(27);z[1]=.1;z[9]=-.1;z[15]=.05
    lo=z.copy();hi=z.copy();lo[25]=-.01;hi[25]=.02
    return make_stream(kernels,kind,source(),z,time,lower=lo,upper=hi,
        reference_binding='source-clock-frame',maximum_packets=4)


def compare(a,b):
    assert set(a)==set(b)
    for k in a:
        if isinstance(a[k],np.ndarray):np.testing.assert_array_equal(a[k],b[k],err_msg=k)
        else:assert a[k]==b[k],k


@pytest.mark.parametrize('kind',['reference','interval','point'])
@pytest.mark.parametrize('time',[.012,.015,np.nextafter(.015,-np.inf),np.nextafter(.015,np.inf)])
def test_copied_source_tail_matches_independent_cold_stream_and_parent(kernels,kind,time):
    from lll.ilvis0_source_prefix import fork_stream
    parent=stream(kernels,kind,.021);parent.append();parent.append()
    before=bytes(parent._buffer)
    child=fork_stream(parent,time,reference_binding='source-clock-frame')
    cold=stream(kernels,kind,time);cold.append();cold.append()
    assert child.visits==2 and child.maximum_packets==4
    for _ in range(2):compare(child.append(),cold.append())
    assert bytes(parent._buffer)==before
    expected=stream(kernels,kind,.021);expected.append();expected.append()
    compare(parent.append(),expected.append())
    with pytest.raises(ValueError):child.append()
    parent.close();child.close();cold.close();expected.close()


@pytest.mark.parametrize('kind',['reference','interval','point'])
def test_clipped_history_and_new_query_at_prefix_boundary_cannot_be_forked(kernels,kind):
    from lll.ilvis0_source_prefix import fork_stream
    parent=stream(kernels,kind,.005);parent.append();parent.append()
    with pytest.raises(ValueError):fork_stream(parent,.02,reference_binding='source-clock-frame')
    parent.close()
    parent=stream(kernels,kind,.021);parent.append();parent.append()
    for t in (.01,.009,.0001):
        with pytest.raises(ValueError):fork_stream(parent,t,reference_binding='source-clock-frame')
    parent.close()


def test_source_binding_and_closed_state_are_enforced(kernels):
    from lll.ilvis0_source_prefix import fork_stream
    parent=stream(kernels,'reference',.021)
    with pytest.raises(ValueError):fork_stream(parent,.02,reference_binding='other')
    parent.close()
    with pytest.raises(ValueError):fork_stream(parent,.02,reference_binding='source-clock-frame')


def test_changed_kernel_identity_cannot_reinterpret_saved_state(kernels):
    from dataclasses import replace
    from lll.ilvis0_source_prefix import fork_stream
    parent=stream(kernels,'reference',.021);parent.append()
    parent.kernel=replace(parent.kernel,identity='different-source-or-compiler')
    with pytest.raises(ValueError):fork_stream(parent,.02,reference_binding='source-clock-frame')


def test_contracted_physical_box_may_exclude_the_retained_expansion(kernels):
    from lll.ilvis0_source_prefix import make_stream,fork_stream
    case=source();z=np.zeros(27);lo=np.full(27,.02);hi=np.full(27,.03)
    # The mathematical source encloses the union of its physical box and fixed
    # expansion. Contracting the box must not silently move that expansion.
    s=make_stream(kernels,'interval',case,z,.021,lower=lo,upper=hi,
        reference_binding='contracted',maximum_packets=4)
    s.append();s.append();child=fork_stream(s,.012,reference_binding='contracted')
    assert child.center==tuple(z) and child.lower==tuple(lo) and child.upper==tuple(hi)
    s.close();child.close()


@pytest.mark.parametrize('kind',['reference','interval','point'])
def test_original_cold_kernels_match_copied_values_and_every_column(kernels,kind,tmp_path):
    from lll.ilvis0_source_prefix import fork_stream
    from lll.ilvis0_source_stream import SourceStream,load_stream
    from lll.ilvis0_source_derivative_intervals import Stream as Intervals,load_kernel as interval_kernel
    from lll.ilvis0_source_point_derivatives import Stream as Point,load_kernel as point_kernel
    case=source();z=np.zeros(27);z[1]=.1;z[9]=-.1;z[15]=.05
    lo=z.copy();hi=z.copy();lo[25]=-.01;hi[25]=.02
    if kind=='reference':cold=SourceStream(load_stream(tmp_path)[0],case,z,.012,maximum_packets=4)
    elif kind=='interval':cold=Intervals(interval_kernel(tmp_path)[0],case,z,lo,hi,.012,maximum_packets=4)
    else:cold=Point(point_kernel(tmp_path)[0],case,z,.012,maximum_packets=4)
    parent=stream(kernels,kind,.021);parent.append();parent.append()
    child=fork_stream(parent,.012,reference_binding='source-clock-frame');cold.append();cold.append()
    for _ in range(2):
        a=child.append();b=cold.append();a.pop('state_bytes');b.pop('state_bytes');compare(a,b)
    parent.close();child.close();cold.close()
