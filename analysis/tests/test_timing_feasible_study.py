# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib


def test_feasible_optimizer_uses_fresh_identity_and_exact_shared_control_matrix():
    from lll import timing_stopping_local_study as old
    m=importlib.import_module('lll.timing_feasible_study');cfg=m.configuration()
    assert m.IDENTITY!=old.IDENTITY and m.case_table()==old.case_table()
    assert cfg['maximum_fits']==36 and cfg['maximum_analytical_evaluations']==7488
    assert cfg['maximum_linear_solves']==22500 and cfg['maximum_wall_s']==600.
    assert len(m.tasks())==44
    assert all(t['limits']['native_calls']==0 and t['limits']['packet_visits']==0 for t in m.tasks())


def test_feasible_optimizer_binds_correction_controls_and_all_qualification_tests():
    from pathlib import Path
    m=importlib.import_module('lll.timing_feasible_study')
    names=m.sources(Path(__file__).resolve().parents[2])
    assert set(m.TESTS)<=set(names)
    assert 'analysis/lll/timing_cells.py' in names and m.PLAN in names and m.ADAPTER in names
