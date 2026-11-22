# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small complete compensated native protocol with charged construction/work."""
import pytest


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    from lll.ilvis0_noise_step import load as noise_load
    from lll.ilvis0_coordinate_precision import load
    from lll.studies.artifacts import digest
    from pathlib import Path
    root=Path('analysis/lll');directory=tmp_path_factory.mktemp('compensated-protocol');builds=[]
    reserve=lambda:builds.append(1)
    noise,_=noise_load(directory,expected_source_sha256=digest((root/'ilvis0_tangent.cpp').read_bytes()),
        expected_bridge_sha256=digest((root/'ilvis0_noise_bridge.cpp').read_bytes()),
        expected_wide_loader_sha256=digest((root/'ilvis0_wide_tangent.py').read_bytes()),reserve_build=reserve)
    def factory(anchor):
        k,m=load(directory,reserve_build=reserve,gravity_anchor_height_m=anchor)
        assert len(builds)<=2
        return None,k,dict(tangent=m)
    yield noise,factory
    assert len(builds)==2


@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[0,1])
def test_compensated_short_protocol(native,law,model,profile):
    from lll.coordinate_optimizer_study import case_recipe
    from lll.structured_noisy_training import calculate,limits
    from lll.structured_noisy_report import check_case
    r=dict(case_recipe(281474976810726),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,maximum_evaluations=8)
    spec=dict(law=law,model=r['models'][model],latitude_deg=55.,profile=bool(profile),start=0,policy_id='reported-short-v1')
    cap,construction=limits(r,law);work={'native_calls':0,'packet_visits':0};used={k:0 for k in construction};saved={}
    def reserve(**counts):
        for k,v in counts.items():
            work[k]+=v;assert work[k]<=cap[k]
    def charge(**counts):
        for k,v in counts.items():
            used[k]+=v;assert used[k]<=construction[k]
    result=calculate(spec,r,kernel_factory=native[1],noise_kernel=native[0],reserve=reserve,
        reserve_construction=charge,save=lambda n,v:saved.update({n:v}),check_continue=lambda:None)
    assert used==construction and work['native_calls']==result['native_calls']
    checked=check_case(spec,result,saved,r=r)
    assert len(saved['fit.json']['active_parameters'])==26+profile
    assert checked['native_calls']==work['native_calls']
    assert result['evaluations']<=8 and result['original_reads']==result['protected_reads']==0


def test_controlled_turn_and_level_route_reaches_both_fit_and_scoring(native):
    from lll.coordinate_optimizer_study import case_recipe
    from lll.structured_noisy_training import calculate,limits
    from lll.airquantumgrav_observation_truth import receiver_samples
    r=dict(case_recipe(281474976810726),duration_s=2.,queries=9,
           query_start_s=.1,query_step_s=.2,maximum_evaluations=8,
           height_profile='level',route='turning')
    spec=dict(law='increment',model='sphere_rotating',latitude_deg=55.,
              profile=False,start=0,policy_id='reported-short-v1')
    cap,construction=limits(r,'increment')
    used={key:0 for key in construction};saved={}
    def reserve(**work):
        for key,value in work.items():
            assert value<=cap[key]
    def charge(**work):
        for key,value in work.items():used[key]+=value
    result=calculate(spec,r,kernel_factory=native[1],noise_kernel=native[0],
        reserve=reserve,reserve_construction=charge,
        save=lambda name,value:saved.update({name:value}),
        check_continue=lambda:None)
    assert used==construction
    assert result['training_epochs']==6
    assert 2490.<saved['input-binding.json']['gravity_anchor_height_m']<2510.
    expected=receiver_samples('sphere_rotating',saved['scores.json']['times_s'],
        latitude_deg=55.,pattern='fast',removal=0.,sign=1,
        route='turning',height_profile='level',gravity_model='inverse_square_height')
    assert saved['scoring-observations.json']['coordinates']==expected['coordinates'].tolist()
