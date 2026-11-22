"""Cross-channel contrasts preserve signs and undefined channels."""


def test_cross_channel_matrix_keeps_signed_alignment():
    import numpy as np
    from lll.esa_training_channel_dependence import (
        contrast_correlations, strongest_pair)

    base = np.array([-2., -1., 0., 1., 2.])
    rows = np.column_stack((base, -base, base**2, 3*base,
                            -2*base, np.ones(5)))
    matrix = contrast_correlations(rows)
    assert matrix[0][1] == -1.
    assert matrix[0][3] == 1.
    assert matrix[0][5] is None
    pair = strongest_pair(matrix, cross_sensor=True)
    assert pair['first_channel'].startswith('gyro_')
    assert pair['second_channel'].startswith('force_')
    assert abs(pair['correlation']) == 1.


def test_cross_channel_matrix_rejects_incomplete_or_nonfinite_input():
    import numpy as np
    import pytest
    from lll.esa_training_channel_dependence import contrast_correlations

    for values in (np.ones((2, 6)), np.ones((4, 5)),
                   np.full((4, 6), np.nan)):
        with pytest.raises(ValueError):
            contrast_correlations(values)
