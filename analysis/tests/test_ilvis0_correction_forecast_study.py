"""Finite, receiver-blind correction forecast development check."""

import gzip
import json
import numpy as np
import pytest


def test_three_fixed_cases_have_one_charged_forecast_each():
    from lll.ilvis0_correction_forecast_study import CASES,tasks
    layouts={identity:{'segment_id':identity.split('-')[0],
                       'native_packets':100+i,'queries':30}
             for i,identity in enumerate(CASES)}
    grid=tasks(layouts)
    assert len(grid)==3
    assert {row['identity'] for row in grid}==set(CASES)
    assert [row['limits']['native_calls'] for row in grid]==[1,1,1]
    assert [row['limits']['packet_visits'] for row in grid]==[
        (100+i)*30 for i in range(3)]


def test_path_difference_uses_predictions_only_and_checks_shape():
    from lll.ilvis0_correction_forecast_study import path_difference
    reference=np.array([[.5,-.3,1000.],[.500001,-.3,1000.],
                        [.500002,-.3,1000.]])
    candidate=reference.copy();candidate[1:,2]+=[2.,4.]
    result=path_difference(reference,candidate,training_epochs=1)
    assert result['later_epochs']==2
    assert result['rms_neu_m'][2]==pytest.approx(np.sqrt(10.))
    assert result['max_absolute_neu_m'][2]==pytest.approx(4.)
    assert result['withheld_positions_read'] is False
    with pytest.raises(ValueError):
        path_difference(reference,candidate[:2],training_epochs=1)


def test_case_staging_never_reads_scoring_positions():
    from lll.ilvis0_correction_forecast_study import CASES,stage_case
    identity=CASES[0]
    segment=identity.split('-')[0]
    class Prior:
        def __init__(self):
            self.tasks={identity:{'payload':dict(segment_id=segment,
                origin='outer',clock='header_elapsed',profile=False,start=1)}}
            self.read=[]
        def input(self,key,*,raw):
            self.read.append(key)
            assert 'scoring' not in key
            if key.endswith('-common'):
                return gzip.compress(json.dumps(dict(values=[[0]*15]*2,
                    layout=dict(native_packets=2))).encode())
            return json.dumps(dict(training_gps=[[0,0,0]],cut_epoch=1)).encode()
        def artifact(self,key,name,*,raw):
            assert key==identity
            if name=='fit.json':return b'{}'
            return json.dumps(dict(times=[0,1],training_epochs=1)).encode()
    prior=Prior()
    layout,material=stage_case(prior,identity,dict(identity=identity))
    assert prior.read==[segment+'-common',segment+'-outer-training']
    assert layout==dict(segment_id=segment,native_packets=2,queries=2)
    assert set(material)=={identity+'-'+suffix for suffix in
        ('common','training','fit','forecast','candidate')}


def test_source_closure_includes_both_native_translation_units():
    from pathlib import Path
    from lll.ilvis0_correction_forecast_study import sources
    names=set(sources(Path(__file__).resolve().parents[2]))
    assert 'analysis/lll/ilvis0_native.c' in names
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
