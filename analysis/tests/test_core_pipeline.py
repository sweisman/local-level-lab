# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small deterministic checks of maneuver guards, replay and research candidates."""
import copy
import json

import numpy as np
import pytest

from lll.attitude import mount_epochs
from lll.maneuvers import maneuver_mask, turn_motion_check
from lll.trajectory import track_spec, TrackReplay
from lll.research_design import realize, scenario
from lll.design_envelope import envelope_information, envelope_size
from lll.inference import CandidateProblem, design_information
from lll.profile_pairs import solve_pair, profile_evidence
from lll.policy import MODEL_PAIRS, scientific_exclusions, eligibility_provenance
from lll.pairwise import pair_stratum, pool_evidence
from test_release060 import crab_fixture
from test_research_candidates import settings


def track_case():
    return dict(id='fixture',status='prepared_geometry_only',source_sha256='fixture-hash',
        candidate_window=dict(start_s=0.,end_s=120.), rows=[dict(t_s=float(t),latitude_deg=40.+t*.002,
            longitude_deg=179.9+t*.001,reported_altitude_m=11000.,ground_course_deg=30.,
            ground_speed_mps=240.,is_provider_estimate=False) for t in range(0,121,20)])


def test_guard_rejects_moving_aircraft_and_missing_coverage():
    t=np.arange(0.,80.,.05); gyro=np.zeros((len(t),3))
    gyro[(t>=20)&(t<24),2]=np.radians(45.)
    gt=np.arange(80.)
    kin=dict(t=gt,speed=np.full(80,240.),psi_dot=np.zeros(80))
    clear=maneuver_mask(kin)
    epochs,_=mount_epochs(t,gyro,[(39.,'index_turn')],aircraft_motion=clear)
    assert not epochs[-1].get('orientation_unresolved')
    kin['psi_dot'][20:60]=np.radians(3.)
    bad=maneuver_mask(kin)
    epochs,_=mount_epochs(t,gyro,[(39.,'index_turn')],aircraft_motion=bad)
    assert epochs[-1]['orientation_unresolved']
    assert epochs[-1]['turn']['aircraft_motion']['reason']=='aircraft maneuver'
    assert not turn_motion_check(maneuver_mask(None),19.,25.)['safe']


def test_buffer_and_gaps_are_forbidden():
    kin=dict(t=np.array([0.,1.,2.,20.,21.,22.]),speed=np.full(6,240.),psi_dot=np.zeros(6))
    assert not turn_motion_check(maneuver_mask(kin,buffer_s=120.),10.,15.)['safe']


@pytest.mark.parametrize('field,value',[('speed',0.),('speed',np.nan),('h_acc',999.),('vz',np.nan)])
def test_motion_mask_requires_usable_position_evidence(field,value):
    kin=dict(t=np.arange(40.),speed=np.full(40,240.),psi_dot=np.zeros(40),vz=np.zeros(40),h_acc=np.full(40,5.))
    kin[field][15:25]=value
    assert not turn_motion_check(maneuver_mask(kin),17.,22.)['safe']


def test_replay_preserves_gaps_estimates_and_longitude_wrap():
    case=track_case(); case['rows'][2]['is_provider_estimate']=True
    case['rows'][-1]['longitude_deg']=-179.98
    spec=track_spec(case); replay=TrackReplay(spec)
    assert not replay.support(np.array([40.]))[0]
    assert replay.support(np.array([10.,70.])).all()
    out=replay.sample(np.array([60.,70.,80.,90.,100.,110.,120.]))
    assert np.isfinite(out['speed']).all()
    assert np.max(out['speed'])<1000.
    assert case['rows'][2]['is_provider_estimate']
    gn=TrackReplay(track_spec(case,'observed_fixes')).observed_gnss(10.,10**12,1000)
    assert np.isnan(gn['h_acc_m']).all()
    assert len(gn['t_ns'])==6
    changed=copy.deepcopy(spec); changed['rows'][0]['latitude_deg']+=1
    with pytest.raises(ValueError,match='hash'): TrackReplay(changed)


