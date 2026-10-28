# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import pytest


@pytest.mark.parametrize('cap,calls,visits',[(8,23642,14910394),(64,23698,119117714),(171,23805,318228129)])
def test_shared_saved_allowance_preserves_original_formula_and_new_eight_sweep_cap(cap,calls,visits):
    from lll.saved_point_runtime import allowance
    from lll.compensated_prediction_release import case_recipe
    assert allowance(case_recipe(281474977010693),cap)==dict(native_calls=calls,packet_visits=visits,
                                                           bound_calls=0,bound_steps=0)


@pytest.mark.parametrize('cap',[True,0,-1,201,1.5])
def test_shared_saved_allowance_rejects_unbounded_or_invalid_caps(cap):
    from lll.saved_point_runtime import allowance
    with pytest.raises(ValueError):allowance({},cap)


def test_shared_capture_binding_keeps_provider_identity_and_original_module_unchanged():
    from lll.saved_point_runtime import bind_capture
    from lll import stopping_consistency_study as old
    from lll.studies.artifacts import digest
    raw=Path(old.__file__).read_bytes()
    bound,proof=bind_capture(lambda *a,**k:None,raw=raw,expected_sha256=digest(raw),provider_sha256='a'*64)
    assert proof['substitutions']==1 and bound is not old.calculate_point
    assert bound.__globals__ is not old.calculate_point.__globals__


@pytest.mark.parametrize('extra',[False,True])
def test_saved_capture_preserves_default_and_exposes_only_explicit_physical_callback(monkeypatch,extra):
    import numpy as np
    from types import SimpleNamespace
    from lll import stopping_consistency_study as old,airquantumgrav_noisy_inputs as noisy
    from lll import ilvis0_native_error_training as errors,generated_prediction as generated
    from lll import ilvis0_solver_position as position
    from lll.studies import protocols
    names=['time_offset']+['p'+str(i) for i in range(26)]
    problem=SimpleNamespace(bounds=SimpleNamespace(active=names),dt=[.005],gps_times=[.5,1.5],
        residual_tangent=lambda u,m:(np.array([1.]),np.zeros((1,27)),0))
    record=dict(payload=dict(case=dict(law='point',model='sphere_rotating',profile=True)),
        fit=dict(normalized_parameters=[0.]*27,active_parameters=names,residual_sum_squares=1.,converged=False),
        artifacts={},artifact_sha256={'fit.json':'a'*64})
    r=dict(input_laws=['point'],noise_by_law={'point':{}},covariance_anchor_policy='normalized-midpoint-v1')
    monkeypatch.setattr(noisy,'construct',lambda *a,**k:dict(training_rows=[{'height_m':10.}],dt=[.005],times=[.5,1.5]))
    monkeypatch.setattr(noisy,'error_law',lambda value:None)
    monkeypatch.setattr(errors,'ErrorTrainingFactory',lambda **kw:object())
    def binding(raw,**kw):
        def bound(*a,**k):return kw['provider'](problem,'sphere_rotating',stopping='near_zero')
        return bound,{'fixture':True}
    monkeypatch.setattr(protocols,'bind_function',binding)
    monkeypatch.setattr(generated,'calculate',lambda *a,**kw:kw['train_and_forecast']())
    seen=[];charges=[]
    def physical(p,delta):
        assert p is problem
        seen.append('physical');return np.ones((1,3))
    monkeypatch.setattr(position,'physical_residual_step',physical)
    def probe(evaluate,point,**options):
        assert ('physical_step' in options) is extra
        if extra:assert options['physical_step'](np.array([0.])).shape==(1,3)
        evaluate(point,fresh=True)
        return dict(stopping_probe={'passed':None},evaluations=1)
    monkeypatch.setattr(__import__('lll.stopping_consistency',fromlist=['probe']),'probe',probe)
    kwargs={} if not extra else dict(probe_options=lambda p:dict(physical_step=lambda d:physical(p,d)))
    result=old.calculate_point(record,r,kernel_factory=None,noise_kernel=None,
        reserve=lambda **kw:charges.append(kw),reserve_construction=lambda **kw:None,
        reserve_evaluation=lambda **kw:None,save=lambda *a:None,check_continue=lambda:None,
        protocol_source=b'fixture',protocol_sha256='b'*64,**kwargs)
    assert result['diagnostic_complete'] and result['nonlinear_fit_starts']==0
    assert charges==[dict(native_calls=1,packet_visits=2)]
    assert seen==(['physical'] if extra else [])
