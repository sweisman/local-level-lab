# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
import pytest

from test_ilvis0_declared_training_rows import fixture


def example():
    training,reports=fixture();region=training['region']
    region.update(lower=[-2.]*78,upper=[2.]*78)
    binding=dict(source_id='increments',reference_binding='clock-frame-processing-basis',
        normalized_center=region['center'][:27],lower=[-2.]*27,upper=[2.]*27)
    training['source_binding']=deepcopy(binding)
    for report in reports:report.update(deepcopy(binding))
    return training,reports,binding


def test_signed_projection_matches_exact_rows_with_uncancelled_remainders():
    from lll.ilvis0_declared_training_rows import projected_training_rows
    training,reports,binding=example();weights=[[1.,0.,0.,-1.,0.,0.],[.1,.2,.3,.4,.5,.6]]
    noise=[.05,.2]
    result=projected_training_rows(training,reports,weights=weights,observation_allowance_m=noise,source_binding=binding)
    assert result['parameter_count']==78 and result['physical_parameter_count']==27 and result['new_rows']==4
    assert all(len(row)==78 for row in result['design'])
    for i,w in enumerate(weights):
        exact=[sum((F(a)*F(training['region']['design'][j][k]) for j,a in enumerate(w)),F(0)) for k in range(51)]
        shift=sum((a*F(c) for a,c in zip(exact,training['region']['center'])),F(0))
        delta=F(0);radius=F(noise[i])
        for j,a in enumerate(w):
            epoch,axis=divmod(j,3);scale=F(training['region']['coordinate_scale'][axis])
            delta+=F(a)*(F(training['observations'][epoch][axis])-F(training['nominal'][epoch][axis]))*scale
            radius+=abs(F(a))*(F(reports[epoch]['unshared_remainder'][axis])*scale+F(.00001))
        rounding=sum((abs(F(result['design'][i][k])-a)*2 for k,a in enumerate(exact)),F(0))
        assert F(result['upper'][i])>=shift+delta+radius+rounding
        assert -F(result['upper'][i+2])<=shift+delta-radius-rounding
        assert result['design'][i+2]==[-a for a in result['design'][i]]
    # Equal unknown remainder signs cannot be assumed to cancel in a difference.
    assert result['unshared_radius_m'][0]>=.4
    assert not result['future_observations_used'] and not result['error_law_qualified']


def test_unit_rows_reproduce_old_coordinate_rows_and_keep_all_columns():
    from lll.ilvis0_declared_training_rows import projected_training_rows,training_rows
    training,reports,binding=example();weights=[[float(i==j) for i in range(6)] for j in range(6)]
    old=training_rows(training,reports,observation_allowance_m=[[.01]*3]*2)
    result=projected_training_rows(training,reports,weights=weights,observation_allowance_m=[.01]*6,source_binding=binding)
    assert result['design']==old['design'] and result['upper']==old['upper']


def test_source_box_must_cover_current_physical_region_and_center():
    from lll.ilvis0_declared_training_rows import projected_training_rows
    for key in ('lower','center'):
        training,reports,binding=example()
        training['region'][key][0]=-3. if key=='lower' else .4
        with pytest.raises(ValueError):projected_training_rows(training,reports,
            weights=[[1.,0.,0.,-1.,0.,0.]],observation_allowance_m=[.01],source_binding=binding)


def test_unlifted_source_keeps_51_columns_and_lifted_source_keeps_78():
    from lll.ilvis0_declared_training_rows import projected_training_rows
    training,reports,binding=example();arguments=dict(weights=[[1.,0.,0.,-1.,0.,0.]],
        observation_allowance_m=[.01],source_binding=binding)
    full=projected_training_rows(training,reports,**arguments)
    for key in ('center','lower','upper'):training['region'][key]=training['region'][key][:51]
    training['region']['parameter_count']=51
    base=projected_training_rows(training,reports,**arguments)
    assert base['parameter_count']==51 and all(len(r)==51 for r in base['design'])
    assert base['design']==[r[:51] for r in full['design']] and base['upper']==full['upper']


def test_full_training_cadence_is_not_limited_to_old_short_interface():
    from lll.ilvis0_declared_training_rows import projected_training_rows
    training,reports,binding=example();n=289
    pattern=deepcopy(training);template=deepcopy(reports);region=training['region']
    training['times_s']=[float(i+1) for i in range(n)];reports=[]
    for key in ('nominal','observations','jacobian'):training[key]=[deepcopy(pattern[key][i%2]) for i in range(n)]
    region['design']=[deepcopy(pattern['region']['design'][3*(i%2)+j]) for i in range(n) for j in range(3)]
    for i,t in enumerate(training['times_s']):
        report=deepcopy(template[i%2]);report['time_s']=t;reports.append(report)
    weights=[[0.]*(3*n)];weights[0][0]=1.;weights[0][-1]=-1.
    result=projected_training_rows(training,reports,weights=weights,observation_allowance_m=[.01],source_binding=binding)
    assert result['new_rows']==2 and result['parameter_count']==78


@pytest.mark.parametrize('change',['source','reference','center','basis','bounds','time','noise','weights'])
def test_projected_rows_reject_incompatible_sources_and_shapes(change):
    from lll.ilvis0_declared_training_rows import projected_training_rows
    training,reports,binding=example();weights=[[1.,0.,0.,-1.,0.,0.]];noise=[.01]
    if change=='source':reports[0]['source_id']='other'
    elif change=='reference':reports[1]['reference_binding']='other'
    elif change=='center':reports[1]['normalized_center'][0]+=.1
    elif change=='basis':reports[1]['transform_coefficients'][0][0]+=.1
    elif change=='bounds':training['region']['upper']=[]
    elif change=='time':reports[1]['time_s']+=1.
    elif change=='noise':noise=[-.1]
    else:weights=[[1.]]
    with pytest.raises(ValueError):projected_training_rows(training,reports,weights=weights,
        observation_allowance_m=noise,source_binding=binding)
