# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def maker(law):
    from lll.airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings
    return noise_settings if law=='increment' else rate_point_noise_settings


def material(law,seed,*,duration=2.,queries=9):
    from lll.airquantumgrav_noisy_inputs import construct,construction_limits
    from lll.airquantumgrav_height_training import recipe
    r=dict(recipe(),duration_s=duration,queries=queries,query_start_s=.1,query_step_s=.2,
        noise=maker(law)(seed=seed))
    spec=dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0,policy_id='reported-short-v1')
    charges={}
    def reserve(**work):
        for key,n in work.items():charges[key]=charges.get(key,0)+n
    return construct(spec,r,reserve=reserve),charges,construction_limits(r),r,spec


@pytest.mark.parametrize('law',['increment','point'])
def test_draw_seed_changes_realization_without_changing_error_law_or_budget(law):
    import numpy as np
    from lll.airquantumgrav_noisy_inputs import error_law
    a,charges,limits,r,_=material(law,26102600)
    b,bcharges,blimits,s,_=material(law,26102601)
    assert charges==bcharges==limits==blimits
    x,y=error_law(r['noise']),error_law(s['noise'])
    assert type(x) is type(y)
    for left,right in zip(x.at(1/300),y.at(1/300)):np.testing.assert_array_equal(left,right)
    np.testing.assert_array_equal(x.initial_loading(),y.initial_loading())
    assert not np.array_equal(a['theta'],b['theta']) and not np.array_equal(a['dv'],b['dv'])
    assert a['training_rows']!=b['training_rows']
    assert a['binding']['clean_raw_array_sha256']==b['binding']['clean_raw_array_sha256']


@pytest.mark.parametrize('law',['increment','point'])
def test_new_seed_repeats_and_preserves_earlier_prefix(law):
    import numpy as np
    a,_,_,_,_=material(law,26102600)
    b,_,_,_,_=material(law,26102600)
    longer,_,_,_,_=material(law,26102600,duration=3.,queries=14)
    for key in ('theta','dv','dt'):
        np.testing.assert_array_equal(a[key],b[key]);np.testing.assert_array_equal(a[key],longer[key][:len(a[key])])
    assert a['training_rows']==b['training_rows']==longer['training_rows'][:len(a['training_rows'])]


@pytest.fixture(scope='module')
def historical():
    from pathlib import Path
    from lll.studies.closed import ClosedStudy,load_python_reference
    s=ClosedStudy(Path(__file__).resolve().parents[2],'docs/structured-noisy-training')
    try:
        name='analysis/lll/airquantumgrav_noisy_inputs.py';sha=s.manifest['sources'][name]
        return load_python_reference(s.read('source-freeze/'+name,sha,raw=True),
            name='lll._historical_noisy_generator_'+sha[:16],sha256=sha)
    finally:s.close()


@pytest.mark.parametrize('law',['increment','point'])
def test_original_seed_is_bitwise_compatible_with_frozen_generator(law,historical):
    import numpy as np
    from lll.studies.artifacts import encoded
    actual,charges,_,r,spec=material(law,26062413);reference_charges={}
    def reserve(**work):
        for k,n in work.items():reference_charges[k]=reference_charges.get(k,0)+n
    old=historical.construct(spec,r,reserve=reserve)
    for key in ('theta','dv','dt','times'):np.testing.assert_array_equal(actual[key],old[key])
    assert encoded(actual['binding'])==encoded(old['binding'])
    assert actual['training_rows']==old['training_rows'] and charges==reference_charges


@pytest.mark.parametrize('seed',[-1,2**64,True,1.5])
def test_invalid_seed_is_rejected_by_settings_before_work(seed):
    for law in ('increment','point'):
        with pytest.raises(ValueError):maker(law)(seed=seed)


@pytest.mark.parametrize('law',['increment','point'])
def test_changing_covariance_cannot_hide_as_a_new_seed(law):
    from lll.airquantumgrav_noisy_inputs import error_law
    s=maker(law)(seed=26102600)
    name='gyro_white_rads_per_sqrt_s' if law=='increment' else 'gyro_point_std_rads'
    s[name]*=2
    with pytest.raises(ValueError):error_law(s)
