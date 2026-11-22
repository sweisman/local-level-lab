"""A model-declared tangent choice cannot depend on fitted outcomes."""

import pytest


def test_dispatch_uses_only_the_declared_model():
    from lll.ilvis0_tangent_dispatch import method_for_model

    assert method_for_model('sphere_rotating') == 'selective'
    assert method_for_model('sphere_still') == 'selective'
    assert method_for_model('flat_still') == 'wide'
    with pytest.raises(ValueError, match='unsupported'):
        method_for_model('flat_rotating')


def test_saved_audit_preserves_a_failed_wide_flat_fit():
    from lll.esa_tangent_dispatch_audit import select_saved

    flat = dict(model='flat_still', wide=dict(passed=False, training_cost=7),
                hybrid=dict(passed=True, training_cost=6),
                comparison=dict(passed=False))
    selected = select_saved(flat)
    assert selected['method'] == 'wide'
    assert selected['numerical_passed'] is False
    globe = dict(model='sphere_still', wide=dict(passed=True, training_cost=7),
                 hybrid=dict(passed=True, training_cost=6),
                 comparison=dict(passed=True))
    assert select_saved(globe)['method'] == 'selective'
    globe['comparison']['passed'] = False
    with pytest.raises(ValueError, match='comparison'):
        select_saved(globe)
    globe['comparison']['passed'] = True
    globe['wide']['accuracy_all_sections'] = True
    globe['hybrid']['accuracy_all_sections'] = False
    with pytest.raises(ValueError, match='physical'):
        select_saved(globe)


def test_published_dispatch_report_preserves_smoke_test_limit(tmp_path, monkeypatch):
    from lll import esa_tangent_dispatch_audit

    monkeypatch.setattr(esa_tangent_dispatch_audit, 'build', lambda root: {
        'counts': {'selective': {'cases': 16, 'numerical_passes': 16},
                   'wide': {'cases': 8, 'numerical_passes': 7}},
    })
    esa_tangent_dispatch_audit.publish(tmp_path)
    page = (tmp_path / 'docs/mixed-tangent-hybrid/MODEL_DISPATCH_RESULT.md').read_text()
    assert 'eight-evaluation cap without meeting convergence' in page
    assert 'neither is a qualifying fit' in page


def test_loader_routes_to_exactly_one_tangent(monkeypatch):
    import hashlib
    from pathlib import Path
    from lll import ilvis0_hybrid_tangent, ilvis0_wide_tangent
    from lll.ilvis0_tangent_dispatch import load_for_model

    calls = []

    def fake_selective(directory, **kwargs):
        calls.append(('selective', directory, kwargs))
        return object(), {'method': 'selective'}

    def fake_wide(directory, **kwargs):
        calls.append(('wide', directory, kwargs))
        return object(), {'method': 'wide'}

    monkeypatch.setattr(ilvis0_hybrid_tangent, 'load', fake_selective)
    monkeypatch.setattr(ilvis0_wide_tangent, 'load', fake_wide)
    wide_sha = hashlib.sha256(Path(ilvis0_wide_tangent.__file__).read_bytes()).hexdigest()
    selective_sha = hashlib.sha256(
        Path(ilvis0_hybrid_tangent.__file__).read_bytes()).hexdigest()
    _, globe = load_for_model('sphere_rotating', 'kernels',
                              expected_source_sha256='source',
                              expected_wide_loader_sha256=wide_sha,
                              expected_selective_loader_sha256=selective_sha,
                              gravity_anchor_height_m=1000)
    _, flat = load_for_model('flat_still', 'kernels',
                             expected_source_sha256='source',
                             expected_wide_loader_sha256=wide_sha,
                             expected_selective_loader_sha256=selective_sha,
                             gravity_anchor_height_m=1000)
    assert [call[0] for call in calls] == ['selective', 'wide']
    assert calls[0][2]['expected_loader_sha256'] == wide_sha
    assert 'expected_loader_sha256' not in calls[1][2]
    assert globe['dispatch_method'] == 'selective'
    assert flat['dispatch_method'] == 'wide'
    with pytest.raises(ValueError, match='selective'):
        load_for_model('sphere_still', 'kernels',
                       expected_source_sha256='source',
                       expected_wide_loader_sha256=wide_sha,
                       expected_selective_loader_sha256='changed')


