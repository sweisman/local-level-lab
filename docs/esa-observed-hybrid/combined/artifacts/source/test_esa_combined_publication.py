# SPDX-License-Identifier: AGPL-3.0-or-later
"""A public paired-study report must retain its verification gate."""

import json
import pytest
from pathlib import Path

from lll.airquantumgrav_observed_hybrid_combined_audit import (
    SOURCES, publication_artifacts, render, verify_publication,
)
from lll.studies.artifacts import atomic, digest, encoded


_AUDIT_CASES = {
    'test_airquantumgrav_observed_hybrid_audit_v2': (
        'test_hybrid_audit_binds_qualified_subset_and_frozen_engine_extension',
        'test_hybrid_audit_rejects_unclosed_study_before_numeric_imports',
        'test_hybrid_public_summary_keeps_failed_pair_and_historical_baseline_separate',
        'test_hybrid_public_summary_rejects_qualified_label_with_failed_pair',
        'test_hybrid_publication_rows_keep_failed_pairs_and_measured_differences',
        'test_hybrid_qualification_requires_all_distinct_primary_groups',
    ),
    'test_combined_task_evidence': (
        'test_combines_original_and_recovery_without_repeating_a_failed_result',
        'test_expired_continuation_reports_unfinished_identities_without_rerunning',
        'test_attempt_cap_reports_terminal_failure_with_every_charge',
    ),
    'test_esa_combined_publication': (
        'test_public_report_requires_complete_verified_replay',
        'test_publication_contains_the_full_report_and_source_hashes',
        'test_publication_rejects_failing_test_report',
        'test_publication_rejects_missing_charged_attempt',
        'test_publication_receipt_detects_a_changed_artifact',
        'test_publication_rejects_unrelated_passing_suite',
        'test_publication_preserves_an_unfinished_pair_as_a_failed_gate',
        'test_public_report_names_forecast_equivalence_failure',
    ),
}


def _passing_test_report():
    cases = ''.join(
        f'<testcase classname="analysis.tests.{module}" name="{name}"/>'
        for module, names in _AUDIT_CASES.items() for name in names
    )
    return (f'<testsuite tests="{sum(map(len, _AUDIT_CASES.values()))}" '
            f'failures="0" errors="0" skipped="0">'
            f'{cases}</testsuite>').encode()


def _report():
    rows = [dict(identity=f'case-{index:02d}', passed=True, returned=True)
            for index in range(24)]
    checks = [dict(model=f'model-{index // 4}', profile=f'profile-{index % 4}',
                   policy_id='fixed', same=True)
              for index in range(12)]
    attempts = [dict(origin='data/parent', identity=f'case-{index:02d}',
                     status='complete', passed=True, artifact='saved/result.json',
                     artifact_sha256='a'*64,
                     charged=dict(native_calls=1, packet_visits=2,
                                  bound_calls=0, bound_steps=0))
                for index in range(24)]
    attempts += [dict(origin='data/parent', identity=f'case-{index:02d}',
                      status='interrupted', passed=False, artifact='',
                      artifact_sha256='',
                      charged=dict(native_calls=1, packet_visits=2,
                                   bound_calls=0, bound_steps=0))
                 for index in range(4)]
    return dict(verified=True, total=24, returned=24, passed=24, errors=0,
                qualified=True, rows=rows, primary_checks=checks,
                technical_interruptions=4, attempts=attempts,
                parent_study='data/parent')


def test_public_report_requires_complete_verified_replay():
    report = _report()
    page = render(report)
    assert page.startswith('# ESA paired tangent check\n\n')
    assert '24/24 paired cases passed' in page
    assert '24 passing pairs and 4 technical' in page
    assert 'technical interruptions' in page
    report['rows'][0]['passed'] = False
    with pytest.raises(ValueError, match='independently replayed'):
        render(report)


def test_publication_preserves_an_unfinished_pair_as_a_failed_gate():
    project = Path(__file__).resolve().parents[2]
    report = _report()
    report['rows'][-1].update(returned=False,passed=False,reason='no sealed result')
    report['attempts'] = [row for row in report['attempts']
                          if not (row['identity']=='case-23'
                                  and row['status']=='complete')]
    report.update(returned=23,passed=23,errors=1,qualified=False,
                  terminal_reason='deadline_exhausted',
                  pending_identities=['case-23'])
    page=render(report)
    assert '23/24 paired cases passed' in page
    assert 'case-23' in page
    materials=publication_artifacts(project,report,_passing_test_report())
    assert materials['pair-results.csv'].count(b'\n')==25
    assert b'case-23' in materials['pair-results.csv']


