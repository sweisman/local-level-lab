# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite observed prediction definition and training-only information boundary."""
import importlib

import pytest


def library():
    return importlib.import_module('lll.ilvis0_prediction_observed')


def test_fixed_pilot_has_all_models_processing_clocks_and_starts():
    layouts=[dict(segment_id=str(i),native_packets=1000,training_epochs=60,receiver_epochs=90) for i in range(3)]
    tasks=library().tasks(layouts)
    assert len(tasks)==len({t['identity'] for t in tasks})==72
    assert sum(t['limits']['native_calls'] for t in tasks)==14472
    assert {t['payload']['clock'] for t in tasks}=={'header_elapsed','nominal_200Hz'}
    assert {t['payload']['profile'] for t in tasks}=={True,False}
    assert all(t['limits']['packet_visits']==1000*(200*60+90) for t in tasks)


@pytest.mark.parametrize('bad',[[],[dict(segment_id='a',native_packets=1000,training_epochs=60,receiver_epochs=90)]*3])
def test_task_grid_rejects_missing_or_duplicate_stretches(bad):
    with pytest.raises(ValueError):library().tasks(bad)


def test_accuracy_screen_requires_height_and_does_not_claim_calibration():
    prediction=dict(horizontal_rms_m=.01,vertical_rms_m=1000.,maximum_horizontal_m=.1,maximum_absolute_up_m=2000.)
    result=library().accuracy_screen(prediction)
    assert not result['passed'] and not result['calibrated_goodness_of_fit']
    prediction.update(vertical_rms_m=20.,maximum_absolute_up_m=100.)
    assert library().accuracy_screen(prediction)['passed']


@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1.])
def test_accuracy_screen_rejects_invalid_errors(bad):
    value=dict(horizontal_rms_m=bad,vertical_rms_m=0.,maximum_horizontal_m=0.,maximum_absolute_up_m=0.)
    with pytest.raises(ValueError):library().accuracy_screen(value)


def test_preparation_cannot_read_originals_before_complete_qualification(tmp_path):
    with pytest.raises(ValueError,match='closed study required'):
        library().prepare(tmp_path,software_report='missing.xml')
    assert not (tmp_path/'data').exists()


def test_source_freeze_includes_both_native_translation_units():
    from pathlib import Path
    sources=library().sources(Path(__file__).resolve().parents[2])
    assert {'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp'}<=set(sources)


def test_frozen_loader_compiles_without_access_to_live_library(tmp_path):
    import importlib.util
    from pathlib import Path
    import shutil
    root=Path(__file__).resolve().parents[2];declared=set(library().sources(root))
    for basename in ('ilvis0_exploratory.py','ilvis0_shape.py','ilvis0_native.c','ilvis0_tangent.cpp'):
        name='analysis/lll/'+basename
        assert name in declared
        shutil.copyfile(root/name,tmp_path/basename)
    for module_name,filename,function in [('value','ilvis0_exploratory.py','load_kernel'),
                                          ('tangent','ilvis0_shape.py','load_tangent')]:
        spec=importlib.util.spec_from_file_location('lll._pilot_'+module_name,tmp_path/filename)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        loaded,metadata=getattr(module,function)(tmp_path/'kernels')
        assert loaded is not None and metadata['source_sha256']


def test_evaluator_saves_forecast_before_opening_later_positions(tmp_path,monkeypatch):
    import gzip
    import json
    from types import SimpleNamespace
    import numpy as np
    from lll import ilvis0_exploratory as explore,ilvis0_shape as shape
    from lll import ilvis0_training_forecast as training,ilvis0_forecast as forward
    from lll.studies.artifacts import encoded
    module=library();n=4800;times=np.arange(1.,24.);cut=15
    values=np.zeros((n,15));values[:,2]=.005
    material=dict(segment_id='test',layout=dict(training_epochs=cut,receiver_epochs=23,native_packets=n),
        values=values.tolist(),times=times.tolist(),training_gps=np.zeros((cut,3)).tolist())
    paths={}
    for key,raw in [('recipe',encoded(module.recipe())),
                    ('measurements',gzip.compress(encoded(material),mtime=0)),
                    ('test-scoring',encoded(dict(segment_id='test',prediction_gps=np.zeros((8,3)).tolist())))]:
        p=tmp_path/key;p.write_bytes(raw);paths[key]=p
    history=[];saved={};captured=[]
    def input_path(key=None):
        if key=='test-scoring':assert 'forecast.json' in saved
        history.append(key);return paths['measurements' if key is None else key]
    def build(t,g,**kw):
        assert 'test-scoring' not in history and np.array_equal(g,np.zeros((cut,3)))
        assert len(t)==cut and len(kw['theta'])<n
        captured.append(g.copy());return SimpleNamespace(bounds=SimpleNamespace(active=list(range(26))))
    def fit(*args,**kwargs):
        assert 'test-scoring' not in history
        return dict(converged=True,normalized_parameters=[0.]*26,residual_sum_squares=1.,evaluations=2)
    def forecast(*args,**kwargs):
        assert 'test-scoring' not in history and len(kwargs['theta'])==n
        return dict(coordinates=np.zeros((23,3)),active_parameters=list(range(26)))
    meta=dict(source_sha256='sha')
    monkeypatch.setattr(explore,'load_kernel',lambda directory:(None,meta))
    monkeypatch.setattr(shape,'load_tangent',lambda directory:(None,meta))
    monkeypatch.setattr(training,'training_problem',build);monkeypatch.setattr(training,'fit_training',fit)
    monkeypatch.setattr(forward,'native_forecast',forecast)
    context=SimpleNamespace(root=tmp_path,shard=0,input_path=input_path,
        save=lambda name,value:saved.update({name:value}),charge=lambda **kwargs:None,
        manifest=dict(sources={'analysis/lll/ilvis0_native.c':'sha','analysis/lll/ilvis0_tangent.cpp':'sha'}))
    task=dict(payload=dict(segment_id='test',model=0,profile=False,clock='nominal_200Hz',start=0))
    first=module.evaluate(task,context)
    assert first['passed'] and first['accuracy_screen']['passed']
    before=encoded(saved['forecast.json']);history.clear();saved.clear()
    paths['test-scoring'].write_bytes(encoded(dict(segment_id='test',prediction_gps=np.ones((8,3)).tolist())))
    second=module.evaluate(task,context)
    assert encoded(saved['forecast.json'])==before and second['training_cost']==first['training_cost']
    assert np.array_equal(*captured) and not second['accuracy_screen']['passed']
