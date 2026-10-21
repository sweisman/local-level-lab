# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fast outward radius operations with unchanged reference centers.

Source/calibration input certificates and whole-program mechanization rounding
remain separate qualifications. Unsupported floating-point modes are rejected.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import tempfile
import numpy as np
from . import ilvis0_local_step_bounds as legacy
from . import ilvis0_cached_transport as exact
from .ilvis0_component_transport import Value as AxisValue
from .ilvis0_batched_bounds import load_backend
from .ilvis0_directional_values import Value as DirectionalValue,_radii
from .ilvis0_saved_prediction_audit import endpoint

_BACKEND=None
_METADATA=None
_TEMPORARY=None


def configure_backend(directory,*,source_directory=None):
    global _BACKEND,_METADATA
    candidate,metadata=load_backend(directory,source_directory=source_directory)
    if _METADATA is not None and _METADATA['source_sha256']!=metadata['source_sha256']:
        raise ValueError('cannot mix compiled arithmetic implementations in one process')
    _BACKEND=candidate;_METADATA=metadata
    return metadata


def backend():
    global _TEMPORARY
    if _BACKEND is None:
        _TEMPORARY=tempfile.TemporaryDirectory(prefix='lll-outward-bounds-')
        configure_backend(_TEMPORARY.name)
    return _BACKEND


def _scalar_radius(value):
    if isinstance(value,(float,np.floating)) and np.asarray(value).itemsize<=8:
        return legacy._radius(value)
    return legacy._radius(endpoint(F(value),True))


def _component_radii(values,shape):
    raw=np.asarray(values)
    if raw.shape!=shape:raise ValueError('component radius shape mismatch')
    if raw.dtype.kind=='f' and raw.dtype.itemsize<=8:
        result=np.array(raw,dtype=float,copy=True)
        if not np.all(np.isfinite(result)) or np.any(result<0):raise ValueError('nonnegative finite component radii required')
        return result
    return _radii(values,shape)


@dataclass(frozen=True,init=False,eq=False)
class Value(exact.Value):
    def __init__(self,center,change=0.,remainder=0.,*,component_change=None,component_remainder=None):
        legacy.Value.__init__(self,center,_scalar_radius(change),_scalar_radius(remainder))
        shape=self.center.shape
        d=np.full(shape,self.change) if component_change is None else _component_radii(component_change,shape)
        r=np.full(shape,self.remainder) if component_remainder is None else _component_radii(component_remainder,shape)
        self._finish(d,r)

    def _install(self,bounds):
        for name in ("component_change","component_remainder"):
            value=bounds[name];value.setflags(write=False);object.__setattr__(self,name,value)
        for name in ("change","remainder"):object.__setattr__(self,name,bounds[name])
        view=object.__new__(DirectionalValue)
        for name,value in (("center",self.center),("change",self.component_change),("remainder",self.component_remainder)):
            object.__setattr__(view,name,value)
        object.__setattr__(self,"_directional_view",view)

    def _finish(self,change,remainder):
        bounds=backend().finalize(change,remainder,self.change,self.remainder)
        self._install(bounds)

    @classmethod
    def _from_cpp(cls,center,bounds):
        result=object.__new__(cls);center=np.asarray(center,float);center.setflags(write=False)
        object.__setattr__(result,"center",center);result._install(bounds)
        return result


def _value(a):
    if not isinstance(a,legacy.Value):raise ValueError('certified scalar or vector required')
    if isinstance(a,Value):return a
    if isinstance(a,AxisValue):return Value(a.center,a.change,a.remainder,component_change=a.component_change,component_remainder=a.component_remainder)
    return Value(a.center,a.change,a.remainder)


def _operation(op,a,b,center):
    result=backend().vector(op,a.center,a.component_change,a.component_remainder,[a.change,a.remainder,0.],
        b.center,b.component_change,b.component_remainder,[b.change,b.remainder,0.],center)
    return Value._from_cpp(center,result)


def add(a,b):
    a,b=_value(a),_value(b)
    if a.center.shape!=b.center.shape:raise ValueError('aligned shapes required')
    return _operation(0,a,b,a.center+b.center)


def scale(a,number):
    a=_value(a)
    if not math.isfinite(number):raise ValueError('finite fixed scalar required')
    if not isinstance(number,(float,np.floating)) and F(float(number))!=F(number):return _value(exact.scale(a,number))
    scalar=Value(float(number));return _operation(1,a,scalar,a.center*float(number))


def scalar_product(a,b):
    a,b=_value(a),_value(b)
    if a.center.shape!=() or b.center.shape!=(3,):raise ValueError('scalar and three-vector required')
    return _operation(2,a,b,a.center*b.center)


def cross(a,b):
    a,b=_value(a),_value(b)
    if a.center.shape!=(3,) or b.center.shape!=(3,):raise ValueError('two three-vectors required')
    return _operation(3,a,b,np.cross(a.center,b.center))


def matrix_vector(matrix,vector):
    from .ilvis0_relative_rotation import Delta
    if not isinstance(matrix,(legacy.Matrix,Delta)):raise ValueError('certified matrix required')
    b=_value(vector)
    if b.center.shape!=(3,):raise ValueError('three-vector required')
    general=isinstance(matrix,Delta);norm=matrix.norm if general else max(1.,backend().matrix_norm(matrix.center))
    center=matrix.center@b.center
    result=backend().vector(5 if general else 4,matrix.center,np.full((3,3),matrix.change),np.full((3,3),matrix.remainder),
        [matrix.change,matrix.remainder,norm],b.center,b.component_change,b.component_remainder,[b.change,b.remainder,0.],center)
    return Value._from_cpp(center,result)


component=exact.component
