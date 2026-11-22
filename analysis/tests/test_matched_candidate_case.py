"""All candidates must consume identical earlier measurements."""

import numpy as np
import pytest


MODELS=('sphere_rotating','sphere_still','flat_still')
NEEDED=('fit.json','forecast.json','forecast-error-diagnostic.json',
        'bounded-physical.json','bounded-receiver.json',
        'receiver-forecast-error-diagnostic.json')


def record(name):
    if name=='bounded-physical.json':
        return dict(prediction_target='physical_position',
                    later_observations_used=False,
                    nominal_joint_coverage_lower_bound=.95)
    if name=='bounded-receiver.json':
        return dict(prediction_target='receiver_measurement',
                    later_observations_used=False,
                    nominal_joint_coverage_lower_bound=.95)
    if name.endswith('forecast-error-diagnostic.json'):
        return dict(prediction_target=('receiver_measurement' if name.startswith('receiver-')
                                       else 'physical_position'),
                    later_observations_used=False)
    return dict(name=name)


def material():
    return dict(theta=np.arange(12.,dtype=float).reshape(4,3),
                dv=np.ones((4,3)),dt=np.ones(4)*.005,
                times=np.array([.001,.006,.011,.016]),
                training_rows=[dict(time_s=.001,latitude_deg=55.,height_m=1000.),
                               dict(time_s=.006,latitude_deg=55.001,height_m=1000.)])


def test_three_candidates_use_one_saved_input_before_later_truth():
    from lll.matched_candidate_case import run
    source=material();saved={};seen=[]
    def fit(model,inputs,save):
        seen.append((model,inputs['theta'].tobytes(),inputs['training_rows'][0]['latitude_deg']))
        for name in NEEDED:save(name,record(name))
        return dict(converged=True)
    def later():
        assert len(seen)==3
        assert all('candidates/'+name+'/bounded-receiver.json' in saved for name in MODELS)
        return dict(coordinates=[[1,2,3]])
    result=run(source,MODELS,fit_candidate=fit,
               save=lambda name,value:saved.setdefault(name,value),
               open_later=later)
    assert [row[0] for row in seen]==list(MODELS)
    assert len({row[1] for row in seen})==1
    assert len({row[2] for row in seen})==1
    assert result['truth']['coordinates']==[[1,2,3]]
    assert saved['input-binding.json']['same_measurements_for_all_candidates'] is True


def test_missing_bound_prevents_later_truth():
    from lll.matched_candidate_case import run
    opened=[]
    def fit(model,inputs,save):
        for name in NEEDED[:-2]:save(name,record(name))
        return {}
    with pytest.raises(ValueError,match='complete candidate artifacts'):
        run(material(),MODELS,fit_candidate=fit,save=lambda *args:None,
            open_later=lambda:opened.append(True))
    assert opened==[]


def test_candidate_mutation_blocks_later_truth():
    from lll.matched_candidate_case import run
    opened=[]
    def fit(model,inputs,save):
        inputs['training_rows'][0]['latitude_deg']+=1
        for name in NEEDED:save(name,record(name))
        return {}
    with pytest.raises(ValueError,match='measurements changed'):
        run(material(),MODELS,fit_candidate=fit,save=lambda *args:None,
            open_later=lambda:opened.append(True))
    assert opened==[]


def test_wrong_target_bound_blocks_later_truth():
    from lll.matched_candidate_case import run
    opened=[]
    def fit(model,inputs,save):
        for name in NEEDED:
            value=record(name)
            if name=='bounded-receiver.json':value['prediction_target']='physical_position'
            save(name,value)
        return {}
    with pytest.raises(ValueError,match='matched target'):
        run(material(),MODELS,fit_candidate=fit,save=lambda *args:None,
            open_later=lambda:opened.append(True))
    assert opened==[]
