# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retain vector coordinates in the existing rotation-departure operators."""
from .ilvis0_relative_rotation import Delta,plus,multiply,rotation,advance_left,advance_right,compose
from .ilvis0_cached_transport import matrix_vector as apply,add


def action(left,right,initial,vector):
    first=apply(multiply(multiply(left,initial),rotation(right)),vector)
    second=apply(multiply(initial,right),vector)
    return add(first,second)
