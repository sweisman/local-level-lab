# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic extended arithmetic; frozen kernels and science decisions unchanged."""
import ctypes
import hashlib
from pathlib import Path
import subprocess

import numpy as np

VERSION='ilvis0-extended-tangent-diagnostic-v1'


def extended_source(source):
    """Change internal representation while preserving ABI and clock branches."""
    replacements={
        'double v; std::array<double,27> d;':'long double v; std::array<long double,27> d;',
        'Dual(double value=0)':'Dual(long double value=0)',
        'double q=std::cos(a.v)':'long double q=std::cos(a.v)',
        'double q=-std::sin(a.v)':'long double q=-std::sin(a.v)',
        'double q=b*std::pow(a.v,b-1)':'long double q=b*std::pow(a.v,b-1)',
        'times[j]+p[25].v<=end':'times[j]+static_cast<double>(p[25].v)<=end',
    }
    for old,new in replacements.items():
        if source.count(old)!=1:
            raise ValueError('unrecognized native tangent layout: '+old)
        source=source.replace(old,new)
    return ('// Diagnostic internal arithmetic; original equations, ABI and packet clock.\n'
            '#include <limits>\n'+source+
            '\nextern "C" int ilvis0_precision_bits() { return std::numeric_limits<long double>::digits; }\n')


def load_tangent(directory):
    original=Path(__file__).with_name('ilvis0_tangent.cpp')
    generated=extended_source(original.read_text())
    digest=hashlib.sha256(generated.encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    source=directory/('tangent-extended-'+digest+'.cpp')
    binary=source.with_suffix('.so')
    if source.exists():
        if source.read_text()!=generated:
            raise ValueError('generated precision source hash mismatch')
    else:
        source.write_text(generated)
    flags=['-O2','-std=c++17','-fPIC','-shared']
    if not binary.exists():
        temporary=binary.with_suffix('.partial.so')
        subprocess.run(['c++',*flags,str(source),'-o',str(temporary)],check=True,capture_output=True)
        temporary.replace(binary)
    library=ctypes.CDLL(str(binary))
    bits=library.ilvis0_precision_bits()
    if bits<=53:
        raise ValueError('platform long double does not provide wider arithmetic')
    function=library.ilvis0_tangent
    array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    function.argtypes=[ctypes.c_size_t,array,array,array,ctypes.c_size_t,array,array,array,array,
                       array,array,ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,
                       array,array,ctypes.POINTER(ctypes.c_int)]
    function.restype=ctypes.c_int
    return function,dict(version=VERSION,original_source_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                         source_sha256=digest,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                         compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
                         flags=flags,internal_mantissa_bits=bits,abi_mantissa_bits=53,
                         packet_clock_changed=False,source_file=source.name,binary_file=binary.name)
