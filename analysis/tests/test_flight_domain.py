# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observable domain guards, exercised without flight synthesis or a tail campaign."""
import copy
import json

import numpy as np
import pytest

from lll import fit, models
from lll.flight_domain import (VERSION, METRICS, descriptor, observables, membership,
                              check_record_domain, decision_exclusions, acquisition_source)
from lll.inference_policy import digest
from lll.policy import scientific_exclusions, decision_stratum, MODEL_PAIRS
from lll.pairwise import flight_evidence, pair_stratum, check_pairwise_policy
from lll.research_calibration import calibrate, assess, check_policy, preregistered_groups
from lll.pairwise_calibration import calibrate as calibrate_pairs, assess as assess_pairs
from test_candidate_eligibility import campaign, candidate_fit


def geometry():
    # Independent geometry fixture: 4 contiguous minutes, two headings straddling north.
    return dict(t=np.array([30.,90.,150.,210.]),dt=np.full(4,60.),lat=np.radians([30.,31.,32.,33.]),
                v_n=200*np.cos(np.radians([350.,350.,10.,10.])),
                v_e=200*np.sin(np.radians([350.,350.,10.,10.])),epoch=np.array([0.,0.,1.,1.]))


def envelope(source='binned_input'):
    bounds = dict(latitude_min_deg=[20.,40.],latitude_max_deg=[20.,40.],speed_min_mps=[190.,210.],
                  speed_max_mps=[190.,210.],usable_minutes=[3.,5.],elapsed_minutes=[3.,5.],
                  heading_span_deg=[10.,30.],max_gap_seconds=[0.,5.],max_bin_seconds=[30.,60.],
                  n_bins=[4,4],n_epochs=[2,2])
    return descriptor(dict(version=VERSION,sources=[source],bounds=bounds,epoch_start_minutes=[[0.,0.],[1.9,2.1]]))


def scoped_campaign():
    data=campaign()
    domain=envelope()
    obs=observables(geometry())
    data['config']['flight_domain']=domain
    for row in data['records']:
        row.update(flight_domain=domain,domain_observables=obs,domain_membership=membership(domain,obs),domain_id=domain['domain_id'])
    return data


def test_observables_are_outcome_independent_and_circular():
    bins=geometry()
    obs=observables(bins)
    assert obs['heading_span_deg']==pytest.approx(20.)
    assert obs['usable_minutes']==4 and obs['elapsed_minutes']==4
    assert obs['epoch_start_minutes']==[0.,2.]
    assert obs['max_gap_seconds']==0 and obs['latitude_min_deg']==pytest.approx(30.)
    bins.update(gyro=np.full((4,3),np.nan),truth='flat_still',science_coefficients=[100.,100.,100.])
    assert observables(bins)==obs
    shifted=copy.deepcopy(bins); shifted['t']+=5000.
    assert observables(shifted)==obs


@pytest.mark.parametrize('change',[
    lambda b:b['t'].__setitem__(1,30.), lambda b:b['dt'].__setitem__(1,-1.),
    lambda b:b['lat'].__setitem__(0,np.nan),lambda b:b['epoch'].__setitem__(2,.5),
    lambda b:b['dt'].__setitem__(0,100.),lambda b:b.pop('epoch')])
def test_invalid_geometry_is_unavailable(change):
    bins=geometry(); change(bins)
    assert observables(bins) is None
    assert not membership(envelope(),observables(bins))['inside']


@pytest.mark.parametrize('metric',METRICS)
def test_boundaries_and_outside_values(metric):
    domain=envelope(); obs=observables(geometry())
    lo,hi=domain['bounds'][metric]
    for v in (lo,hi):
        assert membership(domain,{**obs,metric:v})['inside']
    for v in (lo-1e-8,hi+1e-8,float('nan'),None,True):
        assert not membership(domain,{**obs,metric:v})['inside']


def test_identity_schedule_source_and_no_implicit_widening():
    d=envelope(); obs=observables(geometry())
    assert descriptor(json.loads(json.dumps(d)))==d
    assert membership(d,obs)['domain_id']==d['domain_id']
    for update in ({'source':'recorded_gnss'},{'epoch_start_minutes':[0.,2.2]}, {'epoch_start_minutes':[]}, {'version':'old'}):
        assert not membership(d,{**obs,**update})['inside']
    bad=copy.deepcopy(d); bad['bounds']['latitude_max_deg'][1]+=1
    with pytest.raises(ValueError,match='identity'): descriptor(bad)
    for update in ({'sources':['unknown']},{'epoch_start_minutes':[[0,0],[0,2]]},{'bounds':{}},{'extra':True}):
        with pytest.raises(ValueError): descriptor({**d,**update})