def test_real_loader_compiles_both_model_declared_methods(tmp_path):
    import hashlib
    from pathlib import Path
    from lll import ilvis0_hybrid_tangent, ilvis0_wide_tangent
    from lll.ilvis0_tangent_dispatch import load_for_model

    source = Path(ilvis0_wide_tangent.__file__).with_name('ilvis0_tangent.cpp')
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    wide_sha = hashlib.sha256(
        Path(ilvis0_wide_tangent.__file__).read_bytes()).hexdigest()
    selective_sha = hashlib.sha256(
        Path(ilvis0_hybrid_tangent.__file__).read_bytes()).hexdigest()
    _, globe = load_for_model(
        'sphere_rotating', tmp_path / 'globe',
        expected_source_sha256=source_sha,
        expected_wide_loader_sha256=wide_sha,
        expected_selective_loader_sha256=selective_sha,
        gravity_anchor_height_m=1000)
    _, flat = load_for_model(
        'flat_still', tmp_path / 'flat',
        expected_source_sha256=source_sha,
        expected_wide_loader_sha256=wide_sha,
        expected_selective_loader_sha256=selective_sha,
        gravity_anchor_height_m=1000)
    assert globe['dispatch_method'] == 'selective'
    assert globe['shared_loader_unchanged'] is True
    assert flat['dispatch_method'] == 'wide'
    assert flat['internal_mantissa_bits'] > 53


def test_paired_runner_loads_declared_candidate_without_changing_reference(tmp_path):
    import hashlib
    from pathlib import Path

    from lll.ilvis0_paired_fit_runtime import load_paired_tangent
    from lll.ilvis0_tangent_dispatch import load_for_model
    from lll import ilvis0_hybrid_tangent, ilvis0_wide_tangent

    source = Path(ilvis0_wide_tangent.__file__).with_name('ilvis0_tangent.cpp')
    args = dict(
        expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        expected_wide_loader_sha256=hashlib.sha256(
            Path(ilvis0_wide_tangent.__file__).read_bytes()).hexdigest(),
        expected_selective_loader_sha256=hashlib.sha256(
            Path(ilvis0_hybrid_tangent.__file__).read_bytes()).hexdigest(),
        gravity_anchor_height_m=1000., candidate_loader=load_for_model)
    _, reference = load_paired_tangent(
        'wide', 'sphere_rotating', tmp_path / 'reference', **args)
    _, flat = load_paired_tangent(
        'hybrid', 'flat_still', tmp_path / 'flat', **args)
    _, globe = load_paired_tangent(
        'hybrid', 'sphere_still', tmp_path / 'globe', **args)
    assert reference['internal_mantissa_bits'] > 53
    assert 'dispatch_method' not in reference
    assert flat['dispatch_method'] == 'wide'
    assert globe['dispatch_method'] == 'selective'
    with pytest.raises(ValueError, match='variant'):
        load_paired_tangent('unexpected', 'flat_still', tmp_path / 'invalid', **args)