def test_replay_coverage_block_and_composition_streams():
    case=track_case(); case['status']='blocked_by_observed_coverage'
    with pytest.raises(ValueError,match='blocked'): track_spec(case)
    a=realize(600900,'wind+bias_mixed+correlated+thermal',geometry='fixed')
    b=realize(600900,'thermal+correlated+bias_mixed+wind',geometry='fixed')
    assert a['simulator']==b['simulator']
    assert a['nuisance_component_streams']==b['nuisance_component_streams']
    assert a['simulator']['wind_ne_mps']==[12.,-8.]
    assert a['simulator']['rw_dph_sqrth']==1.5
    with pytest.raises(ValueError,match='duplicate'): scenario('wind+wind')


def problem_fixture(**options):
    bins,fwd=crab_fixture()
    return CandidateProblem(bins,fwd,lambda _:0.,np.full(3,1e-5),
        settings(crab_model='dynamic',bias_model='constant',forward_uncertainty=True,
                 crab_sigma_deg=5.,**options),forward_sigma_rad=.02)


def test_envelope_is_geometry_only_and_reports_worst_states():
    p=problem_fixture(); p.settings['design_mode']='envelope'
    a=envelope_information(p)
    p.bins['gyro']+=1000.
    b=envelope_information(p)
    assert a==b
    assert a['svd_evaluations']==envelope_size(p)
    assert a['envelope_configuration']['evaluated_noise_dph']==6.
    assert all('limiting_state' in v for v in a['model_contrast_information'].values())
    assert a['assumptions']['version']=='nuisance-envelope-1'


def test_pair_line_solver_uses_pair_direction_without_global_rank():
    p=problem_fixture(); p.use_crab=False
    name=next(iter(MODEL_PAIRS)); a,b=MODEL_PAIRS[name]
    from lll import models
    z=np.zeros(p.npar)
    z[:3]=np.asarray(models.EXPECTED_K[b])+.7*(np.asarray(models.EXPECTED_K[a])-models.EXPECTED_K[b])
    p.y=p.prediction(z)
    free=solve_pair(p,name)
    first=solve_pair(p,name,endpoint=1.,start=free)
    second=solve_pair(p,name,endpoint=0.,start=free)
    assert free['success'] and free['estimate']==pytest.approx(.7,abs=1e-4)
    assert free['objective']<min(first['objective'],second['objective'])


def test_profile_stratum_and_pooling_are_method_specific():
    name=next(iter(MODEL_PAIRS)); entry=dict(method='pair-line-profile-1',eligible=True)
    a=dict(candidate_id='c',variant='spp',model_test_rank=1,pairwise={name:entry})
    b={**a,'model_test_rank':3}
    assert pair_stratum(a,name)==pair_stratum(b,name)
    original=dict(method='observable-coordinate-1',eligible=True)
    with pytest.raises(ValueError,match='incompatible'):
        pool_evidence([('unit',{name:entry}),('other',{name:original})],'c','spp')


@pytest.mark.parametrize('mode',['observed_fixes','simulated_high_rate'])
def test_short_replay_exercises_encoded_session_without_a_campaign(tmp_path,mode):
    from lll.synth import synthesize
    from lll.format import read_session
    spec=track_spec(track_case(),mode)
    path=tmp_path/'tiny.zip'
    synthesize(path,'flat_still',fs=20.,cal=(),gap_s=0.,trajectory_input=spec,
        wind_ne_mps=[12.,-8.],wind_rate_ne_mps_per_h=[3.,-2.])
    session=read_session(path)
    assert session.manifest['trajectory_replay']['trajectory_hash']==spec['trajectory_hash']
    gn=session.streams['gnss']
    if mode=='observed_fixes':
        assert len(gn['t_ns'])==7 and np.isnan(gn['h_acc_m']).all()
    else:
        assert len(gn['t_ns'])>100 and np.isfinite(gn['h_acc_m']).all()
    assert spec['trajectory_hash']==track_spec(track_case(),mode)['trajectory_hash']
    from lll.analyze import analyze
    diagnostic=tmp_path/'diagnostics'
    result=analyze(path,diagnostics_directory=diagnostic)
    assert (diagnostic/'session.zip').read_bytes()==path.read_bytes()
    assert json.loads((diagnostic/'analysis.json').read_text())['input_sha256']==result['input_sha256']
    with pytest.raises(FileExistsError): analyze(path,diagnostics_directory=diagnostic)
    with pytest.raises(ValueError,match='domain enforcement'):
        analyze(path,fit_options={'decision_policy':{}})


