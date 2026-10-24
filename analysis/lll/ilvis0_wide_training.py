# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit wider problem factory for unchanged, frozen prediction protocols.

There are no process-global patches or copied worker implementations. Qualified
source/provider hashes and the one-import transformations are recorded separately
from numerical and scientific qualification.
"""
import hashlib
import importlib
from pathlib import Path

SOURCES=('airquantumgrav_prediction.py','airquantumgrav_height_training.py')


def training_problem(*args,**kwargs):
    from lll.ilvis0_training_forecast import training_problem as original
    from lll.ilvis0_wide_tangent import problem
    base=original(*args,**kwargs)
    return problem(base,kernel=kwargs['tangent_kernel'])


def bind(*,expected_sources):
    from lll.studies.protocols import bind_function
    if not isinstance(expected_sources,dict) or set(expected_sources)!=set(SOURCES):
        raise ValueError('both explicit qualified protocol source hashes required')
    raw={name:Path(__file__).with_name(name).read_bytes() for name in SOURCES}
    actual={name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}
    if actual!=expected_sources:raise ValueError('protocol source hash mismatch')
    # Module imports define functions only. No numerical library is needed until
    # a prepared study actually calls its explicitly supplied problem factory.
    modules={name:importlib.import_module('lll.'+name[:-3]) for name in SOURCES}
    for name,module in modules.items():
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()!=actual[name]:
            raise ValueError('imported protocol module differs from bound source')
    provider_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    run,prediction=bind_function(raw[SOURCES[0]],expected_sha256=actual[SOURCES[0]],function='train_and_forecast',
        import_module='lll.ilvis0_training_forecast',import_name='training_problem',provider=training_problem,
        provider_source_sha256=provider_sha,namespace=vars(modules[SOURCES[0]]))
    calculate,control=bind_function(raw[SOURCES[1]],expected_sha256=actual[SOURCES[1]],function='calculate',
        import_module='lll.airquantumgrav_prediction',import_name='train_and_forecast',provider=run,
        provider_source_sha256=prediction['bound_function_ast_sha256'],namespace=vars(modules[SOURCES[1]]))
    return run,calculate,dict(version='explicit-wide-training-provider-v1',source_sha256=actual,
        provider_source_sha256=provider_sha,prediction=prediction,control=control)
