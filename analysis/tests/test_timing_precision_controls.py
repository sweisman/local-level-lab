# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent small controls, without fitting or recorded observations."""
import math

import numpy as np
import pytest


def test_reference_separates_packet_derivatives_from_continuous_motion():
    from lll.timing_precision_controls import turning_reference
    a,w,d=2.,1.6,.25
    reference=turning_reference(a,w,d)
    assert reference['left'][0]==pytest.approx(a*d*math.cos(w*d/2)-a*w*d*d*math.sin(w*d/2)/4)
    assert reference['right'][0]==pytest.approx(a*d*math.cos(w*d/2))
    assert reference['continuous'][0]==pytest.approx(a*math.sin(w*d)/w)
    assert abs(reference['left'][0]-reference['right'][0])>1e-3


def test_controls_are_fixed_and_reject_unknown_identity():
    from lll.timing_precision_controls import cases,fixture
    assert len(cases())==7 and len(set(cases()))==7
    with pytest.raises(ValueError,match='identity'):fixture('extra')


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    from lll.timing_precision_controls import load
    directory=tmp_path_factory.mktemp('timing-native');charged=[]
    kernel,meta=load(directory,reserve_build=lambda:charged.append(1))
    _,cached=load(directory,reserve_build=lambda:charged.append(1))
    assert charged==[1] and meta==cached and meta['internal_mantissa_bits']>53
    return kernel


@pytest.mark.parametrize('identity',(
    'vertical-interior','vertical-boundary','vertical-bound-offset',
    'turning-slow','turning-fast','gyro-origin-zero','gyro-origin-one'))
def test_native_control_matches_its_independent_reference(identity,native):
    from lll.timing_precision_controls import calculate
    charged=[]
    result=calculate(identity,kernel=native,reserve=lambda **v:charged.append(v))
    assert result['passed'],result
    assert result['native_evaluations']==len(charged)==7
    assert all(v['native_calls']==1 and v['packet_visits']>0 for v in charged)
    assert result['nonlinear_fit_starts']==result['original_reads']==result['protected_reads']==0
    if identity.startswith('turning'):
        assert result['derivative_branch_gap']>1e-3
        assert result['finite_difference_error_to_right'][-1]<1e-7
    if identity=='gyro-origin-zero':
        assert max(result['finite_difference_relative_error'])<1e-5
    if identity=='gyro-origin-one':
        assert result['finite_difference_relative_error'][-1]>1e-3


def test_native_charge_rejection_prevents_execution():
    from lll.timing_precision_controls import calculate
    def deny(**v):raise RuntimeError('budget exhausted')
    def forbidden(*a,**k):raise AssertionError('uncharged native call')
    with pytest.raises(RuntimeError,match='budget exhausted'):
        calculate('vertical-interior',kernel=forbidden,reserve=deny)


def test_build_charge_rejection_prevents_compilation(tmp_path):
    from lll.timing_precision_controls import load
    def deny():raise RuntimeError('build allowance exhausted')
    with pytest.raises(RuntimeError,match='build allowance exhausted'):
        load(tmp_path,reserve_build=deny)
    assert not list(tmp_path.glob('*.so'))


def test_study_rejects_wrong_scope_before_building():
    from types import SimpleNamespace
    from lll.timing_precision_controls import evaluate
    with pytest.raises(ValueError,match='scope'):
        evaluate(dict(identity='vertical-interior',payload=dict(identity='vertical-interior')),
            SimpleNamespace(manifest=dict(scope='unapproved expansion')))


def test_every_control_retains_full_parameter_vector_and_timing_support():
    from lll.timing_precision_controls import cases,fixture
    for identity in cases():
        f=fixture(identity);p=f['problem']
        assert len(p.bounds.active)==len(f['point'])==26
        assert p.gps_times[-1]+p.bounds.limits['time_offset']<=sum(p.dt)
        assert p.gps_times[0]-p.bounds.limits['time_offset']>=0
