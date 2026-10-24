# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    directory=tmp_path_factory.mktemp('gravity-calculation')
    return {mode:(load_kernel(directory,gravity_anchor_height_m=anchor)[0],
        load_tangent(directory,gravity_anchor_height_m=anchor)[0])
        for mode,anchor in [('constant',None),('inverse_square_height',1500.)]}


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('gravity_model',('constant','inverse_square_height'))
def test_short_known_correction_calculation_counts_all_work_and_preserves_columns(model,gravity_model,kernels):
    import numpy as np
    from lll.airquantumgrav_gravity_controls import recipe,calculate,construction_limits
    r=dict(recipe(),duration_s=2.,query_start_s=.2,query_step_s=.6,queries=3)
    saved={};native=[];construction=dict.fromkeys(construction_limits(r),0)
    def reserve_construction(**work):
        for key,value in work.items():construction[key]+=value
    value,tangent=kernels[gravity_model]
    spec=dict(model=model,latitude_deg=55.,removal=.35,gravity_model=gravity_model,height_profile='climb')
    result=calculate(spec,r,kernel=value,tangent=tangent,reserve=lambda **v:native.append(v),
        reserve_construction=reserve_construction,save=lambda name,data:saved.__setitem__(name,data),check_continue=lambda:None)
    assert result['passed'] and result['all_columns_retained'] and result['known_corrections_supplied_not_estimated']
    assert construction==construction_limits(r)
    assert len(native)==3 and sum(v['native_calls'] for v in native)==3
    assert sorted(v['native_kind'] for v in native)==['tangent','value','value']
    assert sum(v['packet_visits'] for v in native)==(600+1200+600)*3
    assert saved['tangent.json']['active_parameters'][-1]=='earth_removal'
    assert np.array(saved['tangent.json']['jacobian']).shape==(9,27)
    assert saved['answer.json']['known_not_fitted'] and result['original_reads']==result['protected_reads']==0
    assert result['scientific_decision']=='abstain'
    from lll.airquantumgrav_gravity_report import case_gate
    phases=[saved[f'rate-{hz}.json'] for hz in r['rates_hz']]
    assert case_gate(result,phases,saved['tangent.json'],saved['corrections.json'],saved['answer.json'],r)['passed']
    import copy
    changed=copy.deepcopy(phases);changed[0]['coordinates'][0][2]+=100.
    with pytest.raises(ValueError):case_gate(result,changed,saved['tangent.json'],saved['corrections.json'],saved['answer.json'],r)


def test_gravity_calculation_rejects_unknown_identity_before_native_work():
    from lll.airquantumgrav_gravity_controls import calculate,recipe
    called=[]
    with pytest.raises(ValueError):
        calculate(dict(model='unknown'),recipe(),kernel=None,tangent=None,
            reserve=lambda **v:called.append(v),reserve_construction=lambda **v:called.append(v),
            save=lambda *a:None,check_continue=lambda:None)
    assert not called
