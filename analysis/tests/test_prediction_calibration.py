# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import pytest

POPULATION='a'*64


def family(seed=17,role='calibration'):
    tasks={};rows=[]
    for model in ('sphere_rotating','sphere_still'):
        for start in (0,1):
            identity=f'{seed}-{model}-{start}'
            case=dict(law='increment',model=model,profile=False,start=start)
            tasks[identity]=dict(payload=dict(draw_seed=seed,role=role,case=case))
            rows.append(dict(identity=identity,draw_seed=seed,role=role,**case,
                complete=True,converged=True,accurate=True,training_cost=1.+start,
                maximum_standardized_error=10.-9*start))
    return tasks,rows


def draws(n,role='calibration',first=1000):
    return [dict(seed=first+i,role=role,population_sha256=POPULATION,maximum_score=float(i)) for i in range(n)]


def test_calibration_counts_independent_seeds_and_uses_training_cost():
    from lll.prediction_calibration import aggregate_draws
    tasks,rows=family()
    result=aggregate_draws(rows,tasks,role='calibration',population_sha256=POPULATION,excluded_seeds=[1,2])
    assert len(result)==1 and result[0]['maximum_score']==10.
    assert result[0]['available_settings']==result[0]['expected_settings']==2
    assert all(identity.endswith('-0') for identity in result[0]['selected_identities'])


@pytest.mark.parametrize('failure',['missing','numerical'])
def test_calibration_preserves_unavailable_setting_in_its_seed(failure):
    from lll.prediction_calibration import aggregate_draws
    tasks,rows=family()
    if failure=='missing':rows=rows[:2]
    else:
        for row in rows[2:]:row['converged']=False
    result=aggregate_draws(rows,tasks,role='calibration',population_sha256=POPULATION,excluded_seeds=[])
    assert len(result)==1 and result[0]['maximum_score'] is None
    assert result[0]['available_settings']==1 and result[0]['expected_settings']==2


@pytest.mark.parametrize('field,value',[('draw_seed',18),('role','validation'),('model','disc'),('start',2)])
def test_calibration_rejects_row_different_from_declared_task(field,value):
    from lll.prediction_calibration import aggregate_draws
    tasks,rows=family();rows[0][field]=value
    with pytest.raises(ValueError):aggregate_draws(rows,tasks,role='calibration',population_sha256=POPULATION,excluded_seeds=[])


def test_calibration_rejects_duplicate_rows_and_excluded_pilot_seed():
    from lll.prediction_calibration import aggregate_draws
    tasks,rows=family()
    with pytest.raises(ValueError):aggregate_draws(rows+[rows[0]],tasks,role='calibration',population_sha256=POPULATION,excluded_seeds=[])
    with pytest.raises(ValueError):aggregate_draws(rows,tasks,role='calibration',population_sha256=POPULATION,excluded_seeds=[17])


@pytest.mark.parametrize('value',[float('inf'),float('nan'),-1.,True])
def test_calibration_rejects_invalid_saved_score(value):
    from lll.prediction_calibration import aggregate_draws
    tasks,rows=family();rows[0]['maximum_standardized_error']=value
    with pytest.raises(ValueError):aggregate_draws(rows,tasks,role='calibration',population_sha256=POPULATION,excluded_seeds=[])


def test_order_statistic_probability_matches_independent_binomial_sum():
    from lll.prediction_calibration import order_statistic_plan
    for n in (3,4,6):
        result=order_statistic_plan(n,coverage=.5,confidence=.5)
        k=result['rank'];exact=sum(math.comb(n,j)*.5**n for j in range(k))
        previous=sum(math.comb(n,j)*.5**n for j in range(k-1))
        assert exact>=.5 and previous<.5
        assert result['achieved_confidence']==pytest.approx(exact)


def test_order_statistic_requires_enough_independent_draws():
    from lll.prediction_calibration import order_statistic_plan
    assert order_statistic_plan(58,coverage=.95,confidence=.95)['rank'] is None
    result=order_statistic_plan(59,coverage=.95,confidence=.95)
    assert result['rank']==59 and result['minimum_draws']==59
    assert result['achieved_confidence']==pytest.approx(1-.95**59)


