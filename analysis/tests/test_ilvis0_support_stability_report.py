"""Saved receiver windows remain a fixed cohort in stability reporting."""

from lll.ilvis0_receiver_support import SupportPolicy, select_support
from lll.ilvis0_support_stability_report import rows_for_segment


def test_scenarios_keep_one_original_target_and_abstain_from_science():
    policy = SupportPolicy((2., 4.), 1.1, 5, 100., 300., 5., 10., 1.)
    times = tuple(float(i) for i in range(11))
    motion = dict(times_s=times, speed_mps=(200.,)*11,
                  course_deg=(10.,)*11, vertical_rate_mps=(0.,)*11)
    selected = select_support(times, motion['speed_mps'], motion['course_deg'],
                              motion['vertical_rate_mps'], target_s=5.,
                              policy=policy)
    rows = rows_for_segment('fixed-segment', motion, [selected], policy,
                            scenarios=(('zero', 0., 0., 0.),
                                       ('bounded', .1, .05, .1)))
    assert len(rows) == 2
    assert [row['scenario'] for row in rows] == ['zero', 'bounded']
    assert all(row['selected_half_window_s'] == 4. for row in rows)
    assert all(row['selected_half_window_stable'] for row in rows)
    assert all(row['scientific_decision'] == 'abstain' for row in rows)
