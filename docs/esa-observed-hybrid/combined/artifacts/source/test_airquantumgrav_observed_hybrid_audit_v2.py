# SPDX-License-Identifier: AGPL-3.0-or-later
"""The publication audit accepts only the runtime's explicit engine extension."""
from pathlib import Path

import pytest


def test_hybrid_audit_binds_qualified_subset_and_frozen_engine_extension():
    from lll.airquantumgrav_observed_hybrid_audit_v2 import qualified_sources
    from lll.airquantumgrav_observed_hybrid import qualification_sources
    from lll.studies.artifacts import digest

    root = Path.cwd()
    declared = {name: digest((root / name).read_bytes())
                for name in qualification_sources(root)}
    engine = 'analysis/lll/studies/__main__.py'
    assert engine not in declared
    manifest = dict(sources=dict(declared, **{
        engine: digest((root / engine).read_bytes())}))
    request = dict(sources=declared)
    proof = qualified_sources(root, request, manifest)
    assert proof['qualified_count'] < proof['manifest_count']
    assert proof['all_frozen_source_bytes_verified']
    changed = dict(manifest, sources=dict(manifest['sources']))
    changed['sources']['analysis/lll/airquantumgrav_observed_hybrid.py'] = '0' * 64
    with pytest.raises(ValueError):
        qualified_sources(root, request, changed)


def test_hybrid_audit_rejects_unclosed_study_before_numeric_imports(tmp_path):
    from lll.airquantumgrav_observed_hybrid_audit_v2 import inspect

    with pytest.raises((FileNotFoundError, ValueError)):
        inspect(tmp_path)


def test_hybrid_public_summary_keeps_failed_pair_and_historical_baseline_separate():
    from lll.airquantumgrav_observed_hybrid_audit_v2 import render

    report = dict(verified=True, qualified=False, total=24, returned=24,
                  passed=23, errors=1,
                  historical_wide_qualified_starts=22,
                  historical_wide_deadline_failures=2,
                  rows=[dict(identity=f'case-{index}', returned=True, passed=True)
                        for index in range(23)] +
                       [dict(identity='disc-profiled-short-1', returned=True,
                             passed=False, reason='paired calculation incomplete')],
                  primary_checks=[])
    page = render(report)
    assert '23/24' in page
    assert 'did not qualify' in page
    assert 'disc-profiled-short-1' in page
    assert 'paired calculation incomplete' in page
    assert '22 earlier qualified wide starts' in page
    assert 'not an Earth-model detection' in page


def test_hybrid_public_summary_rejects_qualified_label_with_failed_pair():
    from lll.airquantumgrav_observed_hybrid_audit_v2 import render

    report = dict(verified=True, qualified=True, total=24, returned=24,
                  passed=23, errors=1,
                  historical_wide_qualified_starts=22,
                  historical_wide_deadline_failures=2,
                  rows=[dict(identity=f'case-{index}', returned=True, passed=True)
                        for index in range(23)] +
                       [dict(identity='failed-case', returned=True, passed=False)],
                  primary_checks=[])
    with pytest.raises(ValueError, match='qualified'):
        render(report)


def test_hybrid_publication_rows_keep_failed_pairs_and_measured_differences():
    from lll.airquantumgrav_observed_hybrid_audit_v2 import pair_rows

    report = dict(rows=[
        dict(identity='good', model='sphere_rotating', profile=False,
             policy_id='reported-short-v1', start=0, returned=True, passed=True,
             wide=dict(passed=True, training_cost=7., later_total_rms_m=15.),
             hybrid=dict(passed=True, training_cost=7.0001,
                         later_total_rms_m=15.0002),
             comparison=dict(passed=True, maximum_position_difference_m=.0003,
                             training_cost_difference=.0001)),
        dict(identity='unfinished', returned=True, passed=False,
             reason='evaluation ceiling'),
        dict(identity='missing', returned=False, passed=False,
             reason='no sealed result')])
    rows = pair_rows(report)
    assert [row['identity'] for row in rows] == ['good', 'unfinished', 'missing']
    assert rows[0]['model'] == 'sphere_rotating'
    assert rows[0]['policy_id'] == 'reported-short-v1'
    assert rows[0]['start'] == 0
    assert rows[0]['maximum_position_difference_m'] == .0003
    assert rows[0]['wide_later_rms_m'] == 15.
    assert rows[1]['reason'] == 'evaluation ceiling'
    assert rows[1]['maximum_position_difference_m'] is None
    assert rows[2]['returned'] is False


def test_hybrid_qualification_requires_all_distinct_primary_groups():
    from lll.airquantumgrav_observed_hybrid_audit_v2 import substitution_qualified

    rows = [dict(identity=f'case-{index}', passed=True) for index in range(24)]
    primary = [dict(model=f'model-{model}', profile=profile,
                    policy_id=f'policy-{policy}', same=True)
               for model in range(3) for profile in (False, True)
               for policy in range(2)]
    assert substitution_qualified(rows, primary, returned=24)
    assert not substitution_qualified(rows, primary[:-1], returned=24)
    assert not substitution_qualified(rows, primary[:-1] + primary[:1],
                                      returned=24)
    assert not substitution_qualified(rows, primary, returned=23)
    assert not substitution_qualified(rows[:-1] + [dict(identity='failed',
                                                        passed=False)], primary,
                                      returned=24)
