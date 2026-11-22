# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research candidate: choose tangent precision from the physical model ID."""

import hashlib
from pathlib import Path


VERSION = 'ilvis0-model-declared-tangent-v1'
METHODS = {'sphere_rotating': 'selective',
           'sphere_still': 'selective',
           'flat_still': 'wide'}


def method_for_model(model):
    try:
        return METHODS[model]
    except (KeyError, TypeError) as exc:
        raise ValueError('unsupported physical model for tangent dispatch') from exc


def load_for_model(model, directory, *, expected_source_sha256,
                   expected_wide_loader_sha256,
                   expected_selective_loader_sha256,
                   gravity_anchor_height_m=None):
    """Load exactly one source-bound tangent, without consulting outcomes."""
    from . import ilvis0_hybrid_tangent, ilvis0_wide_tangent

    method = method_for_model(model)
    actual = hashlib.sha256(
        Path(ilvis0_wide_tangent.__file__).read_bytes()).hexdigest()
    if actual != expected_wide_loader_sha256:
        raise ValueError('wide tangent loader source hash differs')
    selective_actual = hashlib.sha256(
        Path(ilvis0_hybrid_tangent.__file__).read_bytes()).hexdigest()
    if selective_actual != expected_selective_loader_sha256:
        raise ValueError('selective tangent loader source hash differs')
    kwargs = dict(expected_source_sha256=expected_source_sha256,
                  gravity_anchor_height_m=gravity_anchor_height_m)
    if method == 'selective':
        kernel, metadata = ilvis0_hybrid_tangent.load(
            directory, expected_loader_sha256=expected_wide_loader_sha256,
            **kwargs)
    else:
        kernel, metadata = ilvis0_wide_tangent.load(directory, **kwargs)
    return kernel, dict(metadata, dispatch_version=VERSION,
                        dispatch_model=model, dispatch_method=method,
                        scientific_decision='abstain')
