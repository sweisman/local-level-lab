# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolated six-fit verified-stopping comparison; preparation starts no fits."""
import importlib.util
from pathlib import Path
import shutil

from lll import ilvis0_solver_verified_stop as solver

SOURCE=Path(__file__).resolve().with_name('ilvis0_unit_scale_trial.py')
spec=importlib.util.spec_from_file_location('isolated_verified_stop_worker',SOURCE)
_worker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(_worker)
# Reuse the unchanged pipeline in a private module, leaving the old worker untouched.
_worker.__file__=__file__
_worker.solver=solver
_worker.VERSION='ilvis0-verified-stop-prediction-trial-v1'
_worker.OUTPUT=Path('data/ilvis0-verified-stop-trial-20261011')
_worker.GUIDE=Path('docs/ilvis0-verified-stop-trial-20261011')
VERSION,OUTPUT,GUIDE=_worker.VERSION,_worker.OUTPUT,_worker.GUIDE
identities=_worker.identities
original_scope=_worker.scope
original_prepare=_worker.prepare
original_verify=_worker.verify
CRITICAL=(Path(__file__).resolve(),SOURCE,
    Path(__file__).resolve().with_name('test_ilvis0_verified_stop_trial.py'))


def scope():
    return dict(original_scope(),optimizer='unit_scale_with_fresh_bounded_stopping',
        critical_source_paths=[str(p) for p in CRITICAL])


def verify(output):
    manifest=original_verify(output)
    if any(str(p) not in manifest['sources'] for p in CRITICAL):
        raise ValueError('verified-stop critical source missing from freeze')
    return manifest


def prepare(output):
    output=Path(output)
    if (output/'manifest.json').exists(): return verify(output)
    # Original preparation verifies its scientific inputs before adding this adapter
    # and reused worker to the new freeze. Never repair an existing manifest.
    _worker.verify=original_verify
    try: manifest=original_prepare(output)
    finally: _worker.verify=verify
    for source in CRITICAL:
        manifest['sources'][str(source)]=_worker.clock.base.il.sha256(source)
        shutil.copyfile(source,output/'source-freeze'/source.name)
    _worker.clock.base.follow.atomic_json(output/'manifest.json',manifest)
    return verify(output)


_worker.scope=scope
_worker.prepare=prepare
_worker.verify=verify
run=_worker.run
publish=_worker.publish
main=_worker.main


if __name__=='__main__': main()
