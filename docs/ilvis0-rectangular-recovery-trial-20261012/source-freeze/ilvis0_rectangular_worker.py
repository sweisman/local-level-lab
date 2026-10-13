# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate finite rectangular-method trial; reuse unchanged durable machinery."""
import argparse
import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from lll import ilvis0_solver_rectangular as solver

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path('docs/ilvis0-rectangular-recovery-trial-20261012')
OUTPUT = Path('data/ilvis0-rectangular-recovery-trial-v2-20261012')
VERSION = 'ilvis0-rectangular-recovery-worker-v2'

# A private module instance keeps the completed worker's globals and source intact.
spec = importlib.util.spec_from_file_location('ilvis0_rectangular_core',
                                             Path(__file__).with_name('ilvis0_recovery_worker.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.VERSION, core.GUIDE, core.OUTPUT, core.solver = VERSION, GUIDE, OUTPUT, solver
original_fit_task = core.fit_task


def save_linearization(output, identity, fit):
    local = fit.pop('local_linearization', None)
    if local is None:
        return
    name = identity.replace('::', '-')+'-linearization.json.gz'
    core.shared.clock.residuals.atomic_bytes(output/name, gzip.compress(
        json.dumps(local, sort_keys=True, allow_nan=False).encode(), mtime=0))
    fit.update(linearization_file=name, linearization_sha256=core.base.il.sha256(output/name))


def fit_task(output, task, *args):
    fit = original_fit_task(output, task, *args)
    save_linearization(output, task['identity'], fit)
    return fit


core.fit_task = fit_task


def verify_linearizations(output, summary):
    for fit in summary['results'].values():
        if 'linearization_file' in fit:
            name = fit['linearization_file']
            if Path(name).name != name:
                raise ValueError('invalid local tangent artifact name')
            core.shared.clock.residuals.check_hashes({str(output/name): fit['linearization_sha256']})
        elif fit.get('converged'):
            raise ValueError('completed fit missing its local tangent artifact')


def verify(output, originals=False):
    manifest = core.verify(output, originals=originals)
    required = [Path(__file__), Path(solver.__file__),
                ROOT/'analysis/tests/test_ilvis0_rectangular_worker.py',
                ROOT/'analysis/tests/test_ilvis0_solver_rectangular.py',
                ROOT/'analysis/lll/ilvis0_solver_refinement.py',
                ROOT/'analysis/lll/ilvis0_solver_verified_stop.py']
    if any(str(p.resolve()) not in manifest['sources'] for p in required):
        raise ValueError('rectangular worker qualification/source freeze incomplete')
    return manifest


def prepare(output):
    if (output/'manifest.json').exists():
        return verify(output)
    manifest = core.prepare(output)
    # Seal the adapter, its tests, and all independently recorded controls before
    # authorization. The inherited preparation has no numerical fitting calls.
    receipt = core.base.load(GUIDE/'control-receipt.json')
    for name, digest in receipt['sources'].items():
        source = Path(name).resolve()
        if core.base.il.sha256(source) != digest:
            raise ValueError('control/source mismatch')
        manifest['sources'][str(source)] = digest
    for path in (Path(__file__), ROOT/'analysis/tests/test_ilvis0_rectangular_worker.py',
                 ROOT/'analysis/tests/test_ilvis0_solver_rectangular.py'):
        manifest['sources'][str(path.resolve())] = core.base.il.sha256(path)
    if len({Path(p).name for p in manifest['sources']}) != len(manifest['sources']):
        raise ValueError('source snapshot filename collision')
    for source in manifest['sources']:
        shutil.copyfile(source, output/'source-freeze'/Path(source).name)
    core.base.follow.atomic_json(output/'manifest.json', manifest)
    return verify(output)


def publish(output):
    verify(output)
    summary = core.base.load(output/'summary.json')
    verify_linearizations(output, summary)
    core.publish(output)
    receipt = core.base.load(GUIDE/'evidence-receipt.json')
    for fit in summary['results'].values():
        if 'linearization_file' in fit:
            name = fit['linearization_file']
            shutil.copyfile(output/name, GUIDE/name)
            receipt['artifacts'][name] = fit['linearization_sha256']
    core.base.follow.atomic_json(GUIDE/'evidence-receipt.json', receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--record-authorization', action='store_true')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--package-only', action='store_true')
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args()
    os.chdir(ROOT)
    output = args.output.resolve()
    if args.prepare_only:
        manifest = prepare(output)
        print(json.dumps(dict(manifest_sha256=core.base.il.sha256(output/'manifest.json'),
                              starts=manifest['proposal']['maximum_starts'],
                              sweeps=manifest['proposal']['maximum_native_sweeps'])))
    elif args.package_only:
        publish(output)
    elif args.record_authorization:
        with core.shared.worker_lock(output):
            manifest = verify(output)
            if (output/'completion.json').exists():
                raise ValueError('completed trial is frozen')
            core.base.follow.atomic_json(output/'authorization.json', dict(
                manifest_sha256=core.base.il.sha256(output/'manifest.json'),
                maximum_starts=manifest['proposal']['maximum_starts'],
                maximum_native_sweeps=manifest['proposal']['maximum_native_sweeps'],
                retries=0, approval='explicit_user_approval'))
    elif args.detach:
        with core.shared.worker_lock(output) as lock:
            manifest = verify(output)
            core.authorization(output, manifest['proposal'])
            if (output/'completion.json').exists():
                raise ValueError('completed trial is frozen')
            with (output/'worker.log').open('ab') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                        '--output', str(output), '--lock-fd', str(lock.fileno())],
                        pass_fds=(lock.fileno(),), start_new_session=True, stdout=log, stderr=log)
            core.base.follow.atomic_json(output/'worker.json', dict(pid=child.pid,
                manifest_sha256=core.base.il.sha256(output/'manifest.json')))
            print('Detached rectangular recovery worker', child.pid)
    else:
        if not (output/'authorization.json').exists():
            raise ValueError('explicit finite authorization required')
        verify(output)
        core.run(output, args.lock_fd)
        publish(output)


if __name__ == '__main__':
    main()
