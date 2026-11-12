# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extend the independent analytic motion control without native prediction."""


def long_case():
    import numpy as np
    from lll.ilvis0_forecast_controls import case_arrays

    short = case_arrays(0, False, 'header_elapsed')
    packets = 20000
    repeats = (packets+len(short['dt'])-1)//len(short['dt'])
    dt = np.tile(short['dt'], repeats)[:packets]
    theta = np.tile(short['theta'], (repeats, 1))[:packets]
    dv = np.tile(short['dv'], (repeats, 1))[:packets]
    times = np.arange(1., 100.)
    longitude_rate = (short['gps'][1, 1]-short['gps'][0, 1]) / (
        short['times'][1]-short['times'][0])
    gps = np.c_[np.full(len(times), short['gps'][0, 0]),
                longitude_rate*times,
                np.full(len(times), short['gps'][0, 2])]
    if not np.isclose(np.sum(dt), 100., rtol=0., atol=1e-12):
        raise ValueError('exact generated support period required')
    return dict(theta=theta, dv=dv, dt=dt, times=times, gps=gps)
