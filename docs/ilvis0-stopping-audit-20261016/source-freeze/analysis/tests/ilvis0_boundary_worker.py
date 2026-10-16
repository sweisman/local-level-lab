# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite boundary-aware trial using unchanged durable recovery machinery."""
import argparse
import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from lll import ilvis0_solver_boundary as solver

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path('docs/ilvis0-boundary-recovery-trial-20261012')
OUTPUT = Path('data/ilvis0-boundary-recovery-trial-20261012')
VERSION = 'ilvis0-boundary-recovery-worker-v1'
spec = importlib.util.spec_from_file_location('ilvis0_boundary_core',
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
            raise ValueError('completed fit missing local tangent artifact')


def validate_controls(receipt):
    required = ('CONTROL.md', 'control-results.json', 'test-output.txt')
    if any(name not in receipt.get('artifacts', {}) for name in required):
        raise ValueError('boundary qualification receipt incomplete')
    core.shared.clock.audit.verify_artifacts(GUIDE, receipt)
    core.shared.clock.residuals.check_hashes(receipt['sources'])
    results = core.base.load(GUIDE/'control-results.json')
    if (results.get('exit_code') != 0 or results.get('known_answer_passes') != 40
            or results.get('observed_fit_starts') != 0 or results.get('solver_version') != solver.VERSION):
        raise ValueError('boundary qualification incomplete')
    core.base.runtime.check_environment(results['numerical_environment'])


def verify(output, originals=False):
    manifest = core.verify(output, originals=originals)
    required = (Path(__file__), Path(solver.__file__),
                ROOT/'analysis/tests/test_ilvis0_boundary_worker.py',
                ROOT/'analysis/tests/test_ilvis0_solver_boundary.py',
                ROOT/'analysis/tests/test_ilvis0_boundary_controls.py')
    if any(str(p.resolve()) not in manifest['sources'] for p in required):
        raise ValueError('boundary qualification/source freeze incomplete')
    validate_controls(core.base.load(GUIDE/'control-receipt.json'))
    return manifest


def completed_numerical_dependency(output):
    """Reuse sealed numerical tools, not an older study's mutable public prose.

    All new observations and fit inputs are frozen separately by prepare(). This
    check never authorizes resuming the completed dependency or changing its inputs.
    """
    manifest = core.base.load(output/'manifest.json')
    complete = core.base.load(output/'completion.json')
    if (complete['state'] != 'complete'
            or complete['manifest_sha256'] != core.base.il.sha256(output/'manifest.json')
            or complete['summary_sha256'] != core.base.il.sha256(output/'summary.json')):
        raise ValueError('completed numerical dependency hash mismatch')
    core.shared.clock.residuals.check_hashes(manifest['sources'])
    core.base.runtime.check_environment(manifest['environment'])
    for name, digest in manifest['sources'].items():
        if core.base.il.sha256(output/'source-freeze'/Path(name).name) != digest:
            raise ValueError('completed numerical source snapshot mismatch')
    for name, digest in manifest['artifacts'].items():
        if core.base.il.sha256(output/name) != digest:
            raise ValueError('completed numerical artifact mismatch')
    core.shared.check_accounting(output, manifest, core.base.load(output/'summary.json'), complete)
    return manifest


def prepare(output):
    with core.shared.worker_lock(output):
        receipt = core.base.load(GUIDE/'control-receipt.json')
        validate_controls(receipt)
        if (output/'manifest.json').exists():
            return verify(output)
        if (output/'starts.jsonl').exists():
            raise ValueError('unmarked charge journal')
        for directory, name in ((core.SUBSET, 'preparation-receipt.json'),
                                (core.BASELINE, 'evidence-receipt.json')):
            saved = core.base.load(directory/name)
            core.shared.clock.audit.verify_artifacts(directory, saved)
            core.shared.clock.residuals.check_hashes(saved.get('sources', {}))
        prior = completed_numerical_dependency(core.shared.OUTPUT)
        baseline = core.base.load(core.BASELINE/'summary.json.gz')
        subset = core.base.load(core.SUBSET/'selection-summary.json')
        proposal = core.planning.build(baseline['results'], subset['selected_segment_ids'])
        proposal.update(solver_version=solver.VERSION,
                        x_scale='physical-bound normalized coordinates; unscaled BVLS linear steps',
                        execution_authority='standing_analysis_roadmap', observed_allowance_authorized=True)
        selection = core.base.load(core.BASELINE/'selection.json.gz')
        indexed = {row['segment']['segment_id']: row for row in selection['selected']}
        chosen = [indexed[sid] for sid in proposal['selected_segment_ids']]
        sources = dict(prior['sources'])
        sources.update(receipt['sources'])
        for path in (Path(core.__file__), Path(core.planning.__file__),
                     ROOT/'analysis/tests/test_ilvis0_recovery_plan.py',
                     ROOT/'analysis/tests/test_ilvis0_recovery_worker.py'):
            sources[str(path.resolve())] = core.base.il.sha256(path)
        core.shared.clock.residuals.check_hashes(sources)
        if len({Path(p).name for p in sources}) != len(sources):
            raise ValueError('source snapshot filename collision')
        inputs = {}
        groups = ((core.BASELINE, ('summary.json.gz', 'selection.json.gz', 'manifest.json',
                                    'fit-manifest.json', 'completion.json', 'evidence-receipt.json')),
                  (core.SUBSET, ('preparation-receipt.json', 'selection-summary.json', 'representative-subset.csv')),
                  (GUIDE, ('PLAN.md', 'control-receipt.json')),
                  (core.shared.OUTPUT, ('manifest.json', 'completion.json', 'summary.json',
                                       'starts.jsonl', 'sweeps.jsonl')))
        for directory, names in groups:
            for name in names:
                path = (directory/name).resolve()
                inputs[str(path)] = core.base.il.sha256(path)
        context = (ROOT/'data/ilvis0-followup-20261007/summary.json').resolve()
        inputs[str(context)] = core.base.il.sha256(context)
        originals = {row['source_path']: core.base.il.sha256(row['source_path']) for row in chosen}
        core.base.observation.gzip_json(output/'selection.json.gz', dict(selected=chosen))
        core.base.follow.atomic_json(output/'proposal.json', proposal)
        (output/'source-freeze').mkdir(exist_ok=True)
        for source in sources:
            shutil.copyfile(source, output/'source-freeze'/Path(source).name)
        manifest = dict(version=VERSION, proposal=proposal, solver_policy=solver.POLICY,
                        sources=sources, inputs=inputs, originals=originals,
                        environment=prior['environment'], value_kernel=prior['value_kernel'],
                        tangent_kernel=prior['tangent_kernel'], cases=core.base.primary_cases(),
                        artifacts={name: core.base.il.sha256(output/name)
                                   for name in ('selection.json.gz', 'proposal.json')},
                        preparation_original_use='byte hashing only; no integration or observed fits',
                        dependency_use='completed numerical tools/environment; new fit inputs frozen separately',
                        scientific_decision='abstain')
        core.base.follow.atomic_json(output/'manifest.json', manifest)
        return verify(output)


def expected_limits(output, proposal):
    return dict(manifest_sha256=core.base.il.sha256(output/'manifest.json'),
                maximum_starts=proposal['maximum_starts'],
                maximum_native_sweeps=proposal['maximum_native_sweeps'], retries=0,
                approval='standing_analysis_roadmap')


def authorization(output, proposal):
    path = output/'authorization.json'
    if not path.exists() or core.base.load(path) != expected_limits(output, proposal):
        raise ValueError('frozen roadmap authorization/limits mismatch')


core.authorization = authorization


def record_limits(output, manifest):
    """Record standing roadmap authority once, without altering prior budgets."""
    if (output/'completion.json').exists():
        raise ValueError('completed trial is frozen')
    if (output/'authorization.json').exists():
        authorization(output, manifest['proposal'])
        return
    core.base.follow.atomic_json(output/'authorization.json', expected_limits(output, manifest['proposal']))


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
                              sweeps=manifest['proposal']['maximum_native_sweeps'],
                              runtime_hours=manifest['proposal']['estimate_range_hours'])))
    elif args.package_only:
        publish(output)
    elif args.detach:
        with core.shared.worker_lock(output) as lock:
            manifest = verify(output)
            record_limits(output, manifest)
            with (output/'worker.log').open('ab') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                        '--output', str(output), '--lock-fd', str(lock.fileno())],
                        pass_fds=(lock.fileno(),), start_new_session=True, stdout=log, stderr=log)
            core.base.follow.atomic_json(output/'worker.json', dict(pid=child.pid,
                manifest_sha256=core.base.il.sha256(output/'manifest.json')))
            print('Detached boundary-aware recovery worker', child.pid)
    else:
        if not (output/'authorization.json').exists():
            raise ValueError('frozen roadmap limits required')
        verify(output)
        core.run(output, args.lock_fd)
        publish(output)


if __name__ == '__main__':
    main()
