"""Finite generated-solver forecast study definition."""

from pathlib import Path
import json

from lll.studies.artifacts import digest,encoded

from lll import ilvis0_solver_forecast_study as study


def test_grid_has_exact_six_fixtures_four_starts_and_finite_charges():
    tasks=study.tasks()
    assert len(tasks)==24
    assert len({row['identity'] for row in tasks})==24
    assert {row['payload']['model'] for row in tasks}=={
        'sphere_rotating','sphere_still','flat_still'}
    assert {row['payload']['clock'] for row in tasks}=={'nominal','variable'}
    assert {row['payload']['strategy'] for row in tasks}=={'original','verified'}
    assert {row['payload']['start'] for row in tasks}=={'zero','opposed'}
    assert all(row['limits']['native_calls']==202 for row in tasks)
    assert all(row['limits']['packet_visits']==2400*(200*16+16+24)
               for row in tasks)


def test_freeze_contains_native_c_and_cpp_and_recovery_checks():
    names=study.sources(Path('.'))
    assert 'analysis/lll/ilvis0_native.c' in names
    assert 'analysis/lll/ilvis0_tangent.cpp' in names
    assert 'analysis/tests/test_ilvis0_solver_forecast_study.py' in names
    assert 'test_reboot_resume_skips_sealed_and_preserves_charges' in study.required_tests()


def test_generated_evaluator_saves_path_before_scoring_and_charges_native(tmp_path):
    policy=tmp_path/'policy'
    policy.write_bytes(encoded(study.POLICY))
    class Context:
        root=tmp_path
        shard=0
        manifest=dict(scope=study.SCOPE,sources={
            name:digest(Path(name).read_bytes()) for name in
            ('analysis/lll/ilvis0_native.c',
             'analysis/lll/ilvis0_tangent.cpp')})
        charges=[]
        saved={}
        def input_path(self):return policy
        def charge(self,**kw):self.charges.append(kw)
        def save(self,name,value):
            json.dumps(value)
            self.saved[name]=value
    context=Context()
    result=study.evaluate(study.tasks()[0],context)
    assert set(context.saved)=={'fit.json','later-path.json'}
    assert context.saved['later-path.json']['later_receiver_positions_used'] is False
    assert result['withheld_positions_used_in_fit'] is False
    assert result['evaluations']<=200
    assert sum(row['native_calls'] for row in context.charges)<=202
    assert (sum(row['packet_visits'] for row in context.charges)<=
            study.tasks()[0]['limits']['packet_visits'])