def test_public_report_names_forecast_equivalence_failure():
    report = _report()
    report['rows'][0].update(
        passed=False,
        comparison=dict(passed=False, same_case=True, same_times=True,
                        same_decisions=True, all_columns_retained=True,
                        later_positions_isolated=True,
                        maximum_position_difference_m=0.01671509586009743,
                        training_cost_difference=0.0001710355281829834),
    )
    report.update(passed=23, errors=1, qualified=False)
    page = render(report)
    assert '0.016715 m' in page
    assert '0.01 m' in page
    assert 'case-00' in page


def test_publication_contains_the_full_report_and_source_hashes():
    project = Path(__file__).resolve().parents[2]
    test_report = _passing_test_report()
    materials = publication_artifacts(project, _report(), test_report)
    assert set(materials) == {
        'README.md', 'pair-results.csv', 'verified-report.json',
        'source-hashes.json', 'audit-tests.xml', 'attempt-ledger.csv',
        *(f'artifacts/source/{Path(name).name}' for name in SOURCES),
    }
    assert materials['audit-tests.xml'] == test_report
    assert materials['pair-results.csv'].count(b'\n') == 25
    assert materials['attempt-ledger.csv'].count(b'\n') == 29
    import json
    hashes = json.loads(materials['source-hashes.json'])
    for name in SOURCES:
        assert hashes[name] == digest(
            materials[f'artifacts/source/{Path(name).name}'])


def test_publication_rejects_failing_test_report():
    project = Path(__file__).resolve().parents[2]
    failing = (b'<testsuite tests="4" failures="1" errors="0">'
               b'<testcase name="a"><failure/></testcase></testsuite>')
    with pytest.raises(ValueError, match='passing audit tests'):
        publication_artifacts(project, _report(), failing)


def test_publication_rejects_missing_charged_attempt():
    project = Path(__file__).resolve().parents[2]
    report = _report()
    report['attempts'].pop()
    passing = _passing_test_report()
    with pytest.raises(ValueError, match='charged-attempt ledger'):
        publication_artifacts(project, report, passing)


def test_publication_receipt_detects_a_changed_artifact(tmp_path):
    public = tmp_path/'docs/esa-observed-hybrid/combined'
    project = Path(__file__).resolve().parents[2]
    report = _report()
    report.update(original_completion_sha256='b'*64,
                  continuation_completion_sha256='c'*64,
                  combined_lineage_sha256='d'*64)
    materials=publication_artifacts(project,report,_passing_test_report())
    for name, raw in materials.items():
        atomic(public/name, raw)
    receipt=dict(
        version='esa-hybrid-combined-publication-v1',
        qualified=True,parent_completion_sha256='b'*64,
        continuation_completion_sha256='c'*64,
        combined_lineage_sha256='d'*64,
        scientific_decision='abstain', original_reads=0,
        protected_reads=0, native_calls=0,
        artifacts={name:digest(raw) for name,raw in materials.items()})
    atomic(public/'evidence-receipt.json', encoded(receipt))
    assert verify_publication(tmp_path)['verified'] is True
    atomic(public/'verified-report.json', b'changed')
    with pytest.raises(ValueError, match='published evidence changed'):
        verify_publication(tmp_path)
    atomic(public/'verified-report.json',materials['verified-report.json'])
    receipt['qualified']=False
    atomic(public/'evidence-receipt.json',encoded(receipt))
    with pytest.raises(ValueError,match='receipt differs from report'):
        verify_publication(tmp_path)
    receipt['qualified']=True
    altered=dict(json.loads(materials['source-hashes.json']))
    altered[SOURCES[0]]='0'*64
    atomic(public/'source-hashes.json',encoded(altered))
    receipt['artifacts']['source-hashes.json']=digest(encoded(altered))
    atomic(public/'evidence-receipt.json',encoded(receipt))
    with pytest.raises(ValueError,match='source hash differs'):
        verify_publication(tmp_path)
    report = _report()
    report['verified'] = False
    with pytest.raises(ValueError, match='independently replayed'):
        render(report)


def test_publication_rejects_unrelated_passing_suite():
    project = Path(__file__).resolve().parents[2]
    unrelated = _passing_test_report().replace(
        b'test_hybrid_audit_binds_qualified_subset_and_frozen_engine_extension',
        b'test_unrelated_calculation')
    with pytest.raises(ValueError, match='passing audit tests'):
        publication_artifacts(project, _report(), unrelated)
