# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply an explicit recorded receiver-clock convention to one RINEX epoch."""

import math


def correct_clock(record, phases, *, retime):
    """Remove the recorded offset from code and phase, with optional epoch retiming."""
    import numpy as np

    from .esa_carrier_phase_support import C, F1, F2

    offset = record['receiver_clock_offset_s']
    cycles = np.asarray(phases, dtype=float)
    if (offset is None or not math.isfinite(offset) or cycles.ndim != 2 or cycles.shape[1] != 2
            or not np.isfinite(cycles).all() or type(retime) is not bool):
        raise ValueError('finite recorded clock, complete carrier phases and explicit epoch convention required')
    correction_m = C*offset
    satellites = []
    for satellite in record['satellites']:
        signals = [dict(signal, pseudorange_m=signal['pseudorange_m']-correction_m)
                   if signal['pseudorange_m'] is not None else signal.copy() for signal in satellite['signals']]
        satellites.append(dict(satellite, signals=signals))
    seconds = record['gps_week_seconds']-offset if retime else record['gps_week_seconds']
    return dict(record, gps_week_seconds=seconds, satellites=satellites,
                receiver_clock_offset_s=0.), cycles-offset*np.array([F1, F2])
