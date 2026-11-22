# SPDX-License-Identifier: AGPL-3.0-or-later

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.esa_direction_velocity_transfer import fixed_alignment_scores, identity, KEYS, SOURCES, summarize


def test_receiver_swap_preserves_the_training_alignment():
    reference = np.vstack((np.eye(3), [.4, .4, 1.]))
    rotation = Rotation.from_rotvec([.3, .1, -.2])
    measured = rotation.apply(reference)
    alternate = reference.copy()
    alternate[:3] *= -1.
    unchanged = fixed_alignment_scores(reference, measured, {'other': alternate}, training=3)
    assert unchanged['scores']['other']['rms_deg'] < 1e-12
    alternate[3] *= -1.
    changed = fixed_alignment_scores(reference, measured, {'other': alternate}, training=3)
    assert changed['scores']['other']['rms_deg'] == pytest.approx(180.)


def test_training_and_scoring_spans_use_distinct_matrix_axes():
    fixed = {}
    for width, training, field, shape in KEYS:
        scores = {}
        for index, scoring in enumerate(SOURCES):
            offset = 3*SOURCES.index(training)+index if shape == 'disc' else 0.
            scores[scoring] = dict(rms_deg=10.+offset)
        fixed[identity(width, training, field, shape)] = dict(scores=scores)
    rows = summarize(fixed)
    assert len(rows) == 6
    assert all(r['scoring_source_max_score_gap_span_deg'] == 2 for r in rows)
    assert all(r['training_source_max_score_gap_span_deg'] == 6 for r in rows)
    assert rows[0]['disc_minus_globe_deg']['R']['export'] == 6.