@pytest.mark.parametrize('field,value',[('draws',True),('draws',0),('coverage',1.),('confidence',float('nan'))])
def test_order_statistic_rejects_invalid_design(field,value):
    from lll.prediction_calibration import order_statistic_plan
    kwargs=dict(draws=59,coverage=.95,confidence=.95);kwargs[field]=value
    with pytest.raises(ValueError):order_statistic_plan(**kwargs)


def test_calibration_selects_order_statistic_without_filtering_missing_draw():
    from lll.prediction_calibration import calibrate
    data=draws(59);data[-1]['maximum_score']=None
    result=calibrate(data,coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    assert result['draws']==59 and result['unavailable_draws']==1
    assert result['threshold'] is None and result['status']=='unavailable'
    data[-1]['maximum_score']=58.
    result=calibrate(data,coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    assert result['threshold']==58. and result['rank']==59


@pytest.mark.parametrize('change',['duplicate','role','population','excluded'])
def test_calibration_rejects_reused_or_unbound_draws(change):
    from lll.prediction_calibration import calibrate
    data=draws(59);excluded=[]
    if change=='duplicate':data[-1]['seed']=data[0]['seed']
    if change=='role':data[0]['role']='method_diagnostic_pilot'
    if change=='population':data[0]['population_sha256']='b'*64
    if change=='excluded':excluded=[data[0]['seed']]
    with pytest.raises(ValueError):calibrate(data,coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=excluded)


def test_validation_counts_seed_family_once_and_keeps_ties_inside_threshold():
    from lll.prediction_calibration import calibrate,validate
    calibration=calibrate(draws(59),coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    validation=draws(59,'validation',first=2000)
    result=validate(calibration,validation,confidence=.95,population_sha256=POPULATION)
    assert result['failures']==0 and result['draws']==59 and result['passed'] is True
    assert result['failure_upper']==pytest.approx(1-.05**(1/59))
    assert result['scientific_decision']=='abstain' and result['aircraft_coverage_established'] is False


def test_validation_counts_unavailable_draw_as_failure_and_rejects_overlap():
    from lll.prediction_calibration import calibrate,validate
    calibration=calibrate(draws(59),coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    validation=draws(59,'validation',first=2000);validation[0]['maximum_score']=None
    result=validate(calibration,validation,confidence=.95,population_sha256=POPULATION)
    assert result['failures']==1 and result['unavailable_draws']==1 and result['passed'] is False
    validation[0]['seed']=1000
    with pytest.raises(ValueError):validate(calibration,validation,confidence=.95,population_sha256=POPULATION)


def test_unsupported_calibration_cannot_pass_validation():
    from lll.prediction_calibration import calibrate,validate
    calibration=calibrate(draws(58),coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    result=validate(calibration,draws(59,'validation',first=2000),confidence=.95,population_sha256=POPULATION)
    assert result['passed'] is False and result['status']=='unavailable'


def test_validation_target_can_be_distinct_from_conservative_calibration():
    from lll.prediction_calibration import calibrate,validate
    calibration=calibrate(draws(299),coverage=.99,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    validation=draws(181,'validation',first=2000)
    for row in validation[:4]:row['maximum_score']=299.
    result=validate(calibration,validation,confidence=.95,coverage=.95,population_sha256=POPULATION)
    assert result['failures']==4 and .01<result['failure_upper']<=.05 and result['passed']
    assert result['calibration_coverage']==.99 and result['target_coverage']==.95
    assert calibration['coverage']==.99 and calibration['threshold']==298.
    original=validate(calibration,validation,confidence=.95,population_sha256=POPULATION)
    assert original['target_coverage']==.99 and original['passed'] is False


@pytest.mark.parametrize('coverage',[False,1.,float('nan')])
def test_validation_rejects_invalid_explicit_coverage(coverage):
    from lll.prediction_calibration import calibrate,validate
    calibration=calibrate(draws(59),coverage=.95,confidence=.95,population_sha256=POPULATION,excluded_seeds=[])
    with pytest.raises(ValueError):validate(calibration,draws(59,'validation',first=2000),
        confidence=.95,coverage=coverage,population_sha256=POPULATION)
