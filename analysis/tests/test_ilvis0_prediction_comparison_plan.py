# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy

import pytest


def reference():
    return dict(segment_id='control',training_epochs=292,prediction_epochs=147,
        first_training_time_s=.2,last_training_time_s=291.2,
        first_prediction_time_s=292.2,last_prediction_time_s=438.2)


def api():
    from lll import ilvis0_prediction_comparison_plan as plan
    return plan


def test_exact_matrix_and_inclusive_ceiling():
    p=api().make(reference(),2.7,3.1)
    assert len(p['identities'])==len(set(p['identities']))==12
    assert p['maximum_native_sweeps']==3060
    assert p['maximum_fit_sweeps']==2400 and p['maximum_diagnostic_sweeps']==660
    assert p['maximum_starts']==12 and p['retry_reserve']==0
    assert p['state']=='prepared_not_launchable' and p['observed_allowance_authorized'] is False
    assert p['scientific_decision']=='abstain'


def test_shared_covariances_cover_each_model_and_processing_case():
    p=api().make(reference(),2.7,3.1)
    for name in ('h1_v3_tau10','h1_v3_tau300'):
        rows=[r for r in p['tasks'] if r['covariance']==name]
        assert len(rows)==6 and {r['model'] for r in rows}==set(api().MODELS)
        assert {r['processing_case'] for r in rows}==set(api().CASES)
    assert all(c['calibrated'] is False for c in p['covariances'])
    assert p['estimate_covariance_from_candidate_residuals'] is False


@pytest.mark.parametrize('key,value',[
    ('training_epochs',291),('prediction_epochs',True),
    ('first_prediction_time_s',291.2),('segment_id','')])
def test_invalid_split_rejected(key,value):
    r=deepcopy(reference());r[key]=value
    with pytest.raises(ValueError):api().make(r,2.7,3.1)


@pytest.mark.parametrize('median,slowest',[(0.,3.),(3.,2.),(float('nan'),3.)])
def test_invalid_runtime_basis_rejected(median,slowest):
    with pytest.raises(ValueError):api().make(reference(),median,slowest)


def test_probe_policy_and_cost_preserve_every_allowed_direction():
    p=api().make(reference(),2.7,3.1)
    assert {t['parameters'] for t in p['tasks']}=={26,27}
    assert p['diagnostics']['normalized_step']==.01
    assert p['diagnostics']['remove_bound_columns'] is False
    assert p['diagnostics']['reoptimized_profiles'] is False
    assert p['runtime_estimate']['ceiling_minutes_at_median']>120
    assert p['runtime_estimate']['ceiling_minutes_at_slowest']>p['runtime_estimate']['ceiling_minutes_at_median']
