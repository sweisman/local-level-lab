# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.ilvis0_distance_inventory_audit import summarize


def test_overlapping_screen_flags_keep_separate_file_and_sample_counts():
    result=summarize([
        dict(state='no_qualifying_segment',rejections=dict(
            incomplete_alignment=10,excessive_course_rate=7,
            short_after_buffers_or_raw_intersection=2)),
        dict(state='segments_available',rejections=dict(incomplete_alignment=3)),
        dict(state='no_qualifying_segment',rejections={})])
    rows={row['reason']:row for row in result['rows']}
    assert result['states']=={'no_qualifying_segment':2,'segments_available':1}
    assert rows['incomplete_alignment']['tally']==13
    assert rows['incomplete_alignment']['files_with_flag']==2
    assert rows['short_after_buffers_or_raw_intersection']['phase']=='candidate spans'
    assert result['counts_overlap'] and not result['unique_causes_identified']
