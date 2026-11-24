# SPDX-License-Identifier: AGPL-3.0-or-later
"""Focused sealed-input gate for the generated nonlinear replay."""

from pathlib import Path

from lll.generated_joint_replay_source import MODELS, SOURCE, verify_source


ROOT = Path(__file__).resolve().parents[2]


def test_sealed_straight_case_has_three_bound_candidates(tmp_path, monkeypatch):
    from lll.studies.closed import ClosedStudy
    from public_fixtures import isolate_frozen_source_reads

    study = ClosedStudy(ROOT, SOURCE)
    try:
        isolate_frozen_source_reads(study, tmp_path, monkeypatch)
    finally:
        study.close()
    sealed = verify_source(ROOT)
    assert tuple(sealed['candidates']) == MODELS
    assert len(sealed['training']) == 79
    assert all(len(row['fit']['active_parameters']) == 26
               for row in sealed['candidates'].values())


def test_changed_numerical_environment_is_rejected():
    try:
        verify_source(ROOT, expected_environment={'deliberately': 'wrong'})
    except ValueError as exc:
        assert 'environment' in str(exc)
    else:
        raise AssertionError('changed environment was accepted')
