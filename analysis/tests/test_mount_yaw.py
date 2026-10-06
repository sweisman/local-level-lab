# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent yaw/sign controls and fail-closed two-path eligibility fixtures."""
import copy
import json

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll import fit,models
from lll.calib import RAD2DPH
from lll.inference import CandidateProblem
from lll.mount_yaw import MountYaw,MOUNT_YAW_POLICY,boundary_keep,compare_paths
from lll.policy import MODEL_PAIRS,eligibility_provenance,scientific_exclusions
from lll.design_envelope import envelope_assumptions


def problem():
    from test_release060 import crab_fixture
    from test_research_candidates import settings
    bins,fwd=crab_fixture(); bins['epoch']=bins['seg']//2
    return CandidateProblem(bins,fwd,lambda _:0.,np.full(3,1.e-5),
        settings(mount_yaw_model='piecewise',mount_yaw_segments=[0,2],design_mode='envelope',pairwise_method='profile'))


def test_piecewise_yaw_is_epoch_local_and_retains_post_segment_offset():
    p=problem(); m=p.mount_yaw; q=np.array([.01,1.e-6,.02,2.e-6])
    yaw=m.B@q; rate=m.D@q
    assert len(m.groups)==2 and m.npar==4
    assert rate[p.bins['seg']==1].max()==0.
    assert rate[p.bins['seg']==3].max()==0.
    assert np.ptp(yaw[p.bins['seg']==1])==0.
    assert yaw[p.bins['seg']==2].min()>=.02
    keep=boundary_keep(p.bins,[0,2])
    assert np.flatnonzero(~keep).tolist()==[0,24]
    with pytest.raises(ValueError,match='unavailable'): MountYaw(p.bins,[99])
    with pytest.raises(ValueError,match='unique integer'): MountYaw(p.bins,[0,0])


@pytest.mark.parametrize('rate_dph',[0.,3.,-3.])
def test_prediction_matches_independent_passive_imu_rotation(rate_dph):
    p=problem(); z=np.zeros(p.npar); z[:3]=models.EXPECTED_K['sphere_rotating']
    nominal=p.prediction(z).reshape(-1,3)
    q=np.tile([np.radians(2.),rate_dph/RAD2DPH],len(p.mount_yaw.groups))
    z[p.mount_slice]=q
    yaw=p.mount_yaw.B@q; rate=p.mount_yaw.D@q
    expected=Rotation.from_rotvec(-yaw[:,None]*p.bins['up']).apply(nominal)+rate[:,None]*p.bins['up']
    np.testing.assert_allclose(p.prediction(z).reshape(-1,3),expected,atol=1.e-14)


def test_mount_and_crab_joint_jacobian_bounds_and_nesting():
    p=problem(); z=np.zeros(p.npar); z[:3]=[1.,1.,0.]
    z[p.mount_slice]=[.03,1.e-6,-.02,-2.e-6]
    _,J=p.prediction(z,True)
    for i in range(p.npar):
        step=1.e-8 if i in range(p.mount_slice.start,p.mount_slice.stop) else 1.e-6
        a=z.copy(); b=z.copy(); a[i]+=step; b[i]-=step
        np.testing.assert_allclose(J[:,i],(p.prediction(a)-p.prediction(b))/(2*step),rtol=1.e-5,atol=1.e-8)
    free=p.solve(); constrained=p.solve(fixed=models.EXPECTED_K['sphere_rotating'],start=free['z'])
    assert free['success'] and constrained['success']
    assert free['objective']<=constrained['objective']+1.e-6
    assert np.linalg.matrix_rank(p.mount_yaw.penalty())==p.nm
    lo,hi=p.bounds(); assert np.all(free['z']>=lo) and np.all(free['z']<=hi)
    assert p.mount_yaw.near_boundary(hi[p.mount_slice])
    from lll.profile_pairs import solve_pair
    name=next(iter(MODEL_PAIRS)); pair=solve_pair(p,name)
    endpoint=solve_pair(p,name,endpoint=0.,start=pair)
    assert pair['success'] and endpoint['success'] and pair['objective']<=endpoint['objective']+1.e-6
    profile=p.profile(models.EXPECTED_K['sphere_still'],np.eye(3),reference=free)
    assert profile['success'] and free['objective']<=profile['objective']+1.e-6
    with pytest.raises(ValueError,match='nonlinear'): p.local(p.y,free)


