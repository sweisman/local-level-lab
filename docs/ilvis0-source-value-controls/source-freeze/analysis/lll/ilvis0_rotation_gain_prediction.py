# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only prediction with qualified rotation/reciprocal-gain supports."""
from lll.ilvis0_consistent_prediction import rebuild_future


def evaluate(task,context):
    from lll.ilvis0_saved_cut_prediction import evaluate as saved_prediction
    from lll.ilvis0_rotation_gain_support import build,exact_slacks
    return saved_prediction(task,context,build=build,exact_slacks=exact_slacks,
        binding_key='rotation_gain_binding')
