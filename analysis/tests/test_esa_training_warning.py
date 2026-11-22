# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_training_prefix_must_align_and_excludes_later_coordinates():
    from lll.esa_training_warning import training_input

    observed = dict(times_s=[0., 1.], coordinates=[[0., 0., 1.], [0., 0., 2.]])
    predicted = dict(times_s=[0., 1., 2.], coordinates=[[0., 0., 1.], [0., 0., 3.], [0., 0., 999.]],
                     training_epochs=2, prediction_receiver_positions_used=False)
    assert training_input(predicted, observed)['predicted'] == [[0., 0., 1.], [0., 0., 3.]]
    observed['times_s'] = [0., 1.1]
    with pytest.raises(ValueError, match='training clock'):
        training_input(predicted, observed)


def test_warning_table_retains_false_alarms_and_unavailable_results():
    from lll.esa_training_warning import contingency

    assert contingency([(False, False), (True, False), (False, True), (True, True), (None, True)]) == dict(
        pass_without_warning=1, pass_with_warning=1, failure_without_warning=1,
        failure_with_warning=1, unavailable=1)
