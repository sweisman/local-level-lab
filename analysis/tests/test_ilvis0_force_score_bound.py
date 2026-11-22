# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np

from lll.ilvis0_common_force_transform import ForceTransform
from lll.ilvis0_force_score_bound import bound
from lll.ilvis0_shared_reference_terms import ReferenceErrors


def test_single_yaw_force_score_encloses_known_cosine_remainder():
    sizes = np.zeros(27)
    sizes[2] = .25
    lo,hi = np.zeros(27),np.zeros(27)
    lo[2],hi[2] = -.1,.2
    reference = ReferenceErrors(dict(initial_r=np.eye(3),limits=sizes),
                                lo,hi,np.zeros(27),source_id='yaw-only')
    force = ForceTransform(reference)
    weights = np.zeros(9)
    weights[0] = force.caps[0]
    result = bound(force,weights,weights,maximum_boxes=7,maximum_seconds=20.)
    assert result['lower'] <= math.cos(.05)-1.
    assert result['upper'] >= 0.
    assert result['upper'] < .001
    assert result['covering_cells'] >= 2