def path(mount=False):
    from test_core_pipeline import profile_fit_fixture
    f=profile_fit_fixture(); config=f['inference_policy']['settings']
    config['n_boot']=0; f['bootstrap']['requested']=0
    f.update(convergence={'converged':True},model_test_rank=3,k=dict(zip(fit.TERM_NAMES,[1.,1.,0.])),
        k_sd=dict.fromkeys(fit.TERM_NAMES,.1),rejected={'sphere_rotating':False,'sphere_still':True,'flat_still':True})
    if mount:
        config.update(mount_yaw_model='piecewise',mount_yaw_segments=[1],mount_yaw_policy=MOUNT_YAW_POLICY)
        f['mount_yaw_test_near_boundary']=False
    f['eligibility_policy']=eligibility_provenance(True,config)
    f['design_identifiability']['assumptions']=copy.deepcopy(envelope_assumptions(config))
    for p in f['pairwise_profile'].values(): p['bootstrap']['requested']=0
    return f


def test_both_paths_must_be_informative_and_agree_for_each_decision():
    a,b=path(True),path(); name=next(iter(MODEL_PAIRS))
    assert scientific_exclusions({'fit':a},name)  # Fit alone cannot certify agreement.
    report=compare_paths(a,b); assert report['primary_agree'] and report['pairwise'][name]['agree']
    a['magnetic_ambiguity_comparison']=report
    assert not scientific_exclusions({'fit':a}) and not scientific_exclusions({'fit':a},name)
    b['rejected']['sphere_rotating']=True
    assert not compare_paths(a,b)['primary_agree']
    b['pairwise_profile'][name]['p_diagnostic']['sphere_rotating']=1.e-12
    assert not compare_paths(a,b)['pairwise'][name]['agree']
    a['magnetic_ambiguity_comparison']=compare_paths(a,None)
    assert scientific_exclusions({'fit':a},name)


@pytest.mark.parametrize('reason',['orientation_unresolved','wmm_selection_sensitive'])
def test_control_path_integrity_and_original_selection_gate_remain(reason):
    a,b=path(True),path(); report=compare_paths(a,b,excluded_flags=[reason])
    assert not report['primary_agree'] and not any(v['agree'] for v in report['pairwise'].values())


def test_global_rank_failure_does_not_destroy_agreed_pair_evidence():
    a,b=path(True),path(); b['model_test_rank']=0; b['convergence']['converged']=False
    report=compare_paths(a,b)
    assert not report['primary_agree'] and all(v['agree'] for v in report['pairwise'].values())


def test_prior_boundary_and_shift_failures_abstain():
    a,b=path(True),path(); b['k']['k_rot_sphere']+=1.
    assert not compare_paths(a,b)['primary_agree']
    b['pairwise_profile'][next(iter(MODEL_PAIRS))]['estimate']+=1.
    assert not compare_paths(a,b)['pairwise'][next(iter(MODEL_PAIRS))]['agree']
    a['mount_yaw_test_near_boundary']=True
    assert not compare_paths(a,path())['primary_agree']
    a['pairwise_profile'][next(iter(MODEL_PAIRS))]['exclusions']=['pair prior dominated']
    assert not compare_paths(a,path())['pairwise'][next(iter(MODEL_PAIRS))]['agree']


def test_missing_and_nonfinite_endpoint_decisions_cannot_agree():
    a,b=path(True),path(); name=next(iter(MODEL_PAIRS))
    a['rejected']=b['rejected']={}
    assert not compare_paths(a,b)['primary_agree']
    a['pairwise_profile'][name]['p_diagnostic']=b['pairwise_profile'][name]['p_diagnostic']={}
    assert not compare_paths(a,b)['pairwise'][name]['agree']
    a['pairwise_profile'][name]['sd']=None
    assert not compare_paths(a,b)['pairwise'][name]['agree']


def test_unvalidated_empirical_policy_and_incomplete_mode_are_refused():
    p=problem()
    with pytest.raises(ValueError,match='envelope'): fit.fit(p.bins,p.fwd,p.bias_fn,np.ones(3),mount_yaw_model='piecewise',n_boot=0)
    with pytest.raises(ValueError,match='dual-path'): fit.fit(p.bins,p.fwd,p.bias_fn,np.ones(3),mount_yaw_model='piecewise',
        mount_yaw_segments=[0],design_mode='envelope',pairwise_method='profile',decision_thresholds={},n_boot=0)


