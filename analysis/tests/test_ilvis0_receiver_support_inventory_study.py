"""Finite GNSS-only support inventory for preselected aircraft stretches."""

import math
from dataclasses import asdict
import csv
import gzip
import hashlib
import io
import json

from lll.ilvis0_receiver_support import SupportPolicy
from lll.ilvis0_receiver_support_inventory_study import evaluate, inventory_block


def _rows(count=41):
    radius = 6378137. + 1000.
    return [dict(gps_week='1900', gps_milliseconds=str(i*1000),
                 latitude_deg='0',
                 longitude_deg=str(math.degrees(200.*i/radius)),
                 ellipsoid_height_m='1000', velocity_north_mps='0',
                 velocity_east_mps='200', velocity_up_mps='0')
            for i in range(count)]


def _policy():
    return SupportPolicy(
        half_windows_s=(5., 10., 15.), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=190.,
        maximum_speed_mps=350., maximum_course_span_deg=1.5,
        maximum_speed_span_mps=10., maximum_vertical_rate_span_mps=1.)


def test_inventory_retains_each_receiver_only_window():
    result = inventory_block(_rows(), _policy(), target_spacing_s=10.,
                             edge_margin_s=15.)
    assert len(result['targets']) == 2
    assert result['supported_targets'] == 2
    assert all(len(row['windows']) == 3 for row in result['targets'])
    assert all(row['selected_half_window_s'] == 15.
               for row in result['targets'])
    assert result['source'] == 'primary_receiver_enhanced_position'
    assert result['scientific_decision'] == 'abstain'


def test_inventory_preserves_rejection_without_changing_policy():
    rows = _rows()
    rows[15]['velocity_east_mps'] = '120'
    result = inventory_block(rows, _policy(), target_spacing_s=10.,
                             edge_margin_s=15.)
    assert result['supported_targets'] == 1
    assert result['targets'][0]['selected_half_window_s'] is None
    assert {'low_speed'} <= {window['reason']
                             for window in result['targets'][0]['windows']}
    assert result['targets'][1]['selected_half_window_s'] == 5.


def test_study_evaluates_all_saved_blocks_and_preserves_prior_abstention(tmp_path):
    stream = io.StringIO(newline='')
    rows = _rows()
    writer = csv.DictWriter(stream, fieldnames=rows[0])
    writer.writeheader()
    writer.writerows(rows)
    blob = gzip.compress(stream.getvalue().encode(), mtime=0)
    (tmp_path/'positions.csv.gz').write_bytes(blob)
    (tmp_path/'completion.json').write_text(
        json.dumps({'manifest_sha256':'fixed-parent'}))
    segments = [dict(segment_id=str(index), filename='test.013',
                     gap_inventory_passed=True, input_key='positions',
                     table_sha256=hashlib.sha256(blob).hexdigest(),
                     first_table_row=0, last_table_row=40)
                for index in range(52)]
    segments.append(dict(segment_id='failed', filename='failed.013',
                         gap_inventory_passed=False,
                         reason='prior_receiver_decoder_failure'))
    task = dict(parent_manifest_sha256='fixed-parent',
                support_policy=asdict(_policy()),
                target_spacing_s=10., edge_margin_s=15., segments=segments)

    class Context:
        def input_path(self, key):
            return tmp_path/('completion.json' if key == 'parent_completion'
                             else 'positions.csv.gz')

        def save(self, name, value):
            assert name == 'support-windows.json'
            self.saved = value
            return name

    context = Context()
    summary = evaluate(task, context)
    assert summary['passed'] is True
    assert summary['receiver_targets'] == 104
    assert summary['supported_targets'] == 104
    assert summary['prior_decoder_abstentions'] == 1
    assert summary['earth_model_fits'] == 0
    assert len(context.saved['segments']) == 53
    assert context.saved['segments'][-1]['disposition'] == 'abstain'
