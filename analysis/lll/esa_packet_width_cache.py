# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare one exact source-bound optimization against its sealed predecessor."""

import argparse
from contextlib import closing
import json
from pathlib import Path
from statistics import median

from .esa_packet_bound_profile import BASE, MODELS, LIMITS as ONE_BOUND, archived_replay
from .esa_packet_bound_profile import ID as PROFILE
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-packet-width-cache-v1'
PLAN = BASE+'ESA_PACKET_WIDTH_CACHE_PLAN.md'
RESULT = BASE+'esa-packet-width-cache-result.json'
REQUEST = BASE+'esa-packet-width-cache-qualification.json'
REPORT = BASE+'esa-packet-width-cache-tests.xml'
SOURCE = 'analysis/lll/ilvis0_dyadic_source.py'
TESTS = ('test_affine_radius_reuses_fixed_box_widths_and_checks_its_order',
         'test_affine_radius_exactly_reproduces_fraction_reference[nonbinary]',
         'test_mean_value_radius_exactly_reproduces_fraction_reference[0]',
         'test_profile_agreement_requires_equal_bound_bytes_and_work')
LIMITS = {key: value*2 for key, value in ONE_BOUND.items()}


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, SOURCE,
        'analysis/tests/test_ilvis0_dyadic_source.py', 'analysis/tests/test_esa_packet_bound_profile.py'))
    env = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env


def prepare(root):
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('use the existing timed exact-computation comparison')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PROFILE)) as profile:
        binding = profile.input('parent')
        compiled = binding['compiled']
        if (not profile.summary['passed'] or profile.manifest['environment'] != env
                or set(profile.rows) != set(MODELS) or digest((root/SOURCE).read_bytes()) == binding['source_hashes'][SOURCE]
                or any(digest((root/name).read_bytes()) != value for name, value in compiled.items())):
            raise ValueError('exact complete prefix profile and one changed Python source required')
        scope = profile.manifest['scope']
        keys = ['parent', 'frozen_python_native']
        tasks = []
        for model in MODELS:
            prior = profile.envelope(model)['result']
            if prior['archived_bounds_sha256'] != prior['profile_bounds_sha256'] or not prior['passed']:
                raise ValueError('the unmodified calculation must reproduce the archived bound')
            keys.extend((model, model+'-metadata', model+'-gold'))
            task = {k: v for k, v in profile.tasks[model].items() if k not in ('index', 'shard')}
            tasks.append(dict(task, limits=LIMITS))
        staged = {key: profile.input(key, raw=True) for key in keys}
        staged['profile_closure'] = encoded(profile.completion)
    staged.update(recovery=recovery, recovery_tests=tests,
                  recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=420)))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=REPORT)
    for key, value in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=scope, sources=sorted(set(sources)|set(compiled)), inputs=inputs,
                      adapter=Path(__file__).relative_to(root).as_posix(), tasks=tasks, workers=2,
                      threads=1, maximum_wall_s=420.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    if task['limits'] != LIMITS or task['identity'] not in MODELS:
        raise ValueError('the two complete fixed-prefix replays require separate charges')
    control = dict(task, limits=ONE_BOUND)
    options = {'archived': None, 'cache': SOURCE}
    order = tuple(options) if task['identity'] == MODELS[0] else tuple(reversed(options))
    variants = {}
    for key in order:
        context.charge(bound_calls=1, bound_steps=ONE_BOUND['bound_steps'])
        variants[key] = archived_replay(control, context, trace=False, replacement=options[key], artifact_prefix=key+'-')
    passed = all(row['passed'] for row in variants.values())
    ratio = (variants['archived']['profile']['bound']['cpu_s']/variants['cache']['profile']['bound']['cpu_s']
             if passed else None)
    value = dict(model=task['identity'], variants=variants, order=order, passed=passed, cpu_ratio=ratio,
                 scientific_decision='abstain')
    context.save('width-cache.json', value)
    return value


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != set(MODELS):
            raise ValueError('both terminal benchmark pairs required')
        rows = {}
        for model in MODELS:
            envelope = study.envelope(model)
            result = envelope['result']
            if (envelope['status'] != 'complete' or envelope['charged'] != LIMITS
                    or result != study.artifact(model, 'width-cache.json')):
                raise ValueError('the benchmark is missing a complete sealed pair')
            rows[model] = result
        ratios = [row['cpu_ratio'] for row in rows.values()]
        qualified = all(ratio is not None for ratio in ratios) and min(ratios) >= 1. and median(ratios) > 1.05
        output = dict(rows=rows, speed_qualified=qualified, completion=study.completion)
    _write_equal(root/RESULT, encoded(output))
    return dict(speed_qualified=qualified, cpu_ratios=ratios)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
