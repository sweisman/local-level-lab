"""Finite revised-tangent ESA development selection and binding checks."""
from pathlib import Path
import json

import pytest


def _layout():
    return dict(native_packets=360028, training_prefix_packets=239867,
                training_epochs=800, receiver_epochs=1200)


def test_v2_three_pair_grid_keeps_original_limits():
    from lll.airquantumgrav_observed_hybrid_v2 import FAILED, tasks
    cases = tasks(_layout())
    assert len(cases) == 3
    assert {case['identity'] for case in cases} == FAILED
    assert sum(case['limits']['native_calls'] for case in cases) == 1206
    assert sum(case['limits']['packet_visits'] for case in cases) == 232864521600


def test_v2_recipe_limits_workers_and_wall():
    from lll.airquantumgrav_observed_hybrid_v2 import recipe
    assert recipe(maximum_wall_s=14400)['workers'] == 3
    assert recipe(maximum_wall_s=14400)['threads'] == 1
    with pytest.raises(ValueError, match='four-hour'):
        recipe(maximum_wall_s=14401)


def test_v2_requires_source_bound_qualification(tmp_path):
    from lll.airquantumgrav_observed_hybrid_v2 import prepare
    with pytest.raises(ValueError, match='qualification'):
        prepare(tmp_path, qualification=None)
    assert not (tmp_path/'data').exists()


def test_v2_loader_and_sealed_source_are_explicit():
    from lll.airquantumgrav_observed_hybrid_v2 import sources
    names = set(sources(Path.cwd()))
    assert 'analysis/lll/ilvis0_hybrid_tangent_v2.py' in names
    assert 'analysis/lll/airquantumgrav_observed_hybrid_v2.py' in names
    assert 'docs/mixed-tangent-hybrid/V2_PAIRED_PLAN.md' in names


def test_v2_evaluator_injects_only_revised_loader(monkeypatch, tmp_path):
    from lll import airquantumgrav_observed_hybrid_v2 as v2
    from lll.ilvis0_hybrid_tangent_v2 import load
    proof = tmp_path/'proof.json'
    proof.write_text(json.dumps(dict(
        parent=v2.SAVED_POINT_PARENT,
        manifest_sha256=v2.SAVED_POINT_MANIFEST,
        summary_sha256=v2.SAVED_POINT_SUMMARY,
        passing_pairs=3)))
    class Context:
        manifest = {'sources': {'analysis/lll/ilvis0_hybrid_tangent_v2.py': 'hash'}}
        def input_path(self, key):
            assert key == 'v2-saved-point-proof'
            return proof
    seen = {}
    def fake(task, context, **options):
        seen.update(options)
        return {'passed': True}
    monkeypatch.setattr(v2, 'evaluate_variant', fake)
    assert v2.evaluate({'identity': 'test'}, Context()) == {'passed': True}
    assert seen['load_hybrid'] is load
    assert seen['expected_precision_revision'] == 'attitude-x-y-wide'
    assert seen['scope'] == v2.SCOPE


def test_v2_preparation_binds_saved_point_and_recovery_receipts():
    from lll.airquantumgrav_observed_hybrid_v2 import saved_point_proof
    proof = saved_point_proof(Path.cwd())
    assert set(proof) == {'v2-saved-point-proof',
                          'v2-recovery-request', 'v2-recovery-report'}
    assert json.loads(proof['v2-saved-point-proof'])['passing_pairs'] == 3


def test_v2_generated_pair_fits_share_inputs_and_forecast(tmp_path):
    """Exercise both tangent loaders through the same short native fit path."""
    import hashlib
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_hybrid_tangent_v2 import load as revised_load
    from lll.ilvis0_wide_tangent import load as wide_load
    from lll.ilvis0_wide_training import SOURCES, bind
    from lll.ilvis0_hybrid_fit_study import pair, recipe, tasks

    source = Path(__file__).resolve().parents[1]/'lll'
    hashes = {name: hashlib.sha256((source/name).read_bytes()).hexdigest()
              for name in SOURCES}
    _, calculate, _ = bind(expected_sources=hashes)
    r = dict(recipe(), duration_s=20., queries=19, maximum_evaluations=8)
    cpp = hashlib.sha256((source/'ilvis0_tangent.cpp').read_bytes()).hexdigest()
    loader = hashlib.sha256((source/'ilvis0_wide_tangent.py').read_bytes()).hexdigest()

    def factory(variant):
        def build(anchor):
            value, vm = load_kernel(tmp_path, gravity_anchor_height_m=anchor)
            if variant == 'wide':
                tangent, tm = wide_load(tmp_path, gravity_anchor_height_m=anchor,
                                        expected_source_sha256=cpp)
            else:
                tangent, tm = revised_load(tmp_path, gravity_anchor_height_m=anchor,
                                           expected_source_sha256=cpp,
                                           expected_loader_sha256=loader)
                assert tm['precision_revision'] == 'attitude-x-y-wide'
            return value, tangent, dict(value=vm, tangent=tm, variant=variant)
        return build

    saved = {}
    result = pair(tasks(r)[0]['payload'], r, calculate=calculate,
                  factories={name: factory(name) for name in ('wide', 'hybrid')},
                  reserve=lambda **_: None,
                  reserve_construction=lambda **_: None,
                  save=lambda name, value: saved.update({name: value}),
                  check_continue=lambda: None)
    assert result['comparison']['forecast_epochs'] == 19
    assert result['comparison']['maximum_prediction_difference_m'] < 1e-5
    assert saved['wide-input-binding.json'] == saved['hybrid-input-binding.json']
