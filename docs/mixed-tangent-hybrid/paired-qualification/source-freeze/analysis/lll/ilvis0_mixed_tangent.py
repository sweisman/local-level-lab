# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolated speed prototype: wide physical values, binary64 derivative arithmetic.

Not a qualified replacement for the running method. The unchanged wide loader
is reused in a private function namespace; no shared source/global is patched.
"""
import hashlib
from pathlib import Path
import types

VERSION='ilvis0-mixed-value-tangent-prototype-v1'


def derive(wide_source,*,expected_sha256):
    """Transform only Dual derivative storage/arithmetic in supplied wide C++."""
    if not isinstance(wide_source,bytes) or hashlib.sha256(wide_source).hexdigest()!=expected_sha256:
        raise ValueError('exact wide source hash required')
    text=wide_source.decode();marker='static void mul'
    if text.count(marker)!=1:raise ValueError('unsupported wide Dual layout')
    head,tail=text.split(marker,1)
    changes={
        'long double v; std::array<long double,27> d;':'long double v; std::array<double,27> d;',
        'static Dual operator*(const Dual& a,const Dual& b) { Dual r(a.v*b.v); for(int i=0;i<27;i++)r.d[i]=a.d[i]*b.v+a.v*b.d[i]; return r; }':
            'static Dual operator*(const Dual& a,const Dual& b) { Dual r(a.v*b.v); double av=static_cast<double>(a.v),bv=static_cast<double>(b.v); for(int i=0;i<27;i++)r.d[i]=a.d[i]*bv+av*b.d[i]; return r; }',
        'static Dual operator/(const Dual& a,const Dual& b) { Dual r(a.v/b.v); for(int i=0;i<27;i++)r.d[i]=(a.d[i]-r.v*b.d[i])/b.v; return r; }':
            'static Dual operator/(const Dual& a,const Dual& b) { Dual r(a.v/b.v); double rv=static_cast<double>(r.v),bv=static_cast<double>(b.v); for(int i=0;i<27;i++)r.d[i]=(a.d[i]-rv*b.d[i])/bv; return r; }',
        'long double q=std::cos(a.v);':'double q=static_cast<double>(std::cos(a.v));',
        'long double q=-std::sin(a.v);':'double q=static_cast<double>(-std::sin(a.v));',
        'static Dual sqrt(const Dual& a) { Dual r(std::sqrt(a.v)); for(int i=0;i<27;i++)r.d[i]=a.d[i]/(2*r.v); return r; }':
            'static Dual sqrt(const Dual& a) { Dual r(std::sqrt(a.v)); double q=2*static_cast<double>(r.v); for(int i=0;i<27;i++)r.d[i]=a.d[i]/q; return r; }',
        'long double q=b*std::pow(a.v,b-1);':'double q=static_cast<double>(b*std::pow(a.v,b-1));',
    }
    for old,new in changes.items():
        if head.count(old)!=1:raise ValueError('unsupported wide Dual layout: '+old)
        head=head.replace(old,new)
    return (head+marker+tail).encode()


def load(directory,*,expected_source_sha256,expected_loader_sha256,gravity_anchor_height_m=None):
    from . import ilvis0_wide_tangent as reference
    loader_sha=hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest()
    if loader_sha!=expected_loader_sha256:raise ValueError('exact shared loader source hash required')
    def bound_derive(raw,*,expected_sha256):
        wide=reference.derive(raw,expected_sha256=expected_sha256)
        return derive(wide,expected_sha256=hashlib.sha256(wide).hexdigest())
    namespace=dict(vars(reference),derive=bound_derive,VERSION=VERSION)
    private=types.FunctionType(reference.load.__code__,namespace,reference.load.__name__,
        reference.load.__defaults__,reference.load.__closure__)
    private.__kwdefaults__=dict(reference.load.__kwdefaults__ or {})
    kernel,metadata=private(directory,expected_source_sha256=expected_source_sha256,
        gravity_anchor_height_m=gravity_anchor_height_m)
    return kernel,dict(metadata,shared_loader_source_sha256=loader_sha,shared_loader_unchanged=True,
        derivative_arithmetic='binary64 with rounded wide coefficients',
        value_arithmetic='original wide path',production_method_changed=False)
