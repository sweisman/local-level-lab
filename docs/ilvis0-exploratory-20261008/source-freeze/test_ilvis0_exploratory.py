# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import numpy as np
import pytest
from lll import ilvis0_exploratory as explore, ilvis0_estimator as estimator
from lll import ilvis0_excitation_controls as controls, ilvis0_gps_sensitivity as sensitivity


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    return explore.load_kernel(tmp_path_factory.mktemp('ilvis0-kernel'))[0]


@pytest.mark.parametrize('model', explore.MODELS)
@pytest.mark.parametrize('removal', [0., .5, 1.])
def test_native_reference_keeps_corrections_and_partial_packets(kernel, model, removal):
    base, _, _ = controls.fixture(2., 'brief_pitch', sensitivity.assumptions()[0])
    kwargs = dict(clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
                  maximum_interval_s=.501, gravity_mps2=9.81, disc_radius_m=6371000.)
    a = explore.ConditionalProblem(base.theta, base.dv, base.dt, base.gps_times, base.gps,
        base.cholesky@base.cholesky.T, base.initial, base.bounds, **kwargs)
    b = explore.ConditionalProblem(base.theta, base.dv, base.dt, base.gps_times, base.gps,
        base.cholesky@base.cholesky.T, base.initial, base.bounds, kernel=kernel, **kwargs)
    point=np.zeros(len(a.bounds.active)); point[-1]=2*removal-1
    for i,name in enumerate(a.bounds.active):
        if name!='earth_removal':point[i]=.1
    # Fixed conventional metre scaling compares candidate predictions, not candidate weights.
    metric=np.array([6371000.,6371000.,1.])
    assert np.max(abs((a.predict(point,model)-b.predict(point,model))*metric))<2e-7


def test_unsubtracted_matches_existing_reference(kernel):
    base, point, _ = controls.fixture(20., 'steady_orientation', sensitivity.assumptions()[0])
    p = explore.ConditionalProblem(base.theta,base.dv,base.dt,base.gps_times,base.gps,
        base.cholesky@base.cholesky.T,base.initial,base.bounds,fit_earth_removal=False,kernel=kernel,
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.501,gravity_mps2=9.81,disc_radius_m=6371000.)
    assert np.max(abs((p.predict(point,'sphere_rotating')-base.predict(point,'sphere_rotating'))*
                       [6371000.,6371000.,1.]))<2e-7


def test_conditional_assumptions_do_not_satisfy_empirical_gate(tmp_path):
    ledger=estimator.StartLedger(tmp_path/'starts.jsonl','a'*64)
    with pytest.raises(ValueError,match='prerequisites'):
        estimator.fit_observed(None,'sphere_rotating',evidence={},ledger=ledger,task='file',maximum_evaluations=200)
    assert not ledger.path.exists()


def test_removal_applies_even_to_still_model(kernel):
    base, _, _ = controls.fixture(20.,'steady_orientation',sensitivity.assumptions()[0])
    p=explore.ConditionalProblem(base.theta,base.dv,base.dt,base.gps_times,base.gps,
        base.cholesky@base.cholesky.T,base.initial,estimator.Bounds({}),kernel=kernel,
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.501,gravity_mps2=9.81,disc_radius_m=6371000.)
    a=p.predict([-1.],'sphere_still');b=p.predict([1.],'sphere_still')
    assert np.max(abs((a-b)*[6371000.,6371000.,1.]))>.01


def test_bounds_reject_invalid_processing():
    bounds=explore.ConditionalBounds({},fit_earth_removal=True)
    assert bounds.decode([-1.])['earth_removal']==0
    assert bounds.decode([1.])['earth_removal']==1
    with pytest.raises(ValueError):bounds.decode([math.nan])