def test_shared_gate_recomputes_membership():
    row=scoped_campaign()['records'][0]
    assert scientific_exclusions({'fit':row})==[]
    row['domain_observables']={**row['domain_observables'],'speed_max_mps':220.}
    assert 'speed_max_mps outside calibrated domain' in scientific_exclusions({'fit':row})
    with pytest.raises(ValueError,match='record flight domain'): check_record_domain(row,envelope())


def test_scoped_calibration_freeze_and_validation_mismatch():
    data=scoped_campaign(); policy=calibrate(data,min_accepted=5)
    assert policy['version']=='empirical-decision-5'
    assert json.loads(next(iter(policy['thresholds'])))[3]==envelope()['domain_id']
    check_policy(policy)
    row=data['records'][0]
    assert not decision_exclusions(row,policy)
    assert decision_exclusions(row,calibrate(campaign(),min_accepted=5))
    config={**data['config'],'geometry':'fixed','operational_cells':[decision_stratum(row)],'preregistered_scenarios':['baseline']}
    assert len(preregistered_groups(config))==1
    bad=copy.deepcopy(data); bad['records'][0].pop('domain_observables')
    with pytest.raises(ValueError,match='record flight domain'): calibrate(bad,min_accepted=5)
    badpolicy=copy.deepcopy(policy); badpolicy['domain_id']='other'
    badpolicy['policy_hash']=digest({k:v for k,v in badpolicy.items() if k!='policy_hash'})
    with pytest.raises(ValueError,match='domain mismatch'): check_policy(badpolicy)
    validation={**data,'partition':'validation','config':{'tail_min_accepted':2000,'decision_policy_hash':policy['policy_hash']},
                'records':[{**r,'partition':'validation','seed':r['seed']+1_000_000,'flight_domain':None} for r in data['records']]}
    with pytest.raises(ValueError,match='validation flight domain'): assess(validation,policy)


def test_primary_fit_and_pairwise_lookup_abstain_outside_domain(monkeypatch):
    data=scoped_campaign(); policy=calibrate(data,min_accepted=5)
    result=candidate_fit()
    result.update(chi2_free=0.,chi2={m:3. for m in models.MODELS},
                  delta_chi2_identifiable={m:3. for m in models.MODELS},rejected=dict.fromkeys(models.MODELS,False),
                  k=dict(zip(('k_rot_sphere','k_curv','k_disc'),[1.,1.,0.])),k_cov=np.eye(3).tolist())
    monkeypatch.setattr('lll.inference.candidate_fit',lambda *a,**kw:copy.deepcopy(result))
    observed=fit.fit(geometry(),None,None,None,research_candidate=True,n_boot=0,
                     decision_policy=policy,decision_candidate_id='x',decision_variant='spp')
    assert observed['decision_valid'] and all(v is False for v in observed['rejected'].values())
    for row in data['records']:
        row.update(k=result['k'],k_cov=result['k_cov'])
        row['pairwise']=flight_evidence(row)
    pairs=calibrate_pairs(data,min_accepted=5)
    assert pairs['version']=='pairwise-empirical-3'
    check_pairwise_policy(pairs,'flight')
    evidence=flight_evidence(observed,policy=pairs,candidate_id='x',variant='spp')
    assert all(e['calibrated'] and e['eligible'] for e in evidence.values())
    bins=geometry(); bins['lat'][:]=np.radians(50.)
    outside=fit.fit(bins,None,None,None,research_candidate=True,n_boot=0,
                    decision_policy=policy,pairwise_decision_policy=pairs,decision_candidate_id='x',decision_variant='spp')
    assert outside['domain_id'] is None and not outside['decision_valid']
    assert all(v is None for v in outside['rejected'].values())
    assert all(e['status']=='abstain' and not e['eligible'] for e in outside['pairwise'].values())
    legacy=fit.fit(geometry(),None,None,None,research_candidate=True,n_boot=0,
                   decision_policy=calibrate(campaign(),min_accepted=5),decision_candidate_id='x',decision_variant='spp')
    assert not legacy['decision_valid'] and all(v is None for v in legacy['rejected'].values())
    validation={**data,'partition':'validation','config':{'pairwise_decision_policy_hash':pairs['policy_hash']},
                'records':[{**r,'flight_domain':None,'partition':'validation','seed':r['seed']+1_000_000} for r in data['records']]}
    with pytest.raises(ValueError,match='validation flight domain'): assess_pairs(validation,pairs)


