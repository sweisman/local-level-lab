"""Finite paired-receiver study adapter checks."""

import csv
import gzip
import hashlib
import io
import json

from lll.ilvis0_receiver_window_pairs_study import evaluate
from test_ilvis0_receiver_window_pairs import _policy, _rows


def _blob(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=rows[0])
    writer.writeheader()
    writer.writerows(rows)
    return gzip.compress(stream.getvalue().encode(), mtime=0)


def test_pair_study_preserves_parent_binding_and_no_imu(tmp_path):
    left, right = _blob(_rows()), _blob(_rows(spike=True))
    (tmp_path/'left').write_bytes(left)
    (tmp_path/'right').write_bytes(right)
    (tmp_path/'completion').write_text(json.dumps(
        {'manifest_sha256': 'parent-manifest',
         'summary_sha256': 'parent-summary'}))
    task = dict(identity='pair', input_key='left', left_key='left',
                right_key='right',
                left_task='left-recording', right_task='right-recording',
                left_sha256=hashlib.sha256(left).hexdigest(),
                right_sha256=hashlib.sha256(right).hexdigest(),
                parent_manifest_sha256='parent-manifest',
                parent_summary_sha256='parent-summary',
                support_policy={**_policy().__dict__,
                                'half_windows_s':[5., 10., 15.]},
                minimum_matches=10, target_spacing_s=10.,
                edge_margin_s=15.)

    class Context:
        def input_path(self, key):
            return tmp_path/('completion' if key == 'parent_completion' else key)

        def save(self, name, value):
            assert name == 'pair-window-comparison.json'
            self.saved = value
            return name

    context = Context()
    result = evaluate(task, context)
    assert result['passed'] is True
    assert result['earth_model_fits'] == 0
    assert context.saved['disagree'] >= 1
    assert context.saved['imu_observations_used'] is False