def test_simulated_wind_preserves_observed_ground_path_and_holes(tmp_path):
    from lll.synth import synthesize
    from lll.format import read_session
    case=track_case(); case['rows'][2]['is_provider_estimate']=True
    spec=track_spec(case)
    streams=[]
    for name,wind in [('clear',None),('wind',[12.,-8.])]:
        path=tmp_path/(name+'.zip')
        synthesize(path,'sphere_still',fs=20.,cal=(),gap_s=0.,trajectory_input=spec,wind_ne_mps=wind)
        session=read_session(path); streams.append(session.streams['gnss'])
        seconds=(session.streams['gnss']['t_ns']-10**12)/1e9
        assert not ((seconds>20.) & (seconds<60.)).any()
        assert any(kind=='imu_disconnect' for _,kind,_ in session.events)
        resumed=[stamp for stamp,kind,_ in session.events if kind=='imu_connect']
        configured=[stamp for stamp,kind,_ in session.events if kind=='imu_config']
        assert set(resumed)<=set(configured)
    for key in streams[0]: np.testing.assert_array_equal(streams[0][key],streams[1][key])


def profile_fit_fixture():
    from test_candidate_eligibility import candidate_fit
    from lll.design_envelope import ENVELOPE_ASSUMPTIONS
    result=candidate_fit()
    config=result['inference_policy']['settings']
    config.update(design_mode='envelope',pairwise_method='profile')
    result['eligibility_policy']=eligibility_provenance(True,config)
    result['design_identifiability']['assumptions']=copy.deepcopy(ENVELOPE_ASSUMPTIONS)
    result['design_identifiability']['untruncated_contrasts']=copy.deepcopy(
        result['design_identifiability']['model_contrast_information'])
    result['model_test_rank']=0
    result['convergence']['converged']=False
    result['bootstrap']['bootstrap_valid']=False
    result['pairwise_profile']={name:dict(method='pair-line-profile-1',eligible=True,exclusions=[],
        converged=True,estimate=1.,sd=.1,statistics={a:0.,b:100.},p_diagnostic={a:1.,b:1e-12},
        bootstrap=dict(requested=20,bootstrap_valid=True)) for name,(a,b) in MODEL_PAIRS.items()}
    return result


def test_pair_profile_gate_uses_own_rank_convergence_and_bootstrap():
    from lll.pairwise import flight_evidence
    result=profile_fit_fixture(); name=next(iter(MODEL_PAIRS))
    assert not scientific_exclusions({'fit':result,'flags':['inference_nonconvergence','prior_dominated']},name)
    assert scientific_exclusions({'fit':result})
    assert flight_evidence(result)[name]['status']=='decision'
    result['design_identifiability']['untruncated_contrasts'][name]['retained_fraction']=.01
    assert 'pair contrast not identified' in scientific_exclusions({'fit':result},name)
    result=profile_fit_fixture(); result['pairwise_profile'][name]['bootstrap']['bootstrap_valid']=False
    assert 'inadequate pair bootstrap convergence' in scientific_exclusions({'fit':result},name)
    result=profile_fit_fixture(); result['pairwise_profile'].pop(name)
    assert 'pair profile unavailable' in scientific_exclusions({'fit':result},name)
    result=profile_fit_fixture()
    assert 'unresolved orientation' in scientific_exclusions({'fit':result,'flags':['orientation_unresolved']},name)


def test_profile_bootstrap_and_prior_failures_abstain(monkeypatch):
    p=problem_fixture(); name=next(iter(MODEL_PAIRS))
    design={'untruncated_contrasts':{n:dict(estimable=True) for n in MODEL_PAIRS}}
    result=profile_evidence(p,design,n_boot=1,block=len(p.bins['t']))
    assert all('inadequate pair bootstrap convergence' in v['exclusions'] for v in result.values())
    import lll.profile_pairs as module
    original=module.solve_pair
    def solve(*args,**kwargs):
        output=original(*args,**kwargs)
        if kwargs.get('penalty') is not None: output={**output,'success':False}
        return output
    monkeypatch.setattr(module,'solve_pair',solve)
    result=profile_evidence(p,design)
    assert 'pair prior refit did not converge' in result[name]['exclusions']


