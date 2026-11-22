import pytest


def test_quiet_bound_accounts_for_course_change_across_block_boundaries():
    from lll.esa_straight_control_windows import quiet_bound

    block = dict(span_deg=.5, signed_course_change_deg=.5)
    assert quiet_bound([block]*4) == 2.
    assert quiet_bound([dict(span_deg=.3, signed_course_change_deg=-.21), block]) == pytest.approx(.59)


def test_quiet_control_selection_excludes_complete_earlier_and_active_supports():
    from lll.esa_straight_control_windows import select_control

    segment = dict(first_index=0, last_index=3599,
                   blocks=[dict(span_deg=.2, signed_course_change_deg=.1)]*60)
    turn = dict(first_index=1660, last_index=2699, scoring_first_index=2460)
    selected = select_control(segment, turn, blocked=[(0, 400), (1660, 2699)])
    assert selected['first_index'] == 580
    assert selected['scoring_first_index'] == 1380
    assert selected['last_index'] < turn['first_index']


def test_control_query_clock_rejects_discontinuity_at_training_boundary():
    from lll.esa_straight_control_windows import query_clock

    earlier = [dict(sequence=2*i, time_s=float(i), gps_week=1234) for i in range(400)]
    later = [(2*i, float(i), 1234) for i in range(400, 520)]
    tags = query_clock(earlier, later)
    assert len(tags) == 520 and tags[400] == (800, 400., 1234)
    later[0] = (801, 400., 1234)
    with pytest.raises(ValueError, match='continuous'):
        query_clock(earlier, later)
