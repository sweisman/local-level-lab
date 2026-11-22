"""Saved noisy increments are compared with the exact clean generator."""

import numpy as np


def test_increment_difference_report_keeps_signed_accumulation():
    from lll.esa_oracle_noise_diagnostic import summarize_difference

    clean=np.zeros((4,3));noisy=np.array([[1.,0.,0.],[-.5,0.,0.],
                                         [0.,0.,0.],[.5,0.,0.]])
    result=summarize_difference(clean,noisy,np.ones(4))
    assert result['signed_total_increment'][0]==1.
    assert result['first_half_increment'][0]==.5
    assert result['second_half_increment'][0]==.5
    assert result['maximum_absolute_cumulative_increment'][0]==1.
