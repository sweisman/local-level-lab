# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import pytest

from lll import ilvis0_saved_prediction as audit


def row(index,role,north,east,up):
    return dict(epoch=str(index),time_s=str(index),role=role,north_direct_error_m=str(north),
        east_direct_error_m=str(east),up_direct_error_m=str(up))


def test_direct_errors_rms_and_fixed_sections_are_not_fit_counts():
    rows=[row(0,'training',0.,0.,0.),row(1,'prediction',3.,4.,-2.),row(2,'prediction',0.,0.,2.)]
    result=audit.summarize(rows,training_epochs=1,prediction_epochs=2,section_seconds=1.)
    assert result['prediction']['horizontal_rms_m']==math.sqrt(12.5)
    assert result['prediction']['vertical_rms_m']==2.
    assert result['prediction']['final_signed_up_m']==2.
    assert len(result['sections'])==2
    assert result['sections'][0]['count']==1 and result['scientific_decision']=='abstain'


@pytest.mark.parametrize('bad',[row(3,'prediction',0.,0.,0.),row(2,'training',0.,0.,0.),row(2,'prediction',float('nan'),0.,0.)])
def test_corrupt_grid_roles_and_nonfinite_values_are_rejected(bad):
    rows=[row(0,'training',0.,0.,0.),row(1,'prediction',0.,0.,0.),bad]
    with pytest.raises(ValueError):audit.summarize(rows,training_epochs=1,prediction_epochs=2)


def test_published_rms_mismatch_is_rejected():
    with pytest.raises(ValueError):audit.check_rms({'horizontal_rms_m':2.,'vertical_rms_m':1.},horizontal=3.,vertical=1.)
