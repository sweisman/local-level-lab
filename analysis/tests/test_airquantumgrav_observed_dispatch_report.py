"""Decision gate for the saved model-declared ESA method comparison."""

import pytest

from lll.airquantumgrav_observed_dispatch_report import (
    assess, inspect, load_frozen_flat, load_saved_flat,
    publication_artifacts, publish, render, replay_case,
    verify_publication,
    verify_contract,
    verify_charge_totals, verify_declared_method, verify_qualified_sources,
)


def cases():
    globe = []
    flat = []
    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        for profile in (False, True):
            for policy in ('reported-short-v1', 'reported-persistent-v1'):
                for start in (0, 1):
                    row = dict(
                        identity=f'{model}-{int(profile)}-{policy}-{start}',
                        model=model, profile=profile, policy_id=policy, start=start,
                        wide_passed=True, selected_passed=True,
                        comparison_passed=True,
                        wide_training_cost=1.0 + start,
                        selected_training_cost=1.0 + start,
                    )
                    (flat if model == 'flat_still' else globe).append(row)
    # The saved flat audit includes one numerical failure, retained as such.
    flat[4]['wide_passed'] = False
    flat[4]['selected_passed'] = False
    flat[4]['comparison_passed'] = False
    return globe, flat


def test_closed_study_reader_loads_parent_proof_before_contract_gate(
        tmp_path, monkeypatch):
    from lll.studies import closed

    class IncompleteStudy:
        manifest = {}

        def close(self):
            pass

    monkeypatch.setattr(closed, 'ClosedStudy',
                        lambda root, prefix: IncompleteStudy())
    with pytest.raises(ValueError, match='expected.*v2 study contract'):
        inspect(tmp_path)


def test_all_globe_pairs_and_saved_flat_identity_qualify():
    globe, flat = cases()
    result = assess(globe, flat)
    assert result['qualified'] is True
    assert result['globe_pairs_passed'] == 16
    assert result['flat_identity_count'] == 8
    assert result['flat_numerical_failures_retained'] == 1
    assert result['primary_groups_agree'] == 8


def test_one_bad_globe_pair_blocks_qualification_without_erasing_flat_failure():
    globe, flat = cases()
    globe[0]['comparison_passed'] = False
    result = assess(globe, flat)
    assert result['qualified'] is False
    assert result['globe_pairs_passed'] == 15
    assert result['flat_numerical_failures_retained'] == 1


def test_different_primary_start_blocks_qualification():
    globe, flat = cases()
    globe[1]['selected_training_cost'] = 0.5
    result = assess(globe, flat)
    assert result['qualified'] is False
    assert result['primary_groups_agree'] == 7


def test_terminal_globe_pair_can_lack_fit_costs_and_cannot_qualify():
    globe, flat = cases()
    globe[0].update(wide_passed=False, selected_passed=False,
                    comparison_passed=False, wide_training_cost=None,
                    selected_training_cost=None)
    result = assess(globe, flat)
    assert result['qualified'] is False
    assert result['primary_groups_agree'] == 7


@pytest.mark.parametrize('mutation', (
    lambda globe, flat: globe.pop(),
    lambda globe, flat: flat.append(dict(flat[0])),
    lambda globe, flat: globe[0].update(model='flat_still'),
    lambda globe, flat: flat[0].update(selected_training_cost=2.0),
    lambda globe, flat: flat[0].update(comparison_passed=False),
))
def test_malformed_or_changed_saved_matrix_is_rejected(mutation):
    globe, flat = cases()
    mutation(globe, flat)
    with pytest.raises(ValueError):
        assess(globe, flat)


def test_saved_globe_case_replays_comparison_and_rejects_changed_verdict():
    from lll.airquantumgrav_observed_hybrid_report import compare_pair

    payload = dict(model='sphere_rotating', profile=False,
                   policy_id='reported-short-v1', start=0)
    identity = 'sphere_rotating-0-reported-short-v1-0'
    fit = dict(active_parameters=['gyro_bias_x'], residual_sum_squares=1.0)
    forecast = dict(times_s=[1.0], coordinates=[[0.5, 0.1, 100.0]],
                    prediction_receiver_positions_used=False)
    part = dict(payload, passed=True, converged=True,
                accuracy_all_sections=True, all_columns_retained=True,
                training_cost=1.0)
    comparison = compare_pair(part, part, fit, fit, forecast, forecast,
                              tolerance_m=0.01)

    class SavedCase:
        tasks = {identity: dict(payload=payload)}
        rows = {identity: dict(identity=identity)}
        result = dict(passed=True, wide=part, hybrid=part,
                      comparison=comparison, original_reads=0,
                      protected_reads=0, scientific_decision='abstain')

        def envelope(self, case):
            assert case == identity
            return dict(result=self.result, artifacts={})

        def artifact(self, case, name):
            assert case == identity
            return fit if name.endswith('-fit.json') else forecast if name.endswith(
                '-forecast.json') else comparison

    saved = SavedCase()
    row = replay_case(saved, identity)
    assert row['comparison_passed'] is True
    assert row['wide_training_cost'] == row['selected_training_cost'] == 1.0
    saved.result = dict(saved.result, comparison=dict(comparison, passed=False))
    with pytest.raises(ValueError, match='comparison'):
        replay_case(saved, identity)


