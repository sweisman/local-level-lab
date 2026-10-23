# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
import pytest


def test_saved_feasible_points_set_lower_spreads_not_outer_bounds():
    from test_ilvis0_truth_probes import _witness_fixture
    from lll.ilvis0_witness_publication import point_spreads
    problem,first,_=_witness_fixture();first=deepcopy(first);first['prediction'][-1]=[0.,0.,0.]
    second=deepcopy(first);second['point'][0]=.001;second['prediction'][-1]=[31.,-22.,60.]
    bad=deepcopy(first);bad['prediction'][0]=[10.,10.,10.]
    result=point_spreads(problem,{'first':first,'second':second,'rejected':bad})
    assert result['feasible']==['first','second'] and result['rejected']==['rejected']
    assert F(result['axes'][0]['separation_lower_exact'])>20
    assert result['axes'][0]['pair']==['first','second']
    assert result['outer_bound_qualified'] is False
    assert result['observational_coverage_qualified'] is False


def test_spreads_keep_different_axis_extremes_and_refuse_different_sources():
    from test_ilvis0_truth_probes import _witness_fixture
    from lll.ilvis0_witness_publication import point_spreads
    problem,first,_=_witness_fixture();first=deepcopy(first);first['prediction'][-1]=[0.,0.,0.]
    north=deepcopy(first);north['prediction'][-1]=[30.,0.,0.]
    east=deepcopy(first);east['prediction'][-1]=[0.,40.,0.]
    result=point_spreads(problem,{'first':first,'north':north,'east':east})
    assert result['axes'][0]['pair']==['first','north']
    assert result['axes'][1]['pair']==['first','east']
    north['binding']=dict(north['binding'],case_sha256='f'*64)
    with pytest.raises(ValueError):point_spreads(problem,{'first':first,'changed':north})


def test_calibration_trace_separates_local_terms_from_nonlinear_difference():
    from test_ilvis0_truth_probes import _witness_fixture
    from lll.ilvis0_witness_publication import calibration_trace
    problem,first,_=_witness_fixture();first=deepcopy(first);first['prediction'][-1]=[0.,0.,0.]
    origin=deepcopy(first);origin['jacobian']=[[[0.]*27 for _ in range(3)] for _ in range(6)]
    origin['jacobian'][-1][0][0]=1000.;origin['jacobian'][-1][0][1]=-990.
    second=deepcopy(first);second['point']=[.001,.001]+[0.]*25;second['prediction'][-1]=[.02,0.,0.]
    value=calibration_trace(problem,origin,first,second,[2.]*27)
    assert F(value['coordinates'][0]['physical_change_exact'])==2*F(.001)
    assert F(value['linear_change_exact'][0])==10*F(.001)
    assert F(value['nonlinear_remainder_exact'][0])==F(.02)-10*F(.001)
    assert value['causal_decomposition'] is False and len(value['coordinates'])==27


def test_calibration_trace_uses_actual_profiled_removal_mapping():
    from test_ilvis0_truth_probes import _witness_fixture
    from lll.ilvis0_witness_publication import calibration_trace
    problem,first,_=_witness_fixture();first=deepcopy(first)
    first['binding']=dict(first['binding'],profile=True);problem['binding']=first['binding']
    origin=deepcopy(first);origin['jacobian']=[[[0.]*27 for _ in range(3)] for _ in range(6)]
    second=deepcopy(first);second['point']=[0.]*26+[.5]
    value=calibration_trace(problem,origin,first,second,[1.]*27)
    assert F(value['coordinates'][26]['physical_change_exact'])==F(1,4)
