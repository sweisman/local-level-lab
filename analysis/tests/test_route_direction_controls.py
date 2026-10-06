# SPDX-License-Identifier: AGPL-3.0-or-later
"""Time-reversed motion must preserve the path and reverse all signed derivatives."""
import numpy as np
import pytest

from screen_route_directions import reverse_motion


def test_reverse_motion_preserves_support_and_changes_velocity_direction():
    t=np.arange(5.); course=np.array([0.,.3,np.nan,.6,.9])
    kin=dict(t=t,lat=t+.1,lon=t+.2,h=t+10000.,v_n=t+1.,v_e=t-7.,vz=t-2.,psi=course,
             psi_dot=t*.01,speed=np.hypot(t+1.,t-7.),bearing_ok=np.isfinite(course))
    reversed_kin=reverse_motion(kin)
    np.testing.assert_array_equal(reversed_kin['t'],t)
    for key in ('lat','lon','h','speed','bearing_ok'):
        np.testing.assert_array_equal(reversed_kin[key],kin[key][::-1])
    for key in ('v_n','v_e','vz','psi_dot'):
        np.testing.assert_array_equal(reversed_kin[key],-kin[key][::-1])
    np.testing.assert_allclose(np.cos(reversed_kin['psi']),-np.cos(course[::-1]),equal_nan=True)
    np.testing.assert_allclose(np.sin(reversed_kin['psi']),-np.sin(course[::-1]),atol=1e-15,equal_nan=True)
    np.testing.assert_array_equal(kin['psi'],course)
    again=reverse_motion(reversed_kin)
    for key in kin:
        if key!='psi': np.testing.assert_allclose(again[key],kin[key],equal_nan=True)
    np.testing.assert_allclose(np.cos(again['psi']),np.cos(course),equal_nan=True)


def test_reverse_motion_refuses_irregular_sampling():
    with pytest.raises(ValueError,match='one-second'):
        reverse_motion(dict(t=np.array([0.,1.,3.])))
