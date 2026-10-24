# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit wider provider for the unchanged observed ESA protocol.

Binding creates callables only. It reads no measurement, grants no fitting
allowance and does not replace the required full training qualification.
"""
import hashlib
import importlib
from pathlib import Path

from lll.ilvis0_wide_training import SOURCES as TRAINING_SOURCES

OBSERVED_SOURCES=('airquantumgrav_observed.py','airquantumgrav_observed_height.py')
SOURCES=(*TRAINING_SOURCES,*OBSERVED_SOURCES)


def bind(*,expected_sources):
    from lll.ilvis0_wide_training import bind as training_bind
    from lll.studies.protocols import bind_function
    if not isinstance(expected_sources,dict) or set(expected_sources)!=set(SOURCES):
        raise ValueError('all four explicit protocol source hashes required')
    raw={name:Path(__file__).with_name(name).read_bytes() for name in SOURCES}
    actual={name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}
    if actual!=expected_sources:raise ValueError('observed protocol source hash mismatch')
    run,unused,training=training_bind(expected_sources={name:actual[name] for name in TRAINING_SOURCES})
    modules={name:importlib.import_module('lll.'+name[:-3]) for name in OBSERVED_SOURCES}
    for name,module in modules.items():
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()!=actual[name]:
            raise ValueError('imported observed module differs from its source')
    observed,first=bind_function(raw[OBSERVED_SOURCES[0]],expected_sha256=actual[OBSERVED_SOURCES[0]],function='calculate',
        import_module='lll.airquantumgrav_prediction',import_name='train_and_forecast',provider=run,
        provider_source_sha256=training['prediction']['bound_function_ast_sha256'],namespace=vars(modules[OBSERVED_SOURCES[0]]))
    calculate,second=bind_function(raw[OBSERVED_SOURCES[1]],expected_sha256=actual[OBSERVED_SOURCES[1]],function='calculate',
        import_module='lll.airquantumgrav_observed',import_name='calculate',provider=observed,
        provider_source_sha256=first['bound_function_ast_sha256'],namespace=vars(modules[OBSERVED_SOURCES[1]]))
    return calculate,dict(version='explicit-wide-observed-provider-v1',source_sha256=actual,
        provider_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        training=training,observed=first,height=second)
