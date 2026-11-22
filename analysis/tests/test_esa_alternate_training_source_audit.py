# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact non-position preservation in alternate training rows."""

import pytest

from lll.esa_alternate_training_source_audit import compare_rows


def _rows():
    return [dict(latitude_deg=float(i),longitude_deg=2.,height_m=3.,
                 time_s=float(i),north_mps=4.,position_variance_m2=[1.,2.,3.])
            for i in range(400)]


def test_only_coordinates_may_change():
    original=_rows()
    alternate=[dict(row,latitude_deg=row['latitude_deg']+.0001)
               for row in original]
    assert compare_rows(original,alternate)==400
    alternate[3]['north_mps']=5.
    with pytest.raises(ValueError,match='non-position'):
        compare_rows(original,alternate)


def test_every_epoch_must_be_matched_and_changed():
    original=_rows()
    with pytest.raises(ValueError,match='exact 400'):
        compare_rows(original,original[:-1])
    with pytest.raises(ValueError,match='all matched'):
        compare_rows(original,original)
