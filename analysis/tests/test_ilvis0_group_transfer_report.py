"""Transfer reporting counts every preselected group and preserves abstentions."""
import pytest


REFERENCE = {'north': 5., 'east': 20., 'vertical': 11.}


def _row(segment, *, status='matched', north=3., east=4., height=5.,
         maximum_horizontal=6., maximum_up=7.):
    return dict(segment_id=segment, status=status,
                north_outer_rms_m=north if status == 'matched' else None,
                east_outer_rms_m=east if status == 'matched' else None,
                vertical_outer_rms_m=height if status == 'matched' else None,
                outer_maximum_horizontal_m=maximum_horizontal if status == 'matched' else None,
                outer_maximum_absolute_up_m=maximum_up if status == 'matched' else None)


def test_all_four_groups_remain_in_denominator_and_adequacy_is_separate():
    from lll.ilvis0_group_transfer_report import assess_transfer
    rows = [_row('a'), _row('b', north=6.),
            _row('c', status='abstain_outer'),
            _row('d', maximum_up=200.)]
    result = assess_transfer(rows, REFERENCE)
    assert result['groups'] == 4
    assert result['transfer_within_reference'] == 2
    assert result['physical_screen_passed'] == 2
    assert result['abstentions'] == 1
    assert result['scientific_decision'] == 'abstain'
    assert result['coverage_calibrated'] is False


def test_no_missing_or_duplicate_group_can_inflate_transfer_fraction():
    from lll.ilvis0_group_transfer_report import assess_transfer
    with pytest.raises(ValueError):
        assess_transfer([_row('a')] * 4, REFERENCE)
    with pytest.raises(ValueError):
        assess_transfer([_row('a'), _row('b'), _row('c')], REFERENCE)


def test_qualified_row_needs_all_axes_and_maxima():
    from lll.ilvis0_group_transfer_report import assess_transfer
    for bad in (None, float('nan'), -1.):
        rows = [_row('a'), _row('b'), _row('c'), _row('d')]
        rows[0]['north_outer_rms_m'] = bad
        with pytest.raises(ValueError):
            assess_transfer(rows, REFERENCE)


def test_missing_first_cut_does_not_hide_available_second_cut():
    from lll.ilvis0_group_transfer_report import assess_transfer
    rows = [_row('a'), _row('b'), _row('c'), _row('d')]
    rows[0]['status'] = 'abstain_inner'
    result = assess_transfer(rows, REFERENCE)
    assert result['groups'] == 4
    assert result['abstentions'] == 0
    assert result['transfer_within_reference'] == 4


def test_render_keeps_stopping_and_coverage_limits_visible():
    from lll.ilvis0_group_transfer_report import assess_transfer, render
    rows = [_row(name) for name in 'abcd']
    selection = [dict(segment_id=name, imu_type='21',
                      mean_latitude_deg='-63', duration_s='600')
                 for name in 'abcd']
    result = dict(tasks=16, selection=selection, rows=rows,
                  assessment=assess_transfer(rows, REFERENCE),
                  scientific_decision='abstain')
    page = render(result)
    assert '4/4 groups' in page
    assert 'not a confidence interval' in page
    assert 'gyroscope channel’s separate contribution' in page


def test_publication_rejects_incomplete_parent(monkeypatch):
    from lll import ilvis0_group_transfer_report as report
    import lll.studies.closed as closed
    import lll.studies.qualification as qualification
    class Running:
        completion = {'state': 'running'}
        def close(self):
            pass
    monkeypatch.setattr(report, 'qualification_sources', lambda root: [])
    monkeypatch.setattr(qualification, 'checked', lambda *args, **kwargs: (b'', b''))
    monkeypatch.setattr(closed, 'ClosedStudy', lambda *args: Running())
    with pytest.raises(ValueError, match='complete exact four-group study'):
        report.build('.')
