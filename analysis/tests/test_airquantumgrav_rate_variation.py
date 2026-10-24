# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_rate_variation_study_has_only_one_finite_saved_training_identity():
    from lll.airquantumgrav_rate_variation import recipe,tasks
    r=recipe();matrix=tasks()
    assert len(matrix)==1 and (r['workers'],r['threads'],r['maximum_wall_s'])==(1,1,300.)
    assert r['strides']==[1,3,30,300] and r['maximum_input_samples']==360100
    assert all(v==0 for v in matrix[0]['limits'].values())
    assert r['original_reads']==r['protected_reads']==r['observed_starts']==r['native_calls']==0


def test_rate_variation_report_rejects_open_before_numerical_imports(tmp_path):
    from lll.airquantumgrav_rate_variation import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_rate_variation_bridge_uses_only_training_rates_and_charges_before_statistics():
    import numpy as np
    from lll.airquantumgrav_rate_variation import calculate,recipe
    r=recipe();t=np.arange(3600.)/300+100.
    arrays=dict(raw_time_s=t,angular_rate_rads=np.column_stack([t,t*2,t*3]),
        acceleration_mps2=np.column_stack([t*4,t*5,t*6]))
    layout=dict(training_epochs=800,prediction_epochs=400,times_s=(np.arange(1200.)*.01).tolist(),
        time_origin_gps_sow_s=100.)
    saved={};charged=[]
    def run():
        return calculate(arrays,layout,r,reserve=lambda **x:charged.append(x),save=lambda k,v:saved.__setitem__(k,v))
    answer=run();first=saved['variation.json'];arrays['angular_rate_rads'][2400:]=1e20
    second=run()
    assert first==saved['variation.json']
    assert answer==second and answer['training_samples']==2398
    assert sum(x.get('input_samples',0) for x in charged)==7200
    assert charged[0]==dict(input_samples=3600)
    assert answer['isolated_sensor_noise_estimated'] is False
    assert answer['passed'] is True and answer['scientific_decision']=='abstain'


def test_rate_variation_rejects_changed_training_layout_before_statistics():
    from lll.airquantumgrav_rate_variation import calculate,recipe
    with pytest.raises(ValueError,match='training layout'):
        calculate({},dict(training_epochs=799),recipe(),reserve=lambda **x:None,save=lambda *x:None)


@pytest.mark.parametrize('fault',['protected','source_hash','raw_count','group'])
def test_rate_variation_rejects_wrong_preparation_before_interval_read(tmp_path,fault):
    import copy
    import json
    from test_airquantumgrav_inventory import metadata
    from lll.airquantumgrav_inventory import validate_context,environment
    from lll.airquantumgrav_rate_variation import evaluate,recipe,tasks,SCOPE
    inputs=metadata();binding=validate_context(**inputs)
    source=dict(group_id='dev',raw_points=3600,references=dict(imu=dict(filename='187_rqh01.txt',sha256='a'*64)))
    parent=dict(verified=True,group_id='dev',raw_points=3600,training_epochs=800,source_references=copy.deepcopy(source['references']))
    if fault=='protected':inputs['groups']['groups'][0]['role']='protected_confirmation'
    elif fault=='source_hash':source['references']['imu']['sha256']='c'*64
    elif fault=='raw_count':source['raw_points']+=1
    else:source['group_id']='other'
    inputs.update(recipe=recipe(),context=binding,**{'qualification-environment':environment(),
        'source-validation':source,'verified-parent':parent})
    for key,value in inputs.items():(tmp_path/key).write_text(json.dumps(value))
    opened=[]
    class Context:
        manifest=dict(scope=SCOPE)
        def input_path(self,key):
            opened.append(key)
            assert key!='interval','rejected metadata must not open measurements'
            return tmp_path/key
    with pytest.raises(ValueError):evaluate(tasks()[0],Context())
    assert 'interval' not in opened
