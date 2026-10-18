# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate finite trial of actual-position stability on saved primary endpoints."""
import argparse
import copy
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

from lll import ilvis0_solver_position as solver
from lll.ilvis0_recovery_diagnosis import load_completed

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path('docs/ilvis0-position-stability-trial-20261013')
OUTPUT = Path('data/ilvis0-position-stability-trial-20261013')
ENDPOINTS = ROOT/'data/ilvis0-boundary-recovery-trial-20261012'
VERSION = 'ilvis0-position-stability-worker-v1'
spec = importlib.util.spec_from_file_location('ilvis0_position_trial_core',
                                             Path(__file__).with_name('ilvis0_boundary_worker.py'))
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)
core = wrapper.core
wrapper.VERSION = core.VERSION = VERSION
wrapper.GUIDE = core.GUIDE = GUIDE
wrapper.OUTPUT = core.OUTPUT = OUTPUT
wrapper.solver = core.solver = solver
fit_task_from_reference = wrapper.fit_task


def endpoint_reference(task, summary):
    primary = task['identity'].rsplit('::', 1)[0]+'::primary'
    fit = summary['results'][primary]
    required = ('active_parameters', 'normalized_parameters', 'residual_sum_squares')
    if any(key not in fit for key in required):
        raise ValueError('saved primary endpoint incomplete')
    return copy.deepcopy({key: fit[key] for key in required})


def fit_task(output, task, reference, *args):
    summary, _ = load_completed(ENDPOINTS)
    fit = fit_task_from_reference(output, task, endpoint_reference(task, summary), *args)
    fit['start_source'] = 'completed boundary-trial primary endpoint; fixed perturbation for repeats'
    return fit


core.fit_task = fit_task
prior_verify = wrapper.verify


def completed_endpoints(output):
    """Verify the completed boundary study with its actual 600/2 call limits."""
    summary, hashes = load_completed(output)
    manifest = core.base.load(output/'manifest.json')
    proposal = manifest['proposal']
    if (proposal['maximum_fit_sweeps'] != 600 or proposal['maximum_diagnostic_sweeps'] != 2
            or proposal['maximum_starts'] != summary['starts']
            or set(proposal['identities']) != set(summary['results'])):
        raise ValueError('completed endpoint allowance/scope mismatch')
    core.shared.clock.residuals.check_hashes(manifest['sources'])
    core.base.runtime.check_environment(manifest['environment'])
    for name, digest in manifest['sources'].items():
        if core.base.il.sha256(output/'source-freeze'/Path(name).name) != digest:
            raise ValueError('completed endpoint source snapshot mismatch')
    for name, digest in manifest['artifacts'].items():
        if core.base.il.sha256(output/name) != digest:
            raise ValueError('completed endpoint artifact mismatch')
    book = core.journal.Ledger(output, hashes['manifest.json'], proposal['identities'],
                               fit_limit=600, diagnostic_limit=2)
    book.read('starts')
    book.read('sweeps')
    for identity, fit in summary['results'].items():
        if (fit['fit_native_sweeps'] != book.count(identity, 'fit')
                or fit['diagnostic_native_sweeps'] != book.count(identity, 'diagnostic')):
            raise ValueError('completed endpoint fit charge mismatch')
    return manifest, summary, hashes


def verify(output, originals=False):
    manifest = prior_verify(output, originals=originals)
    required = (Path(__file__), Path(solver.__file__),
                ROOT/'analysis/tests/test_ilvis0_solver_position.py',
                ROOT/'analysis/tests/test_ilvis0_position_stability_worker.py')
    if any(str(path.resolve()) not in manifest['sources'] for path in required):
        raise ValueError('position-stability source qualification incomplete')
    if str(ENDPOINTS/'summary.json') not in manifest['inputs']:
        raise ValueError('saved endpoint input not frozen')
    return manifest