def test_pair_profile_domain_key_and_rank_independence():
    name=next(iter(MODEL_PAIRS)); row={'candidate_id':'x','variant':'spp','model_test_rank':3,
        'domain_id':envelope()['domain_id'],'pairwise':{name:{'method':'pair-line-profile-1'}}}
    key=pair_stratum(row,name)
    assert json.loads(key)[-1]==row['domain_id'] and len(json.loads(key))==5
    assert pair_stratum({**row,'model_test_rank':1},name)==key


def test_recording_source_is_distinct_from_synthetic_and_replay_lanes():
    assert acquisition_source({})=='recorded_gnss'
    assert acquisition_source({'quality':{'flags':['synthetic']}})=='synthetic_gnss'
    assert acquisition_source({'trajectory_replay':{'mode':'observed_fixes'}})=='replay_observed_fixes'
    assert acquisition_source({'trajectory_replay':{'mode':'simulated_high_rate'}})=='replay_simulated_high_rate'
    assert not membership(envelope('synthetic_gnss'),observables(geometry(),acquisition_source({})))['inside']
    with pytest.raises(ValueError,match='exactly one'):
        descriptor({**envelope(),'sources':['synthetic_gnss','recorded_gnss']})


def test_domain_implementation_is_part_of_the_source_freeze(monkeypatch):
    from pathlib import Path
    from lll.research_design import implementation_hash
    baseline=implementation_hash()
    original=Path.read_text
    def changed(path,*args,**kwargs):
        content=original(path,*args,**kwargs)
        return content+'\n# changed domain implementation\n' if path.name=='flight_domain.py' else content
    monkeypatch.setattr(Path,'read_text',changed)
    assert implementation_hash()!=baseline


def test_direct_profile_calibration_keeps_domain_after_rank_collapse(monkeypatch,tmp_path):
    from test_core_pipeline import profile_fit_fixture
    data=scoped_campaign()
    domain=data['config']['flight_domain']
    data['config'].update(pairwise_method='profile',geometry='fixed',preregistered_scenarios=['baseline'],
        operational_cells=[decision_stratum({'candidate_id':'x','variant':'spp','model_test_rank':r,
                                              'domain_id':domain['domain_id']}) for r in [1,2,3]])
    for i,row in enumerate(data['records']):
        row.update(profile_fit_fixture()); row['model_test_rank']=i%4
        row['pairwise']=flight_evidence(row)
    policy=calibrate_pairs(data,min_accepted=5)
    assert policy['version']=='pairwise-empirical-3' and len(policy['thresholds'])==3
    check_pairwise_policy(policy,'flight')
    row=data['records'][0]; name=next(iter(MODEL_PAIRS))
    entry=flight_evidence(row,policy=policy,candidate_id='x',variant='spp')[name]
    assert entry['eligible'] and entry['calibrated']
    row['domain_observables']={**row['domain_observables'],'epoch_start_minutes':[0.,3.]}
    entry=flight_evidence(row,policy=policy,candidate_id='x',variant='spp')[name]
    assert not entry['calibrated'] and entry['status']=='abstain'
    # Preparing validation inherits the exact envelope and parses rank metadata,
    # rather than treating a comparison name in a profile threshold key as rank.
    import research
    import sys
    policy_file=tmp_path/'pairs.json'; policy_file.write_text(json.dumps(policy))
    manifest_file=tmp_path/'manifest.json'
    monkeypatch.setattr(sys,'argv',['research.py','--partition','validation','--truth','all',
        '--design-mode','envelope','--pairwise-method','profile','--bootstrap','0',
        '--pairwise-decision-policy',str(policy_file),'--write-manifest',str(manifest_file),'-o',str(tmp_path/'unused.json')])
    research.main()
    config=json.loads(manifest_file.read_text())['config']
    assert config['flight_domain']==domain
    assert all(json.loads(c)==['x','spp',1,domain['domain_id']] for c in config['operational_cells'])
