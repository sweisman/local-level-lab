# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolated selective-precision derivative experiment; not a fitting method."""
import hashlib
from pathlib import Path
import re
import types


VERSION = 'ilvis0-hybrid-value-tangent-prototype-v1'
WIDE_COLUMNS = (2, 3, 4, 9, 11, 14, 16, 18, 19, 20)
FAST_COLUMNS = tuple(i for i in range(27) if i not in WIDE_COLUMNS)


def derive(wide_source, *, expected_sha256):
    """Retain wide value arithmetic and selected wide derivative columns."""
    if not isinstance(wide_source, bytes) or hashlib.sha256(wide_source).hexdigest() != expected_sha256:
        raise ValueError('exact wide source hash required')
    source = wide_source.decode()
    marker = 'static void mul'
    if source.count(marker) != 1:
        raise ValueError('unsupported wide tangent layout')
    head, tail = source.split(marker, 1)
    declarations = {
        'long double v; std::array<long double,27> d;':
            f'long double v; std::array<double,{len(FAST_COLUMNS)}> d; '
            f'std::array<long double,{len(WIDE_COLUMNS)}> w;',
        'd.fill(0);': 'd.fill(0); w.fill(0);',
    }
    for old, new in declarations.items():
        if head.count(old) != 1:
            raise ValueError('unsupported wide Dual layout: ' + old)
        head = head.replace(old, new)
    pattern = r'for\(int i=0;i<27;i\+\+\)r\.d\[i\]=([^;]+);'
    if len(re.findall(pattern, head)) != 9:
        raise ValueError('unsupported wide Dual derivative operations')

    def two_precisions(match):
        expression = match.group(1)
        wide = expression.replace('.d[i]', '.w[i]')
        fast = re.sub(r'\b([abr])\.v\b',
                      lambda m: f'static_cast<double>({m.group(1)}.v)', expression)
        fast = re.sub(r'\bq\b', 'static_cast<double>(q)', fast)
        return (f'for(int i=0;i<{len(FAST_COLUMNS)};i++)r.d[i]={fast}; '
                f'for(int i=0;i<{len(WIDE_COLUMNS)};i++)r.w[i]={wide};')

    head = re.sub(pattern, two_precisions, head)
    fast_map = [FAST_COLUMNS.index(i) if i in FAST_COLUMNS else -1 for i in range(27)]
    wide_map = [WIDE_COLUMNS.index(i) if i in WIDE_COLUMNS else -1 for i in range(27)]
    maps = ('static constexpr int FAST_MAP[27]={' + ','.join(map(str, fast_map)) + '};\n'
            'static constexpr int WIDE_MAP[27]={' + ','.join(map(str, wide_map)) + '};\n')
    head = maps + head
    replacements = {
        'p[i].d[i]=limits[i];':
            'if(FAST_MAP[i]>=0) p[i].d[FAST_MAP[i]]=limits[i]; '
            'else p[i].w[WIDE_MAP[i]]=limits[i];',
        'value.d[h];':
            '(FAST_MAP[h]>=0 ? static_cast<long double>(value.d[FAST_MAP[h]]) '
            ': value.w[WIDE_MAP[h]]);',
    }
    for old, new in replacements.items():
        if tail.count(old) != 1:
            raise ValueError('unsupported wide tangent parameter/output mapping: ' + old)
        tail = tail.replace(old, new)
    return (head + marker + tail).encode()


def load(directory, *, expected_source_sha256, expected_loader_sha256,
         gravity_anchor_height_m=None):
    """Compile through an isolated copy of the unchanged wide loader."""
    from . import ilvis0_wide_tangent as reference
    loader_sha = hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest()
    if loader_sha != expected_loader_sha256:
        raise ValueError('exact shared loader source hash required')

    def bound_derive(raw, *, expected_sha256):
        wide = reference.derive(raw, expected_sha256=expected_sha256)
        return derive(wide, expected_sha256=hashlib.sha256(wide).hexdigest())

    namespace = dict(vars(reference), derive=bound_derive, VERSION=VERSION)
    private = types.FunctionType(reference.load.__code__, namespace,
                                 reference.load.__name__, reference.load.__defaults__,
                                 reference.load.__closure__)
    private.__kwdefaults__ = dict(reference.load.__kwdefaults__ or {})
    kernel, metadata = private(directory, expected_source_sha256=expected_source_sha256,
                               gravity_anchor_height_m=gravity_anchor_height_m)
    return kernel, dict(metadata, shared_loader_source_sha256=loader_sha,
                        shared_loader_unchanged=True,
                        wide_derivative_columns=list(WIDE_COLUMNS),
                        fast_derivative_columns=list(FAST_COLUMNS),
                        production_method_changed=False)
