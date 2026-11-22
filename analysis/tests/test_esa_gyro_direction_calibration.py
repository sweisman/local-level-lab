# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll import esa_gyro_direction_calibration as cal
from lll.esa_gyro_force_direction import angles, midpoint_attitudes


def test_box_includes_exact_rotation_and_force_corrections():
    dt = np.full(24,.25)
    time = np.arange(24)*.25
    theta = .05*np.column_stack((np.sin(time),np.cos(time),.1+time/10))
    force = np.column_stack((np.cos(time),.5*np.sin(time),-9.8+time/20))
    limits = np.array([[.002,.003,.004],[.01,.02,.015],[.07,.06,.04],[.01,.007,.014]])
    signed = limits*np.array([[1,-1,1],[-1,1,-1],[1,1,-1],[-1,-1,1]])
    a = np.full(6,1/6)
    lower, upper = slice(2,8), slice(17,23)
    nominal = midpoint_attitudes(theta).apply(force)
    norms = [np.linalg.norm(a@nominal[sl]) for sl in (lower,upper)]
    support = cal.Pair(lower,upper,a,a,*norms)
    changed_theta = (theta-signed[0]*dt[:,None])/(1+signed[1])
    changed_force = (force-signed[2])/(1+signed[3])
    changed = midpoint_attitudes(changed_theta).apply(changed_force)
    change = abs(angles([a@changed[lower]],[a@changed[upper]])[0]-
                 angles([a@nominal[lower]],[a@nominal[upper]])[0])
    assert change <= cal.angle_bounds(theta,force,dt,[support],limits)[0]
    assert cal.angle_bounds(theta,force,dt,[support],np.zeros((4,3)))[0] == 0.
