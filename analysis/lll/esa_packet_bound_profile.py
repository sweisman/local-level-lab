# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile the archived two-query ESA bound without substituting numerical sources."""

import argparse
import cProfile
from contextlib import closing
import io
import json
import os
from pathlib import Path
import pstats
import subprocess
import sys
import time
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ID = 'esa-packet-bound-profile-v1'
PARENT = 'data/esa-shape-prefix-preflight-v2-20261119'
PARENT_SHA = 'f38473c8e02a1e7c6827a38e797f612658773f2255a8329628ec76f74cf84b97'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_PACKET_BOUND_PROFILE_PLAN.md'
REQUEST = BASE+'esa-packet-bound-profile-qualification.json'
REPORT = BASE+'esa-packet-bound-profile-tests.xml'
RESULT = BASE+'esa-packet-bound-profile-result.json'
TEST = 'analysis/tests/test_esa_packet_bound_profile.py'
TESTS = ('test_profile_keeps_result_and_records_failed_work',
         'test_profile_agreement_requires_equal_bound_bytes_and_work')
ADAPTER = 'analysis/lll/esa_packet_bound_profile.py'
MODELS = ('sphere_still', 'flat_still')
ALLOWANCE = 180.
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=1280)


def profile_once(calculate, *, trace=True):
    profiler = cProfile.Profile() if trace else None
    value, error = None, None
    wall, cpu = time.monotonic(), time.process_time()
    try:
        value = profiler.runcall(calculate) if profiler is not None else calculate()
    except Exception as caught:
        error = dict(type=type(caught).__name__, message=str(caught))
    wall, cpu = time.monotonic()-wall, time.process_time()-cpu
    if profiler is None:
        return value, dict(wall_s=wall, cpu_s=cpu, error=error)
    stats = pstats.Stats(profiler)
    functions = [dict(file=Path(key[0]).name, line=key[1], function=key[2], calls=row[1],
                      self_s=row[2], inclusive_s=row[3]) for key, row in stats.stats.items()]
    profile = dict(wall_s=wall, cpu_s=cpu, total_calls=stats.total_calls, error=error,
                   by_self=sorted(functions, key=lambda row: -row['self_s'])[:30],
                   by_inclusive=sorted(functions, key=lambda row: -row['inclusive_s'])[:40])
    return value, profile


def equivalent_report(actual, raw, gold):
    from lll.studies.artifacts import digest

    return bool(actual and actual['passed'] and raw is not None and digest(raw) == gold['sha256']
                and actual['work'] == gold['work'] and actual.get('packet_count') == gold.get('packet_count'))


def qualification(root, *, verify):
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.dependencies import source_closure
    from lll.studies.qualification import checked, request

    names = source_closure(root, (ADAPTER, PLAN, TEST))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=names, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=names, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return names, environment


