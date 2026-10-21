# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math

import pytest

from lll.ilvis0_declared_training_rows import training_rows


def fixture():
    times=[1.,2.5]; scale=[2.,3.,4.]; center=[.05*(i%4-1) for i in range(27)]+[0.]*51
    reports=[]; jac=[]; design=[]
    for epoch in range(2):
        blocks=[[[((i+axis+epoch)%7-3)/16 for i in range(n)] for axis in range(3)]
                for n in (27,6,9,9)]
        jac.append(blocks[0])
        reports.append(dict(time_s=times[epoch],center=[.1,.2,10.+epoch],
            previous_coefficients=blocks[1],acceleration_coefficients=blocks[2],
            transform_coefficients=blocks[3],unshared_remainder=[.1,.2,.3]))
        design.extend([[scale[axis]*a for block in blocks for a in block[axis]]
                       for axis in range(3)])
    training=dict(times_s=times,nominal=[list(r['center']) for r in reports],jacobian=jac,
        observations=[[.125,.18,10.1],[.11,.21,10.9]],region=dict(parameter_count=78,
        center=center,design=design,coordinate_scale=scale,arithmetic_allowance=.00001))
    return training,reports


def test_each_row_matches_independent_rational_construction():
    training,reports=fixture(); noise=[[.03,.04,.05],[.06,.07,.08]]
    result=training_rows(training,reports,observation_allowance_m=noise)
    assert result['parameter_count']==78 and result['new_rows']==12
    for epoch in range(2):
        for axis in range(3):
            index=3*epoch+axis; row=training['region']['design'][index]+[0.]*27
            assert result['design'][index]==row
            assert result['design'][index+6]==[-x for x in row]
            shift=sum((F(a)*F(b) for a,b in zip(row,training['region']['center'])),F(0))
            delta=(F(training['observations'][epoch][axis])-F(reports[epoch]['center'][axis]))*F(training['region']['coordinate_scale'][axis])
            radius=F(reports[epoch]['unshared_remainder'][axis])*F(training['region']['coordinate_scale'][axis])+F(noise[epoch][axis])+F(.00001)
            high=F(result['upper'][index]); low=-F(result['upper'][index+6])
            assert low<=shift+delta-radius<=shift+delta+radius<=high
            assert F(math.nextafter(float(high),-math.inf))<shift+delta+radius
            assert F(math.nextafter(float(low),math.inf))>shift+delta-radius


def test_explicit_one_mm_reproduces_frozen_short_builder_rows():
    from lll.ilvis0_direct_interface import training_rows as old
    training,reports=fixture(); expected=old(training,reports)
    result=training_rows(training,reports,observation_allowance_m=[[.001]*3]*2)
    for key in ('design','upper','parameter_count','new_rows','arithmetic_allowance_m'):
        assert result[key]==expected[key]


def test_larger_noise_only_relaxes_its_own_two_inequalities():
    training,reports=fixture(); noise=[[.001]*3 for _ in range(2)]
    before=training_rows(training,reports,observation_allowance_m=noise)
    noise[1][2]=.4
    after=training_rows(training,reports,observation_allowance_m=noise)
    assert before['design']==after['design']
    assert [i for i,(a,b) in enumerate(zip(before['upper'],after['upper'])) if a!=b]==[5,11]
    assert all(a<=b for a,b in zip(before['upper'],after['upper']))
    noise[1][2]=1.
    assert after['observation_allowance_m'][1][2]==.4


@pytest.mark.parametrize('noise',[.001,[[.001]*3],[[.001]*3]*3,
    [[.001]*3,[.001,-.1,.001]],[[.001]*3,[.001,float('nan'),.001]]])
def test_no_default_broadcast_negative_or_nonfinite_allowance(noise):
    training,reports=fixture()
    with pytest.raises(ValueError):training_rows(training,reports,observation_allowance_m=noise)


@pytest.mark.parametrize('change',['column','center','time','remainder','arithmetic','observation'])
def test_incomplete_or_changed_inputs_are_rejected(change):
    training,reports=fixture()
    if change=='column':training['region']['design'][0]=training['region']['design'][0][:-1]
    elif change=='center':reports[0]['center'][1]+=.1
    elif change=='time':reports[0]['time_s']+=.1
    elif change=='remainder':reports[0]['unshared_remainder'][1]=-.1
    elif change=='arithmetic':training['region']['arithmetic_allowance']=-.1
    else:training['observations'][0][0]=float('nan')
    with pytest.raises(ValueError):training_rows(training,reports,observation_allowance_m=[[.001]*3]*2)


def test_missing_allowances_cannot_silently_use_short_history_default():
    training,reports=fixture()
    with pytest.raises(TypeError):training_rows(training,reports)