def test_unsealed_case_retains_explicit_missing_result_reason():
    identity = 'sphere_still-1-reported-short-v1-0'

    class Unsealed:
        tasks = {identity: dict(payload=dict(
            model='sphere_still', profile=True,
            policy_id='reported-short-v1', start=0))}
        rows = {}

    row = replay_case(Unsealed(), identity)
    assert row['comparison_passed'] is False
    assert row['reason'] == 'no sealed result'


def test_flat_rows_require_exact_saved_audit_bytes(monkeypatch):
    import hashlib
    import json
    from lll import airquantumgrav_observed_dispatch as dispatch

    globe, flat = cases()
    selected = []
    for row in globe + flat:
        selected.append(dict(
            identity=row['identity'], model=row['model'],
            method='wide' if row['model'] == 'flat_still' else 'selective',
            numerical_passed=row['wide_passed'],
            baseline_numerical_passed=row['wide_passed'],
            training_cost=row['wide_training_cost'],
        ))
    raw = json.dumps(dict(
        matching_saved_numerical_dispositions=24,
        native_calculations=0, new_fits=0, original_reads=0,
        protected_group_reads=0, scientific_decision='abstain',
        selected=selected,
    ), sort_keys=True).encode()
    monkeypatch.setattr(dispatch, 'SAVED_AUDIT_SHA256',
                        hashlib.sha256(raw).hexdigest())
    rows = load_saved_flat(raw)
    assert len(rows) == 8
    assert sum(not row['wide_passed'] for row in rows) == 1

    class FrozenStudy:
        manifest = {'sources': {dispatch.SAVED_AUDIT:
                                hashlib.sha256(raw).hexdigest()}}
        payload = raw

        def read(self, name, expected, *, raw=False):
            assert name == 'source-freeze/' + dispatch.SAVED_AUDIT
            assert expected == self.manifest['sources'][dispatch.SAVED_AUDIT]
            assert raw is True
            return self.payload

    assert load_frozen_flat(FrozenStudy()) == rows
    with pytest.raises(ValueError, match='hash'):
        load_saved_flat(raw + b' ')


def test_current_study_contract_is_exact_and_rejects_changed_limit():
    from lll.airquantumgrav_observed_dispatch import SCOPE

    globe, _ = cases()
    manifest = dict(
        adapter='analysis/lll/airquantumgrav_observed_dispatch.py',
        scope=SCOPE, scientific_decision='abstain',
        allocation=dict(workers=4, threads=1, total=4, reserved=0),
        limits=dict(maximum_identities=16, maximum_wall_s=108000.0,
                    native_calls=6432, packet_visits=1241944115200,
                    bound_calls=0, bound_steps=0),
        tasks=[dict(identity=row['identity'], input_key='interval',
                    native_kind='tangent', limits=dict(
                        native_calls=402, packet_visits=77621507200,
                        bound_calls=0, bound_steps=0)) for row in globe],
    )
    verify_contract(manifest)
    manifest['tasks'][0]['limits']['native_calls'] += 1
    with pytest.raises(ValueError, match='limits'):
        verify_contract(manifest)


def test_report_refuses_the_sealed_earlier_path_error_as_current_study():
    with pytest.raises(ValueError, match='v2'):
        inspect('.', prefix='data/esa-observed-model-dispatch-globe-pairs')


def test_source_binding_accepts_frozen_execution_extension(tmp_path):
    import hashlib

    source = 'analysis/lll/airquantumgrav_observed_dispatch.py'
    engine = 'analysis/lll/studies/testing_after.py'
    for name, raw in ((source, b'selected method\n'),
                      (engine, b'shared runtime\n')):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    declared = {source: hashlib.sha256(b'selected method\n').hexdigest()}
    manifest = dict(declared, **{
        engine: hashlib.sha256(b'shared runtime\n').hexdigest()})
    proof = verify_qualified_sources(tmp_path, declared, manifest,
                                     expected_names={source})
    assert proof['engine_extension_count'] == 1
    with pytest.raises(ValueError):
        verify_qualified_sources(tmp_path, declared, manifest,
                                 expected_names={source, engine})


