# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_timing_cells_preserve_closely_spaced_transitions_and_exact_float_coverage():
    from lll.timing_intervals import local_cells
    dt=np.array([.5,.5,.5]);times=np.array([.5,np.nextafter(.5,1.)])
    result=local_cells(dt,times,scale=.01,point=0.)
    assert result['transition_count']==2 and len(result['cells'])==3
    cells=result['cells'];ends=np.cumsum(dt)
    for cell in cells:
        lo,hi,anchor=(cell[k] for k in ('lower','upper','anchor'))
        assert -1<=lo<=anchor<=hi<=1
        # This independently dispatches the original double-precision queries.
        first=np.searchsorted(ends,times+float(np.longdouble(.01)*np.longdouble(lo)),side='left')
        last=np.searchsorted(ends,times+float(np.longdouble(.01)*np.longdouble(hi)),side='left')
        assert np.array_equal(first,last)
    for a,b in zip(cells,cells[1:]):
        assert np.nextafter(a['upper'],np.inf)==b['lower']
    assert any(c['lower']<=0<=c['upper'] for c in cells)


def test_timing_cells_follow_irregular_clock_and_include_original_point():
    from lll.timing_intervals import local_cells
    dt=[.4,.6,.5,.5];times=[.5,1.]
    result=local_cells(dt,times,scale=.1,point=0.)
    assert result['transition_count']==1 and len(result['cells'])==2
    assert any(c['lower']<=0<=c['upper'] for c in result['cells'])
    assert result['window_s']==1e-5 and result['maximum_transitions']==16


def test_timing_cell_partition_retains_a_single_representable_point():
    from lll.timing_intervals import partition
    a=.1;b=float(np.nextafter(a,1.));c=float(np.nextafter(b,1.))
    cells=partition([(a,b),(b,c)],lower=-1.,upper=1.)
    assert cells[1]==dict(lower=b,upper=b,anchor=b,has_representable_interior=False)
    assert len(cells)==3


@pytest.mark.parametrize('change',['dt','times','scale','point','support','overflow'])
def test_timing_geometry_rejects_unsupported_inputs_or_too_many_cells(change):
    from lll.timing_intervals import local_cells
    dt=[.5,.5,.5];times=[.4,.5];scale=.01;point=0.
    if change=='dt':dt[0]=0.
    elif change=='times':times[1]=times[0]
    elif change=='scale':scale=float('nan')
    elif change=='point':point=1.1
    elif change=='support':times[0]=0.
    else:times=[.5+i*1e-7 for i in range(17)]
    with pytest.raises(ValueError):local_cells(dt,times,scale=scale,point=point)


def test_timing_geometry_smooth_cell_uses_nearest_real_dispatch_limits():
    from lll.timing_intervals import local_cells
    result=local_cells([.5]*4,[.7,1.2],scale=.1,point=.2)
    assert result['transition_count']==0 and len(result['cells'])==1
    assert result['cells'][0]['lower']==-1 and result['cells'][0]['upper']==1


def test_local_timing_anchors_sample_each_side_inside_the_local_window():
    from lll.timing_intervals import local_cells
    point=.00001
    result=local_cells([.5,.5,.5],[.5],scale=.01,point=point)
    assert result['anchor_policy']=='midpoint_of_local_cell_intersection'
    for c in result['cells']:
        lo=max(c['lower'],point-.001);hi=min(c['upper'],point+.001)
        expected=lo+(hi-lo)/2
        assert c['anchor']==expected
        assert abs(c['anchor']-point)*.01<=1e-5
    assert result['cells'][0]['anchor']<0<result['cells'][1]['anchor']
    smooth=local_cells([.5]*4,[.7,1.2],scale=.1,point=.2)
    assert abs(smooth['cells'][0]['anchor']-.2)<=1e-16
