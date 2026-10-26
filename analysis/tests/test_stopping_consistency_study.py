# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap guards for the finite saved-point study; no aircraft/native execution."""
import importlib
from pathlib import Path

import pytest


def module():
    return importlib.import_module('lll.stopping_consistency_study')


@pytest.mark.parametrize('case',['source','environment','column_order','replay',
    'nonlinear_fit','protected_seed','duplicate_charge'])
def test_study_guards(case,tmp_path):
    m=module()
    if case in ('source','environment'):
        from lll.studies.artifacts import digest
        p=tmp_path/'source.py';p.write_text('original')
        sources={'source.py':digest(p.read_bytes())}
        env={'version':'same'}
        if case=='source':p.write_text('changed')
        with pytest.raises(ValueError):
            m.verify_bindings(tmp_path,sources,env,{'version':'changed'} if case=='environment' else env)
    elif case=='column_order':
        with pytest.raises(ValueError):m.verify_replay(['b','a'],['a','b'],2.,2.)
    elif case=='replay':
        with pytest.raises(ValueError):m.verify_replay(['a','b'],['a','b'],2.,2.001)
    elif case=='protected_seed':
        with pytest.raises(ValueError):m.point_identity(281474976910656,False,0)
    elif case=='nonlinear_fit':
        with pytest.raises(RuntimeError,match='nonlinear'):
            m.no_nonlinear_fit()
    else:
        from lll.studies.journal import Journal
        j=Journal(tmp_path/'charges.sqlite',freeze='a'*64,limits={'point':{'evaluations':170}})
        j.start('point')
        with pytest.raises(ValueError):j.start('point')


def test_selection_has_only_four_exposed_points():
    m=module()
    assert len(m.POINTS)==4
    assert len({m.point_identity(*p) for p in m.POINTS})==4
    assert {(seed,profile,start) for seed,profile,start in m.POINTS}=={
        (281474976810725,False,0),(281474976810726,False,0),
        (281474976810726,False,1),(281474976810726,True,0)}


def test_report_keeps_failed_probe_and_derivative_discrepancy():
    report=importlib.import_module('lll.stopping_consistency_report')
    row=report.summarize(dict(identity='one',saved_converged=False),dict(
        columns=1,evaluations=10,cost=2.,repeatability={'exact':True},
        singular_value_ratio=1e-9,stopping_probe={'passed':False,'actual_cost_change':1e-6},
        signed_probe={'actual_cost_delta':1e-5,'predicted_cost_delta':-1e-5},
        derivatives=[{'column':0,'steps':[{'step':1e-5,'error_norm':1.,
            'analytic_norm':2.,'difference_norm':3.}]}]))
    assert row['derivative_checks_passed'] is False
    assert row['probe_passed'] is False
    assert row['saved_converged'] is False


def test_capture_binding_exits_before_any_fit_or_forecast():
    from lll.studies.protocols import bind_function
    from lll.studies.artifacts import digest
    source=(Path(__file__).resolve().parents[1]/'lll/airquantumgrav_prediction.py').read_bytes()
    def capture(*a,**k):raise module().Captured({'intercepted':True})
    bound,proof=bind_function(source,expected_sha256=digest(source),function='train_and_forecast',
        import_module='lll.ilvis0_training_forecast',import_name='fit_training',provider=capture,
        provider_source_sha256=digest(Path(module().__file__).read_bytes()),namespace={'math':__import__('math')})
    assert bound.__code__.co_name=='train_and_forecast'
    assert proof['substitutions']==1
    # A reduced protocol exercises the same binding mechanism end to end;
    # anything after the capture must remain unreachable.
    reduced=b'def protocol():\n from lll.ilvis0_training_forecast import fit_training\n fit_training()\n raise AssertionError("forecast reached")\n'
    entry,_=bind_function(reduced,expected_sha256=digest(reduced),function='protocol',
        import_module='lll.ilvis0_training_forecast',import_name='fit_training',provider=capture,
        provider_source_sha256=digest(Path(module().__file__).read_bytes()),namespace={})
    with pytest.raises(module().Captured) as caught: entry()
    assert caught.value.report=={'intercepted':True}


def test_real_frozen_entrypoint_checks_environment_before_native(tmp_path):
    import importlib.util
    from types import SimpleNamespace
    source=Path(module().__file__)
    spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',source)
    frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
    path=tmp_path/'environment.json';path.write_text('{"changed":true}')
    context=SimpleNamespace(root=tmp_path,manifest={'sources':{}},input_path=lambda key:path)
    with pytest.raises(ValueError,match='environment changed'):
        frozen.evaluate({},context)