def test_compilation_metadata_must_report_predeclared_globe_method():
    from lll.ilvis0_tangent_dispatch import VERSION

    meta = dict(tangent=dict(dispatch_version=VERSION,
                             dispatch_model='sphere_still',
                             dispatch_method='selective',
                             scientific_decision='abstain'))
    verify_declared_method(meta, 'sphere_still')
    meta['tangent']['dispatch_method'] = 'wide'
    with pytest.raises(ValueError, match='method'):
        verify_declared_method(meta, 'sphere_still')


def test_journal_totals_must_equal_closed_study_charges():
    native = {'a': dict(value=0, tangent=2, packet_visits=40),
              'b': dict(value=0, tangent=3, packet_visits=60)}
    charged = dict(native_calls=5, packet_visits=100,
                   bound_calls=0, bound_steps=0)
    assert verify_charge_totals(native, charged)['native_calls'] == 5
    with pytest.raises(ValueError, match='charge'):
        verify_charge_totals(native, dict(charged, native_calls=4))


def test_public_summary_preserves_flat_failure_and_rejects_false_qualification():
    globe, flat = cases()
    report = dict(verified=True, state='complete',
                  rows=globe, flat_rows=flat,
                  **assess(globe, flat))
    page = render(report)
    assert '16/16' in page
    assert 'one saved flat numerical failure' in page
    assert 'Earth-model decision' in page
    globe[0]['comparison_passed'] = False
    with pytest.raises(ValueError, match='qualified'):
        render(report)


def test_public_summary_links_to_the_actual_frozen_plan_and_flat_audit():
    globe, flat = cases()
    report = dict(verified=True, state='complete', rows=globe, flat_rows=flat,
                  **assess(globe, flat))
    page = render(report)
    assert '(../mixed-tangent-hybrid/OBSERVED_DISPATCH_PLAN.md)' in page
    assert '(../mixed-tangent-hybrid/MODEL_DISPATCH_RESULT.md)' in page


def test_public_summary_does_not_copy_raw_worker_error_paths():
    globe, flat = cases()
    globe[0].update(comparison_passed=False,
                    reason='/home/example/private/session/token-file')
    report = dict(verified=True, state='terminal',
                  rows=globe, flat_rows=flat,
                  **assess(globe, flat))
    page = render(report)
    assert 'saved calculation did not complete' in page
    assert '/home/example' not in page


def test_public_artifacts_include_all_24_outcomes_without_worker_paths():
    import csv
    import hashlib
    import io
    import json

    globe, flat = cases()
    globe[0].update(comparison_passed=False,
                    reason='/home/example/private/session/token-file')
    report = dict(verified=True, state='terminal',
                  rows=globe, flat_rows=flat,
                  **assess(globe, flat))
    artifacts = publication_artifacts(report)
    assert set(artifacts) == {'README.md', 'pair-results.csv',
                             'verified-report.json', 'auditor-source.py'}
    rows = list(csv.DictReader(io.StringIO(
        artifacts['pair-results.csv'].decode())))
    assert len(rows) == 24
    assert sum(row['origin'] == 'saved_flat' for row in rows) == 8
    assert sum(row['origin'] == 'new_globe' for row in rows) == 16
    assert '/home/example' not in b''.join(artifacts.values()).decode()
    public = json.loads(artifacts['verified-report.json'])
    assert public['qualified'] is False
    assert public['flat_numerical_failures_retained'] == 1
    assert public['auditor_sha256'] == hashlib.sha256(
        artifacts['auditor-source.py']).hexdigest()


def test_publication_seals_and_replays_saved_only_report(tmp_path, monkeypatch):
    import json
    import lll.airquantumgrav_observed_dispatch_report as module

    globe, flat = cases()
    report = dict(verified=True, state='complete', rows=globe, flat_rows=flat,
                  manifest_sha256='m' * 64, summary_sha256='s' * 64,
                  **assess(globe, flat))
    calls = []

    def saved_inspect(root, prefix):
        calls.append(prefix)
        return report

    monkeypatch.setattr(module, 'inspect', saved_inspect)
    result = publish(tmp_path)
    assert result['cases'] == 24
    assert result['published'] == 'docs/esa-observed-model-dispatch-v2'
    assert verify_publication(tmp_path)['verified'] is True
    assert calls == ['data/esa-observed-model-dispatch-globe-pairs-v2'] * 2
    with pytest.raises(ValueError, match='already sealed'):
        publish(tmp_path)
    public = tmp_path / 'docs/esa-observed-model-dispatch-v2'
    assert json.loads((public / 'evidence-receipt.json').read_text())[
        'version'] == 'esa-dispatch-publication-v2'
    (public / 'pair-results.csv').write_text('changed\n')
    with pytest.raises(ValueError, match='published evidence changed'):
        verify_publication(tmp_path)