def test_cli_freezes_magnetic_comparison_without_running(tmp_path,monkeypatch):
    import research
    monkeypatch.setattr(research,'flight_run',lambda *a,**k:pytest.fail('preparation ran a flight'))
    out=tmp_path/'proposal.json'
    monkeypatch.setattr('sys.argv',['research.py','--magnetic-ambiguity','model_and_compare',
        '--design-mode','envelope','--pairwise-method','profile','--bootstrap','0','--write-manifest',str(out),'-o',str(tmp_path/'unrun.json')])
    research.main(); manifest=json.loads(out.read_text())
    assert manifest['config']['magnetic_ambiguity']=='model_and_compare'
    assert manifest['config']['pairwise_method']=='profile'
    assert not (tmp_path/'unrun.json').exists()


def test_analyzer_retains_flagged_bins_but_abstains_without_control(tmp_path,monkeypatch):
    import lll.analyze as module
    from lll.synth import synthesize
    from lll.trajectory import track_spec
    from test_core_pipeline import track_case
    case=track_case(); case['candidate_window']['end_s']=1200.
    case['rows']=[dict(t_s=float(t),latitude_deg=40.+t*.002,longitude_deg=-30.+t*.001,
        reported_altitude_m=11000.,ground_course_deg=30.,ground_speed_mps=240.,is_provider_estimate=False)
        for t in range(0,1201,20)]
    session=tmp_path/'fixture.zip'
    synthesize(session,'sphere_rotating',fs=20.,trajectory_input=track_spec(case),cal_pos_s=40.,gap_s=0.)
    monkeypatch.setattr(module,'estimate_forward_axis',lambda *a:(np.array([1.,0.,0.]),{'fixture':'known axis'}))
    monkeypatch.setattr(module.slip,'watchdog',lambda bins,*a:dict(available=True,version='magnetic-watchdog-2',
        exclude_segments=sorted(int(s) for s in np.unique(bins['seg']))))
    options=dict(n_boot=0,design_mode='envelope',pairwise_method='profile',magnetic_ambiguity='model_and_compare')
    result=module.analyze(session,fit_options=options)
    assert result['slip']['retained_bins']>0 and result['slip']['would_exclude_bins']>0
    assert result['slip']['ambiguous_boundary_bins']>0
    assert 'fit' in result and result['magnetic_exclusion_path']['fit'] is None
    assert not result['fit']['magnetic_ambiguity_comparison']['primary_agree']
    assert all(p['status']=='abstain' for p in result['fit']['pairwise'].values())
    assert 'magnetic retained/excluded paths disagree or comparison unavailable' in result['scientific_exclusions']


def test_analyzer_reruns_original_exclusion_path_with_its_own_settings(tmp_path,monkeypatch):
    import lll.analyze as module
    from lll.synth import synthesize
    session=tmp_path/'two-legs.zip'
    synthesize(session,'sphere_rotating',fs=20.,legs=((10.,12.),(100.,12.)),cal_pos_s=40.,gap_s=0.)
    monkeypatch.setattr(module,'estimate_forward_axis',lambda *a:(np.array([1.,0.,0.]),{'fixture':'known axis'}))
    monkeypatch.setattr(module.slip,'watchdog',lambda bins,*a:dict(available=True,version='magnetic-watchdog-2',
        exclude_segments=[int(np.min(bins['seg']))]))
    result=module.analyze(session,fit_options=dict(n_boot=0,design_mode='envelope',pairwise_method='profile',
        magnetic_ambiguity='model_and_compare'))
    control=result['magnetic_exclusion_path']; settings=result['fit']['inference_policy']['settings']
    assert control['fit'] is not None
    assert settings['mount_yaw_model']=='piecewise'
    assert 'mount_yaw_model' not in control['fit']['inference_policy']['settings']
    assert control['input_sha256']==result['input_sha256']
    assert result['fit']['n_bins']>control['fit']['n_bins']
    assert 'magnetic_ambiguity_comparison' not in control['fit']
