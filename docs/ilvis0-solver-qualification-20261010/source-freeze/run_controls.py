# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite software qualification matrix. Never read or fit archival measurements."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0_solver_controls as controls, ilvis0_exploratory as native
from lll import ilvis0_followup as follow, runtime

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT/'data/ilvis0-solver-qualification-20261010'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def verify(output):
    manifest = read(output/'manifest.json')
    if (manifest['identities'] != controls.identities() or manifest['maximum_starts'] != 34
            or manifest['maximum_actual_evaluations_per_start'] != 200
            or manifest['observed_fit_starts'] != 0):
        raise ValueError('software qualification scope changed')
    runtime.check_environment(manifest['environment'])
    for name, wanted in manifest['sources'].items():
        if sha(name) != wanted or sha(output/'source-freeze'/Path(name).name) != wanted:
            raise ValueError('software qualification source changed')
    return manifest


def prepare(output):
    if (output/'manifest.json').exists():
        return verify(output)
    # Frozen baseline implementation closure; no baseline data or originals opened.
    source_manifest = read(ROOT/'docs/ilvis0-highspeed-segments-20261008/manifest.json')
    sources = dict(source_manifest['sources'])
    for name, wanted in sources.items():
        if sha(name) != wanted:
            raise ValueError('existing frozen implementation changed')
    for path in (Path(__file__), Path(controls.__file__),
                 ROOT/'analysis/lll/ilvis0_estimator_controls.py',
                 ROOT/'analysis/lll/ilvis0_solver_refinement.py',
                 ROOT/'analysis/tests/test_ilvis0_solver_controls.py', HERE/'PLAN.md'):
        sources[str(path)] = sha(path)
    (output/'source-freeze').mkdir(exist_ok=True)
    for name in sources:
        shutil.copyfile(name, output/'source-freeze'/Path(name).name)
    manifest = dict(version=controls.VERSION, identities=controls.identities(), maximum_starts=34,
        maximum_actual_evaluations_per_start=200, observed_fit_starts=0, sources=sources,
        environment=runtime.numerical_environment(), kernel_source_sha256=sha(ROOT/'analysis/lll/ilvis0_native.c'),
        scientific_decision='abstain', qualification_scope='software controls only')
    follow.atomic_json(output/'manifest.json', manifest)
    return verify(output)


def starts(output, digest):
    path = output/'starts.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows) > 34 or len({r['identity'] for r in rows}) != len(rows)
            or any(r['number'] != i+1 or r['identity'] not in controls.identities()
                   or r['manifest_sha256'] != digest for i, r in enumerate(rows))):
        raise ValueError('invalid software start journal')
    return rows


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest = prepare(output); digest = sha(output/'manifest.json')
        if (output/'completion.json').exists():
            raise ValueError('completed qualification is frozen; package only')
        kernel, build = native.load_kernel(output/'kernel')
        results = []
        for identity in manifest['identities']:
            verify(output)
            target = output/(identity.replace('::', '-')+'.json')
            charged = starts(output, digest)
            if target.exists():
                cache = read(target)
                if cache['manifest_sha256'] != digest or cache['result_sha256'] != hashlib.sha256(
                        json.dumps(cache['result'], sort_keys=True, allow_nan=False).encode()).hexdigest():
                    raise ValueError('control cache integrity failure')
                results.append(cache['result']); continue
            if any(r['identity'] == identity for r in charged):
                result = dict(identity=identity, passed=False, error='interrupted charged control; no retry',
                              observed_fit_starts=0, scientific_decision='abstain')
            else:
                with (output/'starts.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(identity=identity, number=len(charged)+1,
                        manifest_sha256=digest, maximum_actual_evaluations=200), sort_keys=True)+'\n')
                    stream.flush(); os.fsync(stream.fileno())
                name, index = identity.split('::')
                try:
                    result = controls.run_one(name, int(index), kernel)
                except Exception as error:
                    result = dict(identity=identity, passed=False, error=type(error).__name__+': '+str(error),
                                  observed_fit_starts=0, scientific_decision='abstain')
            result_digest = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
            follow.atomic_json(target, dict(manifest_sha256=digest, result=result, result_sha256=result_digest))
            results.append(result)
            print(json.dumps(dict(identity=identity, passed=result['passed'], error=result.get('error'))), flush=True)
        verify(output)
        summary = dict(version=controls.VERSION, results=results, starts=len(starts(output, digest)),
            passed=sum(r['passed'] for r in results), actual_evaluations=sum(r.get('actual_evaluations', 0) for r in results),
            observed_fit_starts=0, kernel=build, scientific_decision='abstain')
        follow.atomic_json(output/'summary.json', summary)
        follow.atomic_json(output/'completion.json', dict(state='complete', manifest_sha256=digest,
            summary_sha256=sha(output/'summary.json'), starts=summary['starts'], observed_fit_starts=0))


def publish(output):
    verify(output); completion = read(output/'completion.json')
    if (completion['manifest_sha256'] != sha(output/'manifest.json')
            or completion['summary_sha256'] != sha(output/'summary.json')):
        raise ValueError('software completion receipt changed')
    for name in ('manifest.json', 'summary.json', 'completion.json', 'starts.jsonl'):
        shutil.copyfile(output/name, HERE/name)
    shutil.copytree(output/'source-freeze', HERE/'source-freeze', dirs_exist_ok=True)
    follow.atomic_json(HERE/'evidence-receipt.json', dict(version=controls.VERSION,
        observed_fit_starts=0, scientific_decision='abstain',
        artifacts={name: sha(HERE/name) for name in ('manifest.json', 'summary.json', 'completion.json', 'starts.jsonl')}))
    summary = read(output/'summary.json')
    print(f"Software qualification: {summary['passed']}/{summary['starts']} passed; zero observed starts.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-only', action='store_true')
    args = parser.parse_args()
    if not args.package_only:
        run(OUTPUT)
    publish(OUTPUT)