def prepare(root):
    from lll.ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from lll.ilvis0_matched_observed_inputs import _write_equal
    from lll.studies.artifacts import digest, encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('reuse the existing isolated profile and allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, PARENT)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_SHA or not parent.summary['passed']
                or parent.manifest['environment'] != env or set(parent.rows) != set(MODELS)):
            raise ValueError('two exact archived passes under the same runtime required')
        hashes = parent.manifest['sources']
        compiled = {k: v for k, v in hashes.items() if Path(k).suffix in ('.c', '.cc', '.cpp', '.h', '.hpp')}
        if any(digest((root/k).read_bytes()) != v for k, v in compiled.items()):
            raise ValueError('compiled source files differ from the archived calculation')
        buffer = io.BytesIO()
        with ZipFile(buffer, 'w') as bundle:
            for name, sha in sorted(hashes.items()):
                bundle.writestr(ZipInfo(name), parent.read('source-freeze/'+name, expected=sha, raw=True),
                                compress_type=ZIP_DEFLATED)
        staged = dict(frozen_python_native=buffer.getvalue(), parent=encoded(dict(source_hashes=hashes,
                      source_manifest=PARENT_SHA, compiled=compiled)))
        scope = parent.manifest['scope']
        tasks = []
        for model in MODELS:
            key = model+'-metadata'
            for name in (model, key):
                staged[name] = parent.input(name, raw=True)
            original = parent.envelope(model)
            bound_bytes = parent.artifact(model, 'bounds.json', raw=True)
            result = original['result']
            if original['charged'] != LIMITS or result['packet_count'] != 470 or len(json.loads(bound_bytes)) != 2:
                raise ValueError('the original bound must contain two queries over the fixed packet prefix')
            staged[model+'-gold'] = encoded(dict(sha256=digest(bound_bytes), work=result['work'], packet_count=470))
            tasks.append({k: v for k, v in parent.tasks[model].items() if k not in ('index', 'shard')})
    staged.update(recovery=recovery, recovery_tests=tests,
                  recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=400)))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=REPORT)
    for name, data in staged.items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, data)
        inputs[name] = path
    definition = dict(id=ID, scope=scope, adapter=ADAPTER, sources=sorted(set(sources)|set(compiled)), inputs=inputs,
                      tasks=tasks, workers=1, threads=1, maximum_wall_s=400.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def archived_replay(task, context, *, trace=True, replacement=None, artifact_prefix=''):
    from lll.esa_tangent_remainder import frozen_workspace
    from lll.studies.artifacts import digest

    name = task['identity']
    if name not in MODELS or task['limits'] != LIMITS or task['payload'] != {'model': name}:
        raise ValueError('the original sealed prefix task required')
    binding = json.loads(context.input_path('parent').read_bytes())
    gold = json.loads(context.input_path(name+'-gold').read_bytes())
    if (binding['source_manifest'] != PARENT_SHA or
            any(context.manifest['sources'].get(k) != v for k, v in binding['compiled'].items())):
        raise ValueError('unchanged source snapshot required before evaluating')
    with frozen_workspace(context) as work:
        if replacement is not None:
            from lll.studies.artifacts import safe_path

            archived = safe_path(work, replacement)
            source = safe_path(context.root/'source-freeze', replacement).read_bytes()
            if (digest(archived.read_bytes()) != binding['source_hashes'][replacement]
                    or digest(source) != context.manifest['sources'][replacement]
                    or digest(source) == binding['source_hashes'][replacement]):
                raise ValueError('one verified source substitution required')
            archived.write_bytes(source)
        arguments = dict(task=task, root=str(context.root), manifest=context.manifest,
                         trace=trace,
                         inputs={k: str(context.input_path(k).resolve()) for k in (name, name+'-metadata')})
        argument_file = work/'request.json'
        argument_file.write_text(json.dumps(arguments))
        subprocess.run([sys.executable, str(context.root/'source-freeze'/ADAPTER), '_profile_archived',
                        str(argument_file)], cwd=work, env={**os.environ, 'PYTHONPATH': str(work/'analysis')}, check=True)
        profile = json.loads((work/'profile.json').read_bytes())
        actual = profile.pop('original_result')
        output = work/'bounds.json'
        bound = output.read_bytes() if output.is_file() else None
        for artifact in ('compiler.json', 'reference.json', 'bounds.json'):
            if (work/artifact).is_file():
                context.save_bytes(artifact_prefix+artifact, (work/artifact).read_bytes())
    return dict(model=name, passed=equivalent_report(actual, bound, gold), profile=profile,
                original_result=actual, archived_bounds_sha256=gold['sha256'],
                profile_bounds_sha256=digest(bound) if bound is not None else None, scientific_decision='abstain')


def evaluate(task, context):
    context.charge(bound_calls=1, bound_steps=LIMITS['bound_steps'])
    result = archived_replay(task, context)
    context.save('timing-profile.json', result)
    return result


def archived_child(path):
    from unittest.mock import patch
    from lll import esa_shape_prefix_preflight as original
    from lll import ilvis0_native_prefix
    from lll.studies.artifacts import encoded

    arguments = json.loads(path.read_bytes())
    task = arguments['task']
    target = path.parent

    class ProfileContext:
        root = Path(arguments['root'])
        shard = task['shard']
        manifest = arguments['manifest']
        reserved = False

        def input_path(self, key):
            return Path(arguments['inputs'][key])

        def charge(self, **counts):
            if self.reserved or counts != dict(bound_calls=1, bound_steps=LIMITS['bound_steps']):
                raise ValueError('one previously reserved prefix bound expected')
            self.reserved = True

        def save(self, name, value):
            if name not in ('compiler.json', 'reference.json', 'bounds.json') or (target/name).exists():
                raise ValueError('unexpected archive output')
            (target/name).write_bytes(encoded(value))

    procedure = ilvis0_native_prefix.enclose_many
    timing = None

    def timed(*args, **options):
        nonlocal timing
        if timing is not None or options['maximum_seconds'] != 50.:
            raise ValueError('only the original preflight bound is profiled')
        options['maximum_seconds'] = ALLOWANCE
        result, timing = profile_once(lambda: procedure(*args, **options), trace=arguments.get('trace', True))
        if timing['error']:
            raise ValueError(timing['error']['message'])
        return result

    result, preflight_error = None, None
    cpu, wall = time.process_time(), time.monotonic()
    with patch.object(ilvis0_native_prefix, 'enclose_many', timed):
        try:
            result = original.evaluate(task, ProfileContext())
        except Exception as caught:
            preflight_error = dict(type=type(caught).__name__, message=str(caught))
    (target/'profile.json').write_bytes(encoded(dict(original_result=result, bound=timing, error=preflight_error,
        evaluator_cpu_s=time.process_time()-cpu, evaluator_wall_s=time.monotonic()-wall)))


def report(root):
    from lll.ilvis0_matched_observed_inputs import _write_equal
    from lll.studies.artifacts import encoded
    from lll.studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != set(MODELS):
            raise ValueError('both original task outcomes required')
        results = {}
        for identity in MODELS:
            record = study.envelope(identity)
            result = record['result']
            if record['status'] != 'complete' or record['charged'] != LIMITS or result != study.artifact(identity, 'timing-profile.json'):
                raise ValueError('profile must match its terminal charge and seal')
            results[identity] = result
        result = dict(results=results, completion=study.completion, matched=sum(row['passed'] for row in results.values()))
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('matched', 'completion')}


if __name__ == '__main__':
    if sys.argv[1:2] == ['_profile_archived'] and len(sys.argv) == 3:
        archived_child(Path(sys.argv[2]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('request', 'prepare', 'report'))
        action = parser.parse_args().action
        root = Path.cwd()
        value = qualification(root, verify=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
        print(json.dumps(value, sort_keys=True))
