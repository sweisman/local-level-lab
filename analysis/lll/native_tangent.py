# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared source-bound loader for the complete wider tangent/residual ABI."""
import ctypes
import math


def load(directory,source,*,prefix,expected_sha256,reserve_build,gravity_anchor_height_m=None):
    import numpy as np
    from lll.native_build import cpp
    if gravity_anchor_height_m is not None and (not math.isfinite(gravity_anchor_height_m) or gravity_anchor_height_m<=-6371000.):
        raise ValueError('finite supported gravity anchor required')
    binary,meta=cpp(directory,source,prefix=prefix,expected_sha256=expected_sha256,reserve_build=reserve_build)
    lib=ctypes.CDLL(str(binary));bits=lib.ilvis0_wide_bits()
    if bits<=53:raise ValueError('genuinely wider arithmetic required')
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');fn=lib.ilvis0_wide_tangent
    fn.argtypes=[ctypes.c_size_t,array,array,array,ctypes.c_size_t,array,array,array,array,array,array,
        ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,array,array,array,array,
        ctypes.POINTER(ctypes.c_int),ctypes.c_int,ctypes.c_double];fn.restype=ctypes.c_int
    def kernel(*args,observations=None,difference=None):
        if len(args)!=18:raise ValueError('original complete tangent ABI required')
        if observations is None:observations=np.zeros((args[4],3))
        if difference is None:difference=np.empty((args[4],3))
        return fn(*args[:-1],observations,difference,args[-1],
            int(gravity_anchor_height_m is not None),gravity_anchor_height_m or 0.)
    return kernel,dict(meta,internal_mantissa_bits=bits)
