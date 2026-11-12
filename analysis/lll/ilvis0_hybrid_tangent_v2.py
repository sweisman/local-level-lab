# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolated selective-tangent revision with weak attitude directions widened.

This is a candidate for separate qualification, not a replacement for the
frozen first selective-tangent study or the established wide calculation.
"""

import types

from . import ilvis0_hybrid_tangent as original


VERSION = 'ilvis0-hybrid-value-tangent-prototype-v2'
WIDE_COLUMNS = tuple(sorted((*original.WIDE_COLUMNS, 0, 1)))
FAST_COLUMNS = tuple(index for index in range(27) if index not in WIDE_COLUMNS)


def _bound(function, **overrides):
    namespace = dict(vars(original), **overrides)
    result = types.FunctionType(function.__code__, namespace,
                                function.__name__, function.__defaults__,
                                function.__closure__)
    result.__kwdefaults__ = dict(function.__kwdefaults__ or {})
    return result


def derive(wide_source, *, expected_sha256):
    """Use the old source transformer with a separately bound precision map."""
    candidate = _bound(original.derive, WIDE_COLUMNS=WIDE_COLUMNS,
                       FAST_COLUMNS=FAST_COLUMNS)
    return candidate(wide_source, expected_sha256=expected_sha256)


def load(directory, *, expected_source_sha256, expected_loader_sha256,
         gravity_anchor_height_m=None):
    """Compile the revised source through the unchanged wide loader."""
    candidate = _bound(original.load, derive=derive, VERSION=VERSION,
                       WIDE_COLUMNS=WIDE_COLUMNS, FAST_COLUMNS=FAST_COLUMNS)
    kernel, metadata = candidate(
        directory, expected_source_sha256=expected_source_sha256,
        expected_loader_sha256=expected_loader_sha256,
        gravity_anchor_height_m=gravity_anchor_height_m)
    return kernel, dict(metadata, precision_revision='attitude-x-y-wide',
                        production_method_changed=False)
