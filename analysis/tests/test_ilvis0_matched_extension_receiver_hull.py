import pytest

from lll.ilvis0_matched_extension_receiver_hull import worst_accuracy


def test_worst_accuracy_allows_the_worst_receiver_vertex_to_change_at_each_epoch():
    reference_hull = [[[0., 0., 0.], [11., 0., 0.], [0., 0., 0.]],
                      [[11., 0., 0.], [0., 0., 0.], [0., 0., 0.]]]
    result = worst_accuracy([[0., 0., 0.], [0., 0., 0.]], reference_hull)
    assert result['worst_horizontal_rms_m'] == 11.
    assert result['worst_maximum_horizontal_m'] == 11.
    assert not result['accuracy']['passed']


def test_worst_accuracy_rejects_misaligned_support():
    with pytest.raises(ValueError, match='aligned'):
        worst_accuracy([[0., 0., 0.], [0., 0., 0.]], [[[0., 0., 0.]]])