def prepare(output):
    with core.shared.worker_lock(output):
        wrapper.validate_controls(core.base.load(GUIDE/'control-receipt.json'))
        if (output/'manifest.json').exists():
            return verify(output)
        if (output/'starts.jsonl').exists():
            raise ValueError('unmarked charge journal')
        for directory, name in ((core.SUBSET, 'preparation-receipt.json'),
                                (core.BASELINE, 'evidence-receipt.json')):
            receipt = core.base.load(directory/name)
            core.shared.clock.audit.verify_artifacts(directory, receipt)
            core.shared.clock.residuals.check_hashes(receipt.get('sources', {}))
        prior, endpoints, endpoint_hashes = completed_endpoints(ENDPOINTS)
        baseline = core.base.load(core.BASELINE/'summary.json.gz')
        subset = core.base.load(core.SUBSET/'selection-summary.json')
        proposal = core.planning.build(baseline['results'], subset['selected_segment_ids'])
        proposal.update(solver_version=solver.VERSION, x_scale='physical-bound normalized; unscaled BVLS',
                        execution_authority='standing_analysis_roadmap', observed_allowance_authorized=True,
                        start_source='completed boundary-trial primary endpoint; fixed perturbation for repeats',
                        prior_endpoint_manifest_sha256=endpoint_hashes['manifest.json'])
        for task in proposal['tasks']:
            task['start'] = proposal['start_source']
            endpoint_reference(task, endpoints)
        selection = core.base.load(core.BASELINE/'selection.json.gz')
        indexed = {row['segment']['segment_id']: row for row in selection['selected']}
        chosen = [indexed[sid] for sid in proposal['selected_segment_ids']]
        sources = dict(prior['sources'])
        sources.update(core.base.load(GUIDE/'control-receipt.json')['sources'])
        core.shared.clock.residuals.check_hashes(sources)
        if len({Path(path).name for path in sources}) != len(sources):
            raise ValueError('source snapshot filename collision')
        inputs = {str(ENDPOINTS/name): digest for name, digest in endpoint_hashes.items()}
        inputs[str(ENDPOINTS/'completion.json')] = core.base.il.sha256(ENDPOINTS/'completion.json')
        groups = ((core.BASELINE, ('summary.json.gz', 'selection.json.gz', 'manifest.json',
                                    'fit-manifest.json', 'completion.json', 'evidence-receipt.json')),
                  (core.SUBSET, ('preparation-receipt.json', 'selection-summary.json', 'representative-subset.csv')),
                  (GUIDE, ('PLAN.md', 'control-receipt.json')))
        for directory, names in groups:
            for name in names:
                path = (directory/name).resolve()
                inputs[str(path)] = core.base.il.sha256(path)
        context = ROOT/'data/ilvis0-followup-20261007/summary.json'
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
                        preparation_original_use='byte hashing only; no observed fits',
                        dependency_use='sealed primary endpoints and numerical tools; new finite freeze',
                        scientific_decision='abstain')
        core.base.follow.atomic_json(output/'manifest.json', manifest)
        return verify(output)


wrapper.verify = verify
wrapper.prepare = prepare


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
        print('Prepared position-stability trial:', manifest['proposal']['maximum_starts'], 'starts,',
              manifest['proposal']['maximum_native_sweeps'], 'sweeps maximum')
    elif args.package_only:
        wrapper.publish(output)
    elif args.detach:
        with core.shared.worker_lock(output) as lock:
            manifest = verify(output)
            wrapper.record_limits(output, manifest)
            with (output/'worker.log').open('ab') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                    '--output', str(output), '--lock-fd', str(lock.fileno())],
                    pass_fds=(lock.fileno(),), start_new_session=True, stdout=log, stderr=log)
            core.base.follow.atomic_json(output/'worker.json', dict(pid=child.pid,
                manifest_sha256=core.base.il.sha256(output/'manifest.json')))
            print('Detached position-stability worker', child.pid)
    else:
        if not (output/'authorization.json').exists():
            with core.shared.worker_lock(output):
                wrapper.record_limits(output, verify(output))
        core.run(output, args.lock_fd)
        wrapper.publish(output)


if __name__ == '__main__':
    main()
