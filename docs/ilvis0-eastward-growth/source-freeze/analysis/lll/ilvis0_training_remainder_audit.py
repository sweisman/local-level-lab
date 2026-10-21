# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit coordinate-unit conversion for a saved 51-column bound expression."""
import math


def scaled_design(jacobian,report,scale):
    blocks=[jacobian]+[report[k] for k in ('previous_coefficients','acceleration_coefficients','transform_coefficients')]
    if (len(scale)!=3 or any(not math.isfinite(v) or v<=0 for v in scale)
            or any(len(b)!=3 or any(len(r)!=n for r in b) for b,n in zip(blocks,(27,6,9,9)))
            or any(not math.isfinite(v) for block in blocks for row in block for v in row)):
        raise ValueError('complete finite 27+6+9+9 columns and positive coordinate scales required')
    return [[scale[axis]*v for block in blocks for v in block[axis]] for axis in range(3)]
