# SPDX-License-Identifier: AGPL-3.0-or-later
"""Focused controls for descriptive PPP precision ratios."""

import math

import pytest

from lll import esa_parallel_gnss_reported_precision as audit


def test_ratios_use_original_summed_axis_variance():
    reference=dict(position_variance_m2=[1., 4., 9.])
    other=dict(position_variance_m2=[3., 5., 7.])
    scaled, standard=audit.ratios(reference,other,[4., 6., 8.])
    assert standard==[2., 3., 4.]
    assert scaled==[2., 2., 2.]


@pytest.mark.parametrize('invalid', [0., -1., math.inf, math.nan])
def test_ratios_reject_invalid_reported_variance(invalid):
    with pytest.raises(ValueError,match='positive finite'):
        audit.ratios(dict(position_variance_m2=[1., invalid, 1.]),
                     dict(position_variance_m2=[1., 1., 1.]),[0., 0., 0.])


def test_saved_fast_windows_are_exhaustive_and_not_reselected(monkeypatch):
    monkeypatch.setattr(audit,'corrected_neu',lambda a,b:(None,b['adjusted']))
    reference=[dict(time_s=0.,position_variance_m2=[1.]*3),
               dict(time_s=120.,position_variance_m2=[1.]*3)]
    matched=[(0,dict(time_s=0.,position_variance_m2=[1.]*3,
                     adjusted=[2.,0.,0.])),
             (1,dict(time_s=120.,position_variance_m2=[1.]*3,
                     adjusted=[100.,0.,0.]))]
    saved=[dict(window_id=0,fast_window=True,matched_epochs=1),
           dict(window_id=1,fast_window=False,matched_epochs=1)]
    result=audit.summarize(reference,matched,saved)
    assert result['fast_windows']==1
    assert result['matched_epochs']==1
    assert result['median_absolute_ratio'][0]==pytest.approx(math.sqrt(2.))
    with pytest.raises(ValueError,match='pair counts differ'):
        audit.summarize(reference,matched[:1],[dict(saved[0],matched_epochs=2)])


def test_duplicate_and_time_mismatch_rejected(monkeypatch):
    monkeypatch.setattr(audit,'corrected_neu',lambda a,b:(None,[0.,0.,0.]))
    row=dict(time_s=0.,position_variance_m2=[1.]*3)
    other=dict(time_s=0.,position_variance_m2=[1.]*3)
    saved=[dict(window_id=0,fast_window=True,matched_epochs=1)]
    with pytest.raises(ValueError,match='unique ordered'):
        audit.summarize([row],[(0,other),(0,other)],saved)
    with pytest.raises(ValueError,match='frozen tolerance'):
        audit.summarize([row],[(0,dict(other,time_s=.01))],saved)
