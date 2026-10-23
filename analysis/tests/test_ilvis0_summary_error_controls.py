# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_weights_use_time_only_and_never_include_later_epochs():
    from lll.ilvis0_summary_error_controls import fixed_weights
    times=np.array([2.,10.,30.,180.,290.,292.,438.])
    weights,ids=fixed_weights(times,training_end_s=290.)
    assert weights.shape==(12,21) and len(set(ids))==12
    assert np.all(weights[:,15:]==0.) and not weights.flags.writeable
    for degree in range(4):
        for axis in range(3):
            row=weights[3*degree+axis]
            assert np.isclose(np.linalg.norm(row),1.)
            assert np.all(row.reshape(-1,3)[:,[j for j in range(3) if j!=axis]]==0.)


@pytest.mark.parametrize('times,end',[([2.],2.),([2.,1.],2.),([2.,3.],1.),([2.,float('nan')],3.)])
def test_invalid_summary_epochs_fail_closed(times,end):
    from lll.ilvis0_summary_error_controls import fixed_weights
    with pytest.raises(ValueError):fixed_weights(times,training_end_s=end)


def test_four_laws_and_full_error_family_are_frozen_before_calculations():
    from lll.ilvis0_summary_error_controls import recipe
    r=recipe()
    assert r['correlation_s']==[10,300] and r['gyro_psd_choices']==[1e-12,1e-10]
    assert r['times_s']==list(map(float,range(2,291)))+list(map(float,range(292,439)))
    assert r['scalar_family_count']==453 and r['identities']==4
    assert r['native_calls']==r['optimizer_starts']==r['original_reads']==0


def test_summary_errors_bind_one_family_to_full_parent_law():
    from lll.ilvis0_summary_error_controls import calculate
    r=calculate([2.,10.,30.,180.,290.,292.,438.],correlation_s=10,gyro_psd=1e-12)
    assert r['passed'] and r['scalar_family_count']==18
    assert len(r['allowances']['row_ids'])==18
    assert r['allowances']['covariance_id']==r['covariance_id']
    assert r['allowances']['projection_id']==r['family_projection_id']
    assert r['allowances']['tail_certificate']['coordinate_count']==18
    assert r['certified_variance_above_operator'] and not r['uncertainty_qualified']
    assert r['future_observations_used'] is False and r['scientific_decision']=='abstain'


def test_dense_lineage_accepts_the_actual_numerical_error_family():
    from lll.ilvis0_summary_error_controls import calculate,fixed_weights,recipe
    from lll.ilvis0_prediction_lineage import _family
    times=recipe()['times_s'];earlier=[t for t in times if t<=290.]
    result=calculate(times,correlation_s=10,gyro_psd=1e-12)
    weights=fixed_weights(times,training_end_s=290.)[0][:,:3*len(earlier)].tolist()
    family_id,premise_id=_family(result,weights,earlier)
    assert family_id==result['family_projection_id'] and premise_id!=family_id
    assert result['allowances']['coordinate_count']==453
