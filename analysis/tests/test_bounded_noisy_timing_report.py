"""The saved timing result must remain a terminal technical diagnostic."""
import pytest


def _fixture():
    labels = ('saved_point', 'boundary_before_1ns', 'boundary_after_1ns',
              'minus_100ns', 'plus_100ns', 'minus_10us', 'plus_10us',
              'full_timing_component')
    rows = []
    for i, label in enumerate(labels):
        delta = 0. if i == 0 else float(i)
        rows.append(dict(label=label, changed_packet_epochs=79 if i % 2 else 0,
                         actual_cost=100. + delta,
                         predicted_local_cost=100. + delta,
                         actual_change_from_center=delta,
                         predicted_change_from_center=delta,
                         physical_offset_s=0. if i == 0 else -i * 1e-7))
    return rows


def test_saved_timing_summary_preserves_terminal_status_and_costs():
    from lll.bounded_noisy_timing_report import summarize
    result = summarize(_fixture())
    assert result['evaluations'] == 8
    assert result['full_timing_actual_change'] == 7.
    assert result['full_timing_predicted_change'] == 7.
    assert result['maximum_local_cost_disagreement'] == 0.
    assert result['scientific_decision'] == 'abstain'


def test_saved_timing_summary_rejects_changed_points_or_costs():
    from lll.bounded_noisy_timing_report import summarize
    rows = _fixture()
    rows[1]['label'] = 'other'
    with pytest.raises(ValueError):
        summarize(rows)
    rows = _fixture()
    rows[1]['actual_change_from_center'] += 1.
    with pytest.raises(ValueError):
        summarize(rows)
