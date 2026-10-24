# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent arithmetic examples for descriptive rate contrasts."""
import math
import pytest


def test_rate_variation_import_is_metadata_only():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,'-c',
        "import sys; import lll.rate_variation; assert 'numpy' not in sys.modules and 'scipy' not in sys.modules"],
        text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_nonuniform_rate_contrasts_remove_linear_motion_and_keep_all_axes():
    import numpy as np
    from lll.rate_variation import contrasts
    times=np.array([0.,1.,3.,4.,7.,8.])
    slopes=np.array([1.,-2.,.5,4.,0.,3.])
    values=times[:,None]*slopes+np.arange(6.)
    result=contrasts(times,values,stride=1,maximum_points=6)
    np.testing.assert_allclose(result['values'],0.,atol=2e-15)
    assert result['count']==2 and result['discarded_points']==0
    assert result['separation_s']==[3.,4.]
    assert result['sampling_assumption']=='independent_equal_variance_point_errors_for_normalization_only'


def test_rate_contrast_normalization_matches_independent_three_point_arithmetic():
    import numpy as np
    from lll.rate_variation import contrasts
    times=[0.,1.,3.,4.,7.,8.,9.]
    values=np.arange(42.).reshape(7,6)**2
    result=contrasts(times,values,stride=1,maximum_points=7)
    expected=[]
    for first,middle,last in ((0,1,2),(3,4,5)):
        a=(times[middle]-times[first])/(times[last]-times[first])
        row=[(values[middle,j]-(1-a)*values[first,j]-a*values[last,j])/
             math.sqrt(1+(1-a)**2+a*a) for j in range(6)]
        expected.append(row)
    np.testing.assert_allclose(result['values'],expected,rtol=2e-15,atol=2e-14)
    assert result['discarded_points']==1


def test_rate_contrasts_use_disjoint_triples_at_each_stride():
    import numpy as np
    from lll.rate_variation import contrasts
    values=np.zeros((24,6));values[6]=1.
    result=contrasts(np.arange(24.),values,stride=2,maximum_points=24)
    assert result['indices'].tolist()==[[0,2,4],[6,8,10],[12,14,16],[18,20,22]]
    assert np.count_nonzero(np.any(result['values'],axis=1))==1


@pytest.mark.parametrize('failure',['order','gap','nonfinite','shape','limit','stride','capacity'])
def test_rate_variation_rejects_unsupported_inputs(failure):
    import numpy as np
    from lll.rate_variation import contrasts
    t=np.arange(12.)/300;v=np.ones((12,6));options=dict(stride=1,maximum_points=12,maximum_gap_s=.005)
    if failure=='order':t[4]=t[3]
    elif failure=='gap':t[4:]+=.1
    elif failure=='nonfinite':v[2,0]=np.nan
    elif failure=='shape':v=v[:,:5]
    elif failure=='limit':options['maximum_points']=11
    elif failure=='stride':options['stride']=True
    elif failure=='capacity':options['stride']=6
    with pytest.raises(ValueError):contrasts(t,v,**options)


def test_rate_variation_summary_has_no_automatic_noise_estimate_or_decision():
    import numpy as np
    from lll.rate_variation import summarize
    times=np.arange(900.)/300;values=np.sin(times[:,None]*np.arange(1.,7.))
    original=values.copy();result=summarize(times,values,strides=(1,3,30),maximum_points=900,maximum_gap_s=.005)
    assert result['points']==900 and len(result['contrasts'])==3
    assert result['isolated_sensor_noise_estimated'] is False
    assert result['error_distribution_established'] is False
    assert result['scientific_decision']=='abstain'
    assert result['fitted_parameters']==result['interpolated_points']==0
    assert result['total_contrasts']==300+100+10
    assert len(result['contrasts'][0]['rms_native_units'])==6
    assert result['nominal_period_white_noise_conversion_applied'] is False
    assert np.array_equal(values,original)


def test_time_extension_cannot_enter_explicit_training_only_selection():
    import numpy as np
    from lll.rate_variation import training_prefix
    t=np.arange(12.);v=np.ones((12,6))
    before=training_prefix(t,v,last_training_time_s=7.,maximum_points=12)
    v[8:]=1e20
    after=training_prefix(t,v,last_training_time_s=7.,maximum_points=12)
    assert before[0].tolist()==list(range(8))
    assert np.array_equal(before[1],after[1])
    assert not np.shares_memory(before[1],v)
