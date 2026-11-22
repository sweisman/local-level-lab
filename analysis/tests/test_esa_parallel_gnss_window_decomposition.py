# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for saved PPP window mean-square decomposition."""

import pytest

from lll import esa_parallel_gnss_window_decomposition as study


def _source(*,rms=5.):
    row=dict(window_id=1,fast_window=True,matched_epochs=10,
             time_adjusted=dict(mean=[3.,3.,3.],
                                centered_rms=[4.,4.,4.],rms=[rms]*3))
    return dict(windows=[row,dict(row,window_id=2,fast_window=False)],
                fast_summary=dict(fast_windows=1,matched_epochs=10))


def test_exact_offset_fraction():
    result=study.summarize(_source())
    assert result['offset_fraction_of_relative_mean_square']==[9/25]*3
    assert result['p95_absolute_window_mean_m']==[3.]*3
    assert result['p95_within_window_centered_rms_m']==[4.]*3


def test_saved_identity_and_inventory_required():
    with pytest.raises(ValueError,match='identity'):
        study.summarize(_source(rms=6.))
    source=_source()
    source['fast_summary']['matched_epochs']=11
    with pytest.raises(ValueError,match='inventory'):
        study.summarize(source)
