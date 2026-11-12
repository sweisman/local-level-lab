"""A two-seed method gate cannot pass with a missing or failed condition."""


def test_independent_seed_gate_requires_all_48_combined_passes():
    from lll.bounded_independent_seeds_report import method_gate
    rows = [dict(identity=f'task-{i}', technical=True, numerical=True,
                 accuracy=True) for i in range(48)]
    assert method_gate(rows)
    rows[7]['numerical'] = False
    assert not method_gate(rows)
    rows[7]['numerical'] = True
    assert not method_gate(rows[:-1])


def test_expected_identity_matrix_has_no_overlap_with_original_seed():
    from lll.bounded_independent_seeds_report import expected_identities
    names = expected_identities()
    assert len(names) == 48
    assert len(set(names)) == 48
    assert all(name.startswith(('seed314159-', 'seed161803-')) for name in names)


def test_report_uses_original_view_when_no_continuation(monkeypatch, tmp_path):
    from lll import bounded_independent_seeds_report as report

    marker = object()
    monkeypatch.setattr(report, 'ClosedStudy', lambda *_a: marker)
    assert report.open_view(tmp_path) == (marker, None)


def test_report_verifies_continuation_lineage_before_combining(monkeypatch, tmp_path):
    from lll import bounded_independent_seeds_report as report
    import pytest

    (tmp_path / report.CONTINUATION).mkdir(parents=True)
    lineage = {'parent': report.STUDY, 'total': 48, 'verified': True,
               'scientific_decision': 'abstain', 'state': 'all_tasks_finished'}
    monkeypatch.setattr(report, 'inspect_lineage', lambda *_a: lineage)
    marker = object()
    monkeypatch.setattr(report, 'CombinedStudy', lambda *_a: marker)
    assert report.open_view(tmp_path) == (marker, lineage)
    lineage['parent'] = 'data/other-study'
    with pytest.raises(ValueError, match='continuation'):
        report.open_view(tmp_path)
