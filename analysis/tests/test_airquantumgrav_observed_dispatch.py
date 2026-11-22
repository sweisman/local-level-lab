"""The observed dispatch check must preserve the original ESA case matrix."""

import json
import hashlib
from pathlib import Path

import pytest


LAYOUT = dict(native_packets=360028, training_prefix_packets=239867,
              training_epochs=800, receiver_epochs=1200)


def test_dispatch_selects_exact_sixteen_globe_cases_and_limits():
    from lll.airquantumgrav_observed_dispatch import tasks

    cases = tasks(LAYOUT)
    assert len(cases) == 16
    assert {case['payload']['model'] for case in cases} == {
        'sphere_rotating', 'sphere_still'}
    assert sum(case['limits']['native_calls'] for case in cases) == 6432
    assert sum(case['limits']['packet_visits'] for case in cases) == 1241944115200
    assert len({case['identity'] for case in cases}) == 16


def test_dispatch_budget_is_finite_and_source_bound():
    from lll.airquantumgrav_observed_dispatch import recipe, sources, prepare

    setting = recipe(maximum_wall_s=108000)
    assert (setting['workers'], setting['threads']) == (4, 1)
    assert setting['maximum_wall_s'] == 108000
    assert setting['maximum_evaluations'] == 200
    with pytest.raises(ValueError):
        recipe(maximum_wall_s=108001)
    with pytest.raises(ValueError, match='qualification'):
        prepare(Path('/tmp/does-not-exist'), qualification=None,
                maximum_wall_s=108000)
    names = set(sources(Path.cwd()))
    assert 'analysis/lll/airquantumgrav_observed_dispatch.py' in names
    assert 'analysis/lll/ilvis0_tangent_dispatch.py' in names
    assert 'docs/mixed-tangent-hybrid/OBSERVED_DISPATCH_PLAN.md' in names
    assert 'docs/mixed-tangent-hybrid/OBSERVED_DISPATCH_RECOVERY.md' in names


def test_dispatch_loader_receives_model_before_fit(monkeypatch, tmp_path):
    from lll import airquantumgrav_observed_dispatch as candidate
    from lll import ilvis0_tangent_dispatch as dispatch

    calls = []

    def fake_load(model, directory, **kwargs):
        calls.append((model, directory, kwargs))
        return object(), {'dispatch_model': model}

    def fake_evaluate(task, context, *, load_hybrid, **kwargs):
        _, metadata = load_hybrid('kernel', expected_source_sha256='cpp',
                                  expected_loader_sha256='wide',
                                  gravity_anchor_height_m=900)
        return metadata

    monkeypatch.setattr(dispatch, 'load_for_model', fake_load)
    monkeypatch.setattr(candidate, 'evaluate_variant', fake_evaluate)
    request = tmp_path/'request.json'
    request.write_bytes(b'recovery request')
    report = tmp_path/'recovery-report.xml'
    report.write_bytes(b'<testsuite tests="5"/>')
    proof = tmp_path/'proof.json'
    proof.write_text(json.dumps(dict(
        generated_parent=candidate.GENERATED_PARENT,
        generated_manifest_sha256=candidate.GENERATED_MANIFEST,
        generated_summary_sha256=candidate.GENERATED_SUMMARY,
        saved_audit_sha256=candidate.SAVED_AUDIT_SHA256,
        generated_pairs_passed=6, flat_saved_cases=8,
        globe_saved_cases=16,
        recovery_request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),
        recovery_report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())))

    class Context:
        root = tmp_path/'data'/'study'
        manifest = {'sources': {
            'analysis/lll/ilvis0_hybrid_tangent.py': 'selective'}}

        def input_path(self, key):
            return {'dispatch-parent-proof': proof,
                    'dispatch-recovery-request': request,
                    'dispatch-recovery-report': report}[key]

    context = Context()
    result = candidate.evaluate({'payload': {'model': 'sphere_still'}}, context)
    assert result == {'dispatch_model': 'sphere_still'}
    assert calls == [('sphere_still', 'kernel', dict(
        expected_source_sha256='cpp',
        expected_wide_loader_sha256='wide',
        expected_selective_loader_sha256='selective',
        gravity_anchor_height_m=900))]
