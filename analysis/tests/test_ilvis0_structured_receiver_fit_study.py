"""Matched finite dense/structured training fits."""
import gzip
import json
from pathlib import Path

import pytest


def test_fit_tasks_share_input_and_limits_but_have_distinct_error_paths():
    from lll.ilvis0_structured_receiver_fit_study import tasks
    result=tasks(dict(packets=24049,epochs=120))
    assert [row['payload']['error_path'] for row in result]==[
        'dense','structured']
    assert {row['input_key'] for row in result}=={'training'}
    assert [row['limits']['native_calls'] for row in result]==[201,201]
    assert [row['limits']['packet_visits'] for row in result]==[
        201*24049*120]*2
    with pytest.raises(ValueError):tasks(dict(packets=24049,epochs=119))


def test_staged_material_contains_no_scoring_positions():
    from lll.ilvis0_structured_receiver_fit_study import stage_material
    class Prior:
        def __init__(self):self.keys=[]
        def input(self,key,*,raw):
            self.keys.append(key)
            assert key in ('training','layout')
            return (gzip.compress(json.dumps(dict(times=[0,1,2],
                    gps=[[0,0,0]]*3,values=[[0]*15]*3,
                    recipe={})).encode()) if key=='training' else
                    b'{"packets":3,"epochs":3}')
    prior=Prior()
    material=stage_material(prior)
    assert prior.keys==['training','layout']
    assert set(material)=={'training','layout'}


def test_fit_source_closure_includes_native_sources():
    from lll.ilvis0_structured_receiver_fit_study import sources
    names=set(sources(Path(__file__).resolve().parents[2]))
    assert 'analysis/lll/ilvis0_native.c' in names
    assert 'analysis/lll/ilvis0_tangent.cpp' in names


def test_matched_result_requires_both_stopping_checks_and_close_paths():
    from lll.ilvis0_structured_receiver_fit_study import compare_fits
    a=dict(converged=True,residual_sum_squares=1.)
    b=dict(converged=True,residual_sum_squares=1.0000001)
    first=[[.5,.1,1000.],[.5001,.1,1000.]]
    second=[[.5,.1,1000.],[.5001,.1,1000.001]]
    assert compare_fits(a,b,first,second)['passed'] is True
    assert compare_fits(a,dict(b,converged=False),first,second)['passed'] is False
    second[1][2]+=1.
    assert compare_fits(a,b,first,second)['passed'] is False
