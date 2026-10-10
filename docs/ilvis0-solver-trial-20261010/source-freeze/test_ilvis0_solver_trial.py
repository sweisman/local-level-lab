# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import json
import numpy as np
import pytest


def worker():
    return importlib.import_module('ilvis0_solver_trial')


def test_scope_is_exactly_two_stretches_three_models_two_cases():
    w = worker()
    identities = w.identities()
    assert len(identities) == len(set(identities)) == 12
    assert {i.split('::')[0] for i in identities} == {
        'b4e44ddc0f130ecd45674c78', '570b37d23af5e245dd461051'}
    assert w.MAXIMUM_STARTS == 12 and w.MAXIMUM_PER_IDENTITY == 1
    assert w.MAXIMUM_EVALUATIONS == 200


def test_each_interrupted_identity_is_charged_once_and_cannot_retry(tmp_path):
    w = worker(); path = tmp_path/'starts.jsonl'; digest = 'a'*64
    row = w.charge(path, w.identities()[0], digest)
    assert row['start'] == 1
    with pytest.raises(ValueError, match='already charged'):
        w.charge(path, w.identities()[0], digest)
    with pytest.raises(ValueError, match='identity'):
        w.charge(path, 'other', digest)
    assert len(path.read_text().splitlines()) == 1


def test_total_cap_and_manifest_mismatch(tmp_path):
    w = worker(); path = tmp_path/'starts.jsonl'; digest = 'a'*64
    for identity in w.identities():
        w.charge(path, identity, digest)
    with pytest.raises(ValueError):
        w.charge(path, w.identities()[0], digest)
    with pytest.raises(ValueError, match='journal'):
        w.journal(path, 'b'*64)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 12 and all(r['maximum_evaluations'] == 200 for r in rows)


def test_original_initialization_includes_force_gain_and_zero_removal():
    w = worker()
    class Problem:
        class bounds:
            active = ('gyro_bias_x', 'accel_gain_x', 'earth_removal')
    point = w.initial_point(Problem(), 9., dict(accel_gain_x=.15))
    assert point[0] == 0.
    assert point[1] == pytest.approx((9./9.81-1)/.15)
    assert point[2] == -1.


def test_no_rotation_comparison_for_unresolved_shape():
    w = worker()
    baseline = dict(profile=dict(conditional_shape_preference='globe', rotation_diagnostics=[]))
    new = dict(profile=dict(conditional_shape_preference='unresolved', rotation_diagnostics=None))
    compared = w.compare_stretch(baseline, new)
    assert compared['new_shape'] == 'unresolved'
    assert compared['rotation_comparison'] is None


def test_completed_publication_is_audit_only_and_cannot_refit(tmp_path):
    w = worker(); out = tmp_path/'trial'; out.mkdir()
    (out/'completion.json').write_text('{}')
    with pytest.raises(ValueError, match='completed'):
        w.run(tmp_path, out)
    assert not (out/'starts.jsonl').exists()


def test_saved_trial_can_publish_and_detect_tampered_fit_without_refitting(tmp_path):
    w = worker(); out = tmp_path/'trial'; out.mkdir(); (out/'source-freeze').mkdir()
    (out/'kernel').mkdir(); binary = out/'kernel/native-test.so'; binary.write_bytes(b'fixture')
    (out/'kernel/tangent-test.so').write_bytes(b'fixture')
    w.base.observation.gzip_json(out/'selection.json.gz', dict(selected=[]))
    build = dict(source_sha256='test', binary_sha256=w.base.il.sha256(binary))
    manifest = dict(identities=w.identities(), maximum_starts=12, maximum_per_identity=1,
        maximum_evaluations=200, solver_policy=w.solver.POLICY, sources={}, inputs={},
        environment=w.base.runtime.numerical_environment(), value_kernel=build, tangent_kernel=build,
        selection_sha256=w.base.il.sha256(out/'selection.json.gz'))
    w.base.follow.atomic_json(out/'manifest.json', manifest); digest = w.base.il.sha256(out/'manifest.json')
    results = []
    for sid in w.TARGETS:
        cases = []
        for case in w.base.primary_cases():
            fits = []
            for index, model in enumerate(w.base.explore.MODELS):
                identity = sid+'::'+case['case_id']+'::'+model
                fit = dict(model=model, converged=True, exact_projected_gradient_relative=1e-8,
                    residual_sum_squares=float(index+1), evaluations=10,
                    start_charge=w.charge(out/'starts.jsonl', identity, digest))
                w.base.save(out/(identity.replace('::','-')+'.json'), fit, digest); fits.append(fit)
            cases.append(dict(case_id=case['case_id'], fits=fits))
        result = dict(segment_id=sid, filename='sample.013', cases=cases,
                      profile=w.base.shape.hierarchical_profile(cases))
        w.base.save(out/(sid+'.json'), result, digest); results.append(result)
    summary = dict(state='complete', starts=12, results=results)
    w.base.observation.gzip_json(out/'summary.json.gz', summary)
    baseline = tmp_path/w.BASELINE; baseline.mkdir(parents=True)
    w.base.observation.gzip_json(baseline/'summary.json.gz', summary)
    w.base.follow.atomic_json(out/'completion.json', dict(state='complete', starts=12,
        manifest_sha256=digest, summary_sha256=w.base.il.sha256(out/'summary.json.gz')))
    w.publish(tmp_path, out)
    assert (tmp_path/w.GUIDE/'RESULTS.md').exists()
    assert len((out/'starts.jsonl').read_text().splitlines()) == 12
    fit_path = out/(w.identities()[0].replace('::','-')+'.json')
    value = w.base.load(fit_path); value['result']['converged'] = False
    w.base.follow.atomic_json(fit_path, value)
    with pytest.raises(ValueError, match='integrity'):
        w.publish(tmp_path, out)
