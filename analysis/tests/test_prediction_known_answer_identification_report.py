# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.prediction_known_answer_identification_report import summarize_rows


def test_report_recounts_selected_and_abstaining_histories():
    rows = [
        dict(seed=10, classification=dict(status='provisional_minimum'),
             selected_law='reference', oracle_covered_epochs=9,
             selected_covered_epochs=9, oracle_mean_width_m=3.,
             selected_mean_width_m=3.),
        dict(seed=11, classification=dict(status='abstain'),
             selected_law=None, oracle_covered_epochs=10,
             selected_covered_epochs=None, oracle_mean_width_m=4.,
             selected_mean_width_m=None),
    ]
    result = summarize_rows(rows, truth='reference', seed_start=10,
                            seed_count=2)
    assert result['histories'] == 2
    assert result['abstain'] == 1
    assert result['truth_selected'] == 1
    assert result['wrong_selected'] == 0
    assert result['oracle_covered_epochs'] == 19
    assert result['selected_covered_epochs'] == 9
    with pytest.raises(ValueError):
        summarize_rows(rows, truth='reference', seed_start=11, seed_count=2)
