# SPDX-License-Identifier: AGPL-3.0-or-later
import copy

import numpy as np
import pytest

import ilvis0_prediction_controls as controls


@pytest.mark.parametrize('name',controls.CASES)
def test_generated_inputs_are_reproducible_with_separate_streams(name):
    control=controls.fixture(name)
    a=controls.realization(control,0);b=controls.realization(control,0)
    for key in ('calibration','training','future','training_design'):
        np.testing.assert_array_equal(a[key],b[key])
    assert not np.array_equal(a['training'],controls.realization(control,1)['training'])


@pytest.mark.parametrize('name',controls.CASES)
def test_envelope_uses_training_and_calibration_without_future_observations(name):
    control=controls.fixture(name);sample=controls.realization(control,0)
    inputs={k:sample[k] for k in ('training','calibration','training_design')}
    result=controls.envelope(control,**inputs)
    assert result['supported'] and result['scientific_decision']=='abstain'
    assert len(result['lower'])==3*control['nf']
    assert result['nominal_failure_probability_bound']<=.05
    changed=copy.deepcopy(sample);changed['future'][:]=1e50
    changed['covariance_truth']='not-an-input'
    again=controls.envelope(control,**{k:changed[k] for k in inputs})
    np.testing.assert_array_equal(result['lower'],again['lower'])
    np.testing.assert_array_equal(result['upper'],again['upper'])


def test_nonlinear_truth_respects_declared_global_remainder_bounds():
    control=controls.fixture('bounded_nonlinear')
    for member in control['family'].values():
        assert np.linalg.norm(member['operator'].whiten(control['training_remainder_shape']))<=.1+1e-14
        assert np.linalg.norm(member['calibration'].whiten(control['calibration_remainder']))<=.03+1e-14
    assert np.all(abs(control['theta'])<=1.)


def test_covariance_union_keeps_both_members_without_truth_selection():
    control=controls.fixture('finite_covariance_union');sample=controls.realization(control,0)
    result=controls.envelope(control,**{k:sample[k] for k in ('training','calibration','training_design')})
    assert result['covariance_ids']==['a','b']
