# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np


def test_native_prefix_control_allowances_and_proof_scopes_are_fixed():
    from lll.ilvis0_native_prefix_controls import recipe,limits,make_case
    r=recipe()
    assert r['identities']==14 and r['packets']==16 and r['queries']==3
    assert r['oracle_arithmetic_allowance_m']==1e-5
    for scope in ('physical','conditioned'):
        value=make_case(0,False,scope,reserve=lambda **v:None)
        assert len(value['dt'])==16 and len(value['times'])==3
        assert np.all(np.diff(value['times'])>0.)
        assert limits(scope)['packet_steps']==48
        assert limits(scope)['lp_proposals']==(6 if scope=='conditioned' else 0)


def test_complete_control_checks_strict_runner_charges_and_full_design(kernels):
    from collections import Counter
    from native_prefix_reference import original
    from lll.ilvis0_native_prefix_controls import check,limits
    # kernels is local to the numerical prefix tests; this fixture is supplied
    # by the explicit import below to keep the compiled resources shared.
    from lll.ilvis0_shape import load_tangent
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory(prefix='lll-prefix-control-') as d:
        tangent=load_tangent(Path(d))[0];counts=Counter();charges=[];saved={}
        def reserve(**v):
            counts.update(v)
            assert all(counts[k]<=bound for k,bound in limits('physical').items())
        def charge(**v):
            assert set(v) in ({'bound_calls','bound_steps'},{'native_calls','packet_visits'})
            charges.append(v)
        result=check(0,False,'physical',original=original()[0],prefix_kernels=kernels[0],
            cold_kernels=kernels[1],tangent=tangent,reserve=reserve,charge=charge,
            save=lambda n,v:saved.update({n:v}))
    assert result['passed'] and result['complete_reports_equal'] and result['design_columns_checked']==51
    assert sum(v.get('native_calls',0) for v in charges)==3
    assert sum(v.get('bound_calls',0) for v in charges)==4
    assert result['whole_native_prefix_qualified'] is False
    assert counts['report_comparisons']==3 and counts['design_comparisons']==3


def test_existing_source_cap_failure_stays_unsupported_in_both_paths(kernels):
    from native_prefix_reference import original
    from lll.ilvis0_native_prefix_controls import check_rejection
    result=check_rejection('physical',original=original()[0],prefix_kernels=kernels[0],cold_kernels=kernels[1],
        reserve=lambda **v:None,charge=lambda **v:None,save=lambda *v:None)
    assert result['passed'] and result['baseline_unsupported'] and result['expected_rejections']==2
    assert result['native_evaluations']==0 and not result['whole_native_prefix_qualified']


def test_evaluator_runs_from_its_declared_source_freeze(tmp_path,monkeypatch):
    import json,subprocess
    from types import SimpleNamespace
    from pathlib import Path
    from lll.studies.dependencies import source_closure
    from lll.studies.artifacts import encoded,digest
    from lll.ilvis0_native_prefix_controls import recipe,limits,evaluate
    from native_prefix_reference import original
    from lll import ilvis0_control_shards as runner
    root=Path(__file__).resolve().parents[2];raw=original()[1]
    seeds=['analysis/lll/ilvis0_native_prefix_controls.py','analysis/lll/ilvis0_source_prefix_reference.cpp',
        'analysis/lll/ilvis0_source_prefix_intervals.cpp','analysis/lll/ilvis0_tangent.cpp']
    sources=source_closure(root,seeds);hashes={}
    assert 'analysis/lll/ilvis0_batched_bounds.cpp' in sources
    for name in sources:
        content=(root/name).read_bytes();hashes[name]=digest(content)
        target=tmp_path/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    (tmp_path/'manifest.json').write_bytes(encoded(dict(sources=hashes)))
    (tmp_path/'cold.py').write_bytes(raw)
    settings=dict(recipe(),cold_sha256=digest(raw),compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0])
    (tmp_path/'recipe.json').write_bytes(encoded(settings));directory=tmp_path/'artifacts/check';directory.mkdir(parents=True)
    saved={};charges=[]
    def save(name,value):
        content=encoded(value);(directory/name).write_bytes(content);saved[name]=json.loads(content)
    def charge(**values):
        assert set(values) in ({'native_calls','packet_visits'},{'bound_calls','bound_steps'})
        charges.append(values)
    # The independent framework tests cover deadlines. Here the real adapter,
    # copied source tree, compiler checks, journal and output encoder all run.
    monkeypatch.setattr(runner,'_check_continue',lambda *v:None)
    context=SimpleNamespace(root=tmp_path,manifest={'sources':hashes},directory=directory,shard=0,
        input_path=lambda key=None:tmp_path/('cold.py' if key=='cold' else 'recipe.json'),
        save=save,charge=charge,note_file=lambda path:None)
    task=dict(identity='check',payload=dict(model=0,profile=False,scope='physical',limits=limits('physical')))
    result=evaluate(task,context)
    assert result['passed'] and saved['native-prefix-checks.json']==result
    assert sum(v.get('native_calls',0) for v in charges)==3 and sum(v.get('bound_calls',0) for v in charges)==4


from test_ilvis0_native_prefix import kernels  # noqa: E402,F401
