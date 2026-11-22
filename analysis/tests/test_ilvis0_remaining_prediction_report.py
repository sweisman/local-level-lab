"""Twenty-group saved-result accounting and abstention rules."""

import pytest
from types import SimpleNamespace

from lll import ilvis0_remaining_prediction_report as report


def _rows():
    return [dict(segment_id=f'segment-{i}',status='matched',
                 north_outer_rms_m=1.,east_outer_rms_m=2.,
                 vertical_outer_rms_m=3.,
                 outer_maximum_horizontal_m=5.,
                 outer_maximum_absolute_up_m=6.) for i in range(20)]


def test_all_twenty_selected_groups_remain_in_denominator():
    rows=_rows()
    rows[-1]['status']='abstain_both'
    assessment=report.assess(rows,dict(north=2.,east=3.,vertical=4.))
    assert assessment['groups']==20
    assert assessment['abstentions']==1
    assert assessment['transfer_within_reference']==19
    assert assessment['physical_screen_passed']==19
    assert assessment['scientific_decision']=='abstain'


def test_missing_or_duplicate_group_cannot_inflate_transfer_count():
    rows=_rows()
    with pytest.raises(ValueError):
        report.assess(rows[:-1],dict(north=2.,east=3.,vertical=4.))
    rows[-1]['segment_id']=rows[0]['segment_id']
    with pytest.raises(ValueError):
        report.assess(rows,dict(north=2.,east=3.,vertical=4.))


def test_physical_screen_is_separate_from_relative_reference():
    rows=_rows()
    rows[0]['outer_maximum_horizontal_m']=51.
    assessment=report.assess(rows,dict(north=2.,east=3.,vertical=4.))
    assert assessment['transfer_within_reference']==20
    assert assessment['physical_screen_passed']==19


def test_public_summary_keeps_scope_and_abstentions_visible():
    rows=_rows()
    rows[-1]['status']='abstain_outer'
    selection=[dict(segment_id=row['segment_id'],imu_type='21',
                    mean_latitude_deg='-62',duration_s='480') for row in rows]
    text=report.render(dict(selection=selection,rows=rows,
                            assessment=report.assess(
                                rows,dict(north=2.,east=3.,vertical=4.))))
    assert '19/20' in text
    assert '1/20' in text
    assert 'not independent confirmation' in text


def test_saved_builder_requires_exact_closed_eighty_task_study():
    parent=SimpleNamespace(
        completion=dict(state='incomplete',manifest_sha256=report.MANIFEST_SHA256),
        tasks={str(i):{} for i in range(80)},
        rows={str(i):{} for i in range(80)},
        manifest=dict(allocation=dict(total=4),
                      limits=dict(maximum_identities=80,native_calls=16080),
                      scope=report.SCOPE))
    with pytest.raises(ValueError,match='closed eighty-task'):
        report.verify_closed(parent)
    parent.completion['state']='complete'
    report.verify_closed(parent)
    parent.manifest['limits']['maximum_identities']=79
    with pytest.raises(ValueError,match='closed eighty-task'):
        report.verify_closed(parent)


def test_group_csv_joins_frozen_metadata_and_scores():
    rows=_rows()
    selection=[dict(segment_id=row['segment_id'],group_id=f'group-{i}',
                    filename=f'flight-{i}.013',mean_latitude_deg='-62',
                    duration_s='480',imu_type='21') for i,row in enumerate(rows)]
    data=report.group_csv(dict(selection=selection,rows=rows,
                               assessment=report.assess(
                                   rows,dict(north=2.,east=3.,vertical=4.))))
    import csv,io
    saved=list(csv.DictReader(io.StringIO(data.decode())))
    assert len(saved)==20
    assert saved[0]['group_id']=='group-0'
    assert saved[0]['north_outer_rms_m']=='1.0'
    assert saved[0]['transfer_within_reference']=='True'


def test_publication_requires_source_bound_qualification(tmp_path,monkeypatch):
    monkeypatch.setattr(report,'qualification_sources',lambda _:[])
    with pytest.raises(FileNotFoundError,match='remaining-report-qualification'):
        report.build(tmp_path)
