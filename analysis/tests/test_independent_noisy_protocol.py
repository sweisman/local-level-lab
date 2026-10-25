# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh qualification seed through the existing real native protocol checks."""
import pytest
import test_noisy_native_protocol as legacy
from test_native_structured_training import training_kernels,native_training_case


def definition():
    value=legacy.definition()
    value['additional_sources']+=['analysis/tests/test_independent_noisy_protocol.py',
        'analysis/lll/independent_noisy_study.py','analysis/tests/test_independent_noisy_study.py',
        'analysis/lll/structured_noisy_study.py','analysis/tests/test_structured_noisy_study.py',
        'analysis/lll/prediction_scores.py','analysis/tests/test_prediction_scores.py',
        'analysis/tests/test_noise_draw_identity.py','analysis/tests/test_airquantumgrav_noisy_inputs.py',
        'docs/prediction-score-qualification/PIPELINE_PILOT.md']
    return value


@pytest.mark.parametrize('training_kernels',[pytest.param(definition(),id='independent-noisy-v1')],indirect=True)
@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[True])
def test_independent_short_native_protocol_and_score(native_training_case,monkeypatch,law,model,profile,height):
    from lll import structured_noisy_training
    from lll.airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings
    from lll.independent_noisy_study import score_records
    original_recipe=structured_noisy_training.recipe;original_calculate=structured_noisy_training.calculate
    saved={}
    def seeded_recipe():
        return dict(original_recipe(),noise_by_law=dict(increment=noise_settings(seed=26102602),
            point=rate_point_noise_settings(seed=26102602)))
    def capture(spec,r,**kwargs):
        save=kwargs['save']
        def recording(name,value):saved[name]=value;save(name,value)
        return original_calculate(spec,r,**dict(kwargs,save=recording))
    monkeypatch.setattr(structured_noisy_training,'recipe',seeded_recipe)
    monkeypatch.setattr(structured_noisy_training,'calculate',capture)
    legacy.test_complete_short_native_noisy_protocol(native_training_case,law,model,profile,height)
    score=score_records(saved,seed=26102602)
    assert score['epochs']==3 and score['confidence_calibrated'] is False
    assert score['calibration_uncertainty_included'] is False
    native_training_case['results'][-1].update(qualification_seed=26102602,prediction_score=score)