def test_profile_pool_keeps_physical_units_and_method():
    name=next(iter(MODEL_PAIRS))
    entry=dict(method='pair-line-profile-1',eligible=True,estimate=.95,sd=.05)
    output=pool_evidence([('u1',{name:entry}),('u1',{name:entry}),('u2',{name:entry}),('u3',{name:entry})],'c','spp')
    assert output['pairwise'][name]['method']=='pair-line-profile-reml-hk-1'
    assert output['pairwise'][name]['n_units']==3 and output['pairwise'][name]['n_sessions']==4
    assert output['pairwise'][name]['eligible']


def test_profile_rejects_thresholds_for_the_other_statistic(monkeypatch):
    import lll.pairwise as module
    monkeypatch.setattr(module,'check_pairwise_policy',lambda *args:None)
    with pytest.raises(ValueError,match='statistic method'):
        module.flight_evidence(profile_fit_fixture(),policy={'statistic_methods':['observable-coordinate-1']})


def test_diagnostics_retain_exception_and_raw_input(tmp_path,monkeypatch):
    import lll.analyze as module
    source=tmp_path/'bad.zip'; source.write_bytes(b'fixture')
    def fail(*args,**kwargs): raise ValueError('fixture failure')
    monkeypatch.setattr(module,'_analyze',fail)
    with pytest.raises(ValueError,match='fixture failure'):
        module.analyze(source,diagnostics_directory=tmp_path/'failed')
    assert (tmp_path/'failed'/'session.zip').read_bytes()==b'fixture'
    assert json.loads((tmp_path/'failed'/'failure.json').read_text())['type']=='ValueError'


def test_geometry_optimizer_masks_maneuvers_and_never_calls_fitter(monkeypatch):
    import optimize_turns as optimizer
    import lll.design_geometry as geometry
    import lll.design_envelope as envelope
    t=np.arange(0.,2400.)
    kin=dict(t=t,speed=np.full(len(t),240.),psi_dot=np.zeros(len(t)))
    kin['psi_dot'][1190:1210]=np.radians(1.)
    monkeypatch.setattr(geometry,'geometry_kinematics',lambda _: (kin,2400.))
    calls=[]
    monkeypatch.setattr(geometry,'geometry_problem',lambda design,schedule,crab,kin=None: (tuple(schedule),crab))
    def score(problem):
        calls.append(problem)
        schedule,crab=problem
        # Higher absolute information at 10 min must lose to estimable 15 min.
        retention=.8 if schedule==(15.,) else .1
        information=1. if schedule==(15.,) else 100.
        from lll.policy import CANDIDATE_POLICY
        return dict(assumptions=envelope.ENVELOPE_ASSUMPTIONS,rank_threshold=CANDIDATE_POLICY['retention_threshold'],
            model_contrast_information={n:dict(retained_fraction=retention,information=information,estimable=retention>.31) for n in MODEL_PAIRS})
    monkeypatch.setattr(envelope,'envelope_information',score)
    monkeypatch.setattr(optimizer,'flight_run',lambda *args,**kwargs:pytest.fail('full fitter called'))
    estimate=optimizer.search_geometry([{'geometry_cell':'fixture'}],max_turns=1,estimate_only=True)
    assert calls==[] and estimate['upper_bound_fits']==0 and 20. not in estimate['feasible_grid_min']
    output=optimizer.search_geometry([{'geometry_cell':'fixture'}],max_turns=1)
    assert output['best']['turn_schedule_min']==[15.]
    assert {crab for _,crab in calls}=={'dynamic','wind'}
    assert len(calls)==len(set(calls))


def test_observed_cli_freezes_combined_scenarios_without_attempts(tmp_path,monkeypatch):
    import research
    import sys
    spec_file=tmp_path/'trajectory.json'; spec_file.write_text(json.dumps(track_spec(track_case())))
    output=tmp_path/'manifest.json'
    monkeypatch.setattr(research,'flight_run',lambda *args,**kwargs:pytest.fail('flight attempt called'))
    monkeypatch.setattr(sys,'argv',['research','--geometry','observed','--trajectory',str(spec_file),
        '--scenarios','wind+bias_mixed','wind+bias_mixed+correlated+thermal','--design-mode','envelope',
        '--pairwise-method','profile','--bootstrap-refit','nonlinear','--write-manifest',str(output),
        '-o',str(tmp_path/'unused.json')])
    research.main()
    config=json.loads(output.read_text())['config']
    assert config['preregistered_geometry_cells']==['trajectory-'+track_spec(track_case())['trajectory_hash']]
    assert len(config['preregistered_scenarios'])==2 and config['pairwise_method']=='profile'


