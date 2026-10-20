# SPDX-License-Identifier: AGPL-3.0-or-later
"""Display already-verified support summands without repeating evaluations."""
from fractions import Fraction as F


def components(future,region,axis):
    if type(axis)!=int or not 0<=axis<3:raise ValueError('one saved coordinate axis required')
    scale=F(region['coordinate_scale'][axis]);remainder=F(future['bound']['unshared_remainder'][axis])
    arithmetic=F(region['arithmetic_allowance']);certificate=future['envelope']['certificates'][axis]
    if scale<=0 or remainder<0 or arithmetic<0:raise ValueError('positive scale and nonnegative saved allowances required')
    affine=F(certificate['upper'])+F(certificate['negated_lower'])
    unshared=2*remainder*scale;rounding=2*arithmetic
    width=F(future['envelope']['upper'][axis])-F(future['envelope']['lower'][axis])
    padding=width-affine-unshared-rounding
    if width<0 or padding<0:raise ValueError('saved width and verified component terms disagree')
    return dict(affine_width=str(affine),unshared_width=str(unshared),arithmetic_width=str(rounding),
        rounding_padding=str(padding),total_width=str(width),saved_remainder_floor=str(unshared+rounding),
        affine_width_nonnegative=affine>=0,remainder_floor_requires_nonempty_region=True,
        new_support_evaluations=0,new_native_evaluations=0)
