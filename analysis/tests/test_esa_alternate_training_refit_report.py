# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep incomplete settings abstaining and shape first."""

import pytest

from lll.esa_alternate_training_refit_report import rank_complete


def test_missing_model_abstains():
    assert rank_complete({'sphere_rotating':{'total_rms_m':1.}})['shape']=='unresolved'


def test_complete_ranking_is_shape_first():
    scores=dict(sphere_rotating=dict(total_rms_m=1.),
                sphere_still=dict(total_rms_m=2.),
                flat_still=dict(total_rms_m=3.))
    assert rank_complete(scores)==dict(shape='globe',field='specified_field',reason=None)
    scores['flat_still']['total_rms_m']=.5
    assert rank_complete(scores)==dict(shape='flat',field=None,reason=None)


def test_nonfinite_scores_rejected():
    with pytest.raises(ValueError,match='finite'):
        rank_complete(dict(sphere_rotating=dict(total_rms_m=1.),
                           sphere_still=dict(total_rms_m=float('nan')),
                           flat_still=dict(total_rms_m=2.)))