def test_fitted_diagnostics_capture_bins_rows_and_mounts(tmp_path):
    from lll.analyze import analyze
    from lll.synth import synthesize
    case=track_case(); case['candidate_window']['end_s']=1200.
    case['rows']=[dict(t_s=float(t),latitude_deg=40.+t*.002,longitude_deg=-30.+t*.001,
        reported_altitude_m=11000.,ground_course_deg=30.,ground_speed_mps=240.,is_provider_estimate=False)
        for t in range(0,1201,20)]
    spec=track_spec(case)
    session=tmp_path/'fixture.zip'
    synthesize(session,'sphere_rotating',fs=20.,trajectory_input=spec,cal_pos_s=40.,gap_s=0.)
    output=tmp_path/'diagnostics'
    result=analyze(session,fit_options={'n_boot':0},diagnostics_directory=output)
    assert 'fit' in result
    assert np.load(output/'mount-matrices.npy',allow_pickle=False).shape[-2:]==(3,3)
    with np.load(output/'fit-input.npz',allow_pickle=False) as data:
        assert len(data['t'])>0 and data['gyro'].shape[1]==3
    with np.load(output/'fit-rows.npz',allow_pickle=False) as data:
        assert len(data['y'])==len(data['bin_index'])==data['jacobian'].shape[0]


def test_preparation_preserves_all_seven_tracks_and_no_compute_allowance(tmp_path,monkeypatch):
    import prepare_core_pipeline as preparation
    import optimize_turns
    from lll.research_design import validate_manifest
    monkeypatch.setattr(optimize_turns,'flight_run',lambda *args,**kwargs:pytest.fail('flight attempt called'))
    manifest=preparation.prepare(preparation.ROOT/'docs/research-next-stage-20261006/geometry-stress-plan.json',
        preparation.ROOT/'docs/protocol-development-20261006/manifest.json',
        preparation.ROOT/'docs/protocol-development-20261006/processing-audit.json',tmp_path/'prepared')
    config=manifest['config']
    assert len(config['replay_inputs'])==10 and len(config['blocked_tracks'])==2
    assert config['authorized_additional_attempts']==0 and not config['execution_authorized']
    assert all(not arm['eligible_to_schedule'] for arm in config['matched_timing_arms'] if 'shift--10' in arm['name'] or 'shift-+10' in arm['name'])
    validate_manifest(manifest,config)


def test_profile_candidate_reaches_fit_and_separate_calibration():
    from lll import fit
    from lll.pairwise import flight_evidence,check_pairwise_policy
    from lll.pairwise_calibration import calibrate,group
    from lll.research_design import implementation_hash
    from lll.policy import decision_stratum
    from test_candidate_eligibility import campaign
    bins,fwd=crab_fixture()
    result=fit.fit(bins,fwd,lambda _:0.,np.full(3,1e-5),n_boot=0,crab_model='dynamic',
        design_mode='envelope',pairwise_method='profile')
    assert set(result['pairwise_profile'])==set(MODEL_PAIRS)
    assert result['eligibility_policy']==eligibility_provenance(True,result['inference_policy']['settings'])
    data=campaign(); data['implementation_hash']=implementation_hash()
    data['config'].update(pairwise_method='profile',geometry='fixed',preregistered_scenarios=['baseline'],
        operational_cells=[decision_stratum(dict(candidate_id='x',variant='spp',model_test_rank=r)) for r in [1,2,3]])
    for i,row in enumerate(data['records']):
        row.update(profile_fit_fixture()); row['model_test_rank']=i%4
        row['pairwise']=flight_evidence(row)
    policy=calibrate(data,min_accepted=5)
    assert policy['version']=='pairwise-empirical-2' and policy['statistic_methods']==['pair-line-profile-1']
    assert policy['family_size']==6 and len(policy['thresholds'])==3
    check_pairwise_policy(policy,'flight')
    name=next(iter(MODEL_PAIRS)); row=data['records'][0]
    assert group(row,name,'flight')==group({**row,'model_test_rank':3},name,'flight')
    assert flight_evidence(row,policy=policy,candidate_id='x',variant='spp')[name]['calibrated']