def test_dispatched_kernels_match_wide_on_generated_models(tmp_path):
    import hashlib
    from pathlib import Path
    from lll import ilvis0_hybrid_tangent, ilvis0_wide_tangent
    from lll.ilvis0_mixed_benchmark import calculate, recipe
    from lll.ilvis0_tangent_dispatch import load_for_model

    r = dict(recipe(), duration_s=2., queries=9,
             query_start_s=.1, query_step_s=.2)
    source_sha = hashlib.sha256(Path(ilvis0_wide_tangent.__file__).with_name(
        'ilvis0_tangent.cpp').read_bytes()).hexdigest()
    wide_sha = hashlib.sha256(
        Path(ilvis0_wide_tangent.__file__).read_bytes()).hexdigest()
    selective_sha = hashlib.sha256(
        Path(ilvis0_hybrid_tangent.__file__).read_bytes()).hexdigest()
    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        for profile in (False, True):
            def kernels(anchor):
                reference, reference_meta = ilvis0_wide_tangent.load(
                    tmp_path / 'reference',
                    expected_source_sha256=source_sha,
                    gravity_anchor_height_m=anchor)
                candidate, candidate_meta = load_for_model(
                    model, tmp_path / model,
                    expected_source_sha256=source_sha,
                    expected_wide_loader_sha256=wide_sha,
                    expected_selective_loader_sha256=selective_sha,
                    gravity_anchor_height_m=anchor)
                return {'reference': reference, 'candidate': candidate}, {
                    'reference': reference_meta, 'candidate': candidate_meta}

            result = calculate(
                dict(model=model, latitude_deg=55., profile=profile, start=0),
                r, kernel_factory=kernels,
                reserve=lambda **_: None,
                reserve_construction=lambda **_: None,
                save=lambda *_: None, save_bytes=lambda *_: None,
                check_continue=lambda: None)
            assert result['checks']['values_bitwise_identical']
            assert result['checks']['differences_bitwise_identical']
            assert result['checks']['boundary_counts_identical']
            assert result['checks']['jacobian_within_tolerance']


@pytest.mark.parametrize('model,expected_method', [
    ('sphere_rotating', 'selective'),
    ('flat_still', 'wide'),
])
def test_model_dispatch_preserves_generated_fit_and_forecast(
        tmp_path, model, expected_method):
    """Exercise the model rule through the fitter, with finite generated input."""
    import hashlib
    from pathlib import Path

    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_hybrid_fit_study import pair, recipe, tasks
    from lll.ilvis0_tangent_dispatch import load_for_model
    from lll.ilvis0_wide_tangent import load as wide_load
    from lll.ilvis0_wide_training import SOURCES, bind

    source = Path(__file__).resolve().parents[1] / 'lll'
    hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
              for name in SOURCES}
    _, calculate, _ = bind(expected_sources=hashes)
    r = dict(recipe(), duration_s=20., queries=19, maximum_evaluations=8)
    spec = next(row['payload'] for row in tasks(r)
                if row['payload']['model'] == model and not row['payload']['profile'])
    cpp_sha = hashlib.sha256((source / 'ilvis0_tangent.cpp').read_bytes()).hexdigest()
    wide_sha = hashlib.sha256((source / 'ilvis0_wide_tangent.py').read_bytes()).hexdigest()
    selective_sha = hashlib.sha256(
        (source / 'ilvis0_hybrid_tangent.py').read_bytes()).hexdigest()
    methods = []

    def factory(variant):
        def build(anchor):
            value, value_meta = load_kernel(
                tmp_path / variant, gravity_anchor_height_m=anchor)
            if variant == 'wide':
                tangent, tangent_meta = wide_load(
                    tmp_path / variant, expected_source_sha256=cpp_sha,
                    gravity_anchor_height_m=anchor)
            else:
                tangent, tangent_meta = load_for_model(
                    model, tmp_path / variant, expected_source_sha256=cpp_sha,
                    expected_wide_loader_sha256=wide_sha,
                    expected_selective_loader_sha256=selective_sha,
                    gravity_anchor_height_m=anchor)
                methods.append(tangent_meta['dispatch_method'])
            return value, tangent, dict(
                value=value_meta, tangent=tangent_meta, variant=variant)
        return build

    saved = {}
    result = pair(spec, r, calculate=calculate,
                  factories={name: factory(name) for name in ('wide', 'hybrid')},
                  reserve=lambda **work: None,
                  reserve_construction=lambda **work: None,
                  save=lambda name, value: saved.update({name: value}),
                  check_continue=lambda: None)
    assert methods == [expected_method]
    assert result['reference']['converged'] == result['candidate']['converged']
    assert result['reference']['passed'] == result['candidate']['passed']
    assert result['comparison']['forecast_epochs'] == 19
    assert result['comparison']['maximum_prediction_difference_m'] < 1e-5
    assert result['comparison']['passed'] == result['comparison']['both_fits_adequate']
    assert saved['wide-input-binding.json'] == saved['hybrid-input-binding.json']
