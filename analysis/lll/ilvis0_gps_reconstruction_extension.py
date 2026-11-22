# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct two further preselected GPS streams with the original solver."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

from . import ilvis0_gps_extension_selection as selection, ilvis0_gps_reconstruction_pilot as pilot
from .ilvis0_matched_generated import RECOVERY
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-gps-reconstruction-extension-v1'
SCOPE = 'two further preselected NASA flight groups, GPS reconstruction only'
REQUEST = pilot.FOLDER+'gps-reconstruction-extension-qualification.json'
REPORT = pilot.FOLDER+'gps-reconstruction-extension-tests.xml'
SELECTION_SHA = '82a3fd18f674ae59621b81793f82a826c5037c8f78f7b7c683f3bd068a0e13c1'
RECOVERY_POLICY = dict(max_attempts_per_task=2, max_technical_interruptions=2,
    maximum_wall_s=600, minimum_free_bytes=1024**3, smoke_task_count=0)
TEST_FILES = ('analysis/tests/test_ilvis0_gps_extension_selection.py',
              'analysis/tests/test_ilvis0_gps_reconstruction_extension.py',
              'analysis/tests/test_ilvis0_gps_reconstruction_pilot.py')
TESTS = ('test_extension_selects_only_the_two_unused_groups',
         'test_extension_does_not_replace_a_failed_metadata_selection',
         'test_extension_uses_first_observed_tag_and_requires_both_methods',
         'test_extension_charges_the_frozen_position_and_iteration_allowance')


def position_limits(starts):
    return dict(native_calls=0, packet_visits=0, bound_calls=1,
                bound_steps=starts*pilot.MAX_ITERATIONS)


def evaluate_positions(task, context, *, solve=pilot.evaluate):
    limits = position_limits(task['position_starts'])
    if task['limits'] != limits:
        raise ValueError('the exact position and iteration allowance is required')
    context.charge(bound_calls=limits['bound_calls'], bound_steps=limits['bound_steps'])
    return solve(task, context)


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE:
        raise ValueError('the two-group receiver-only reconstruction is required')
    return evaluate_positions(task, context)


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), selection.PLAN, *TEST_FILES))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(), output=REQUEST, report=REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing GPS reconstruction allowance')
    raw = (root/selection.OUTPUT).read_bytes()
    if digest(raw) != SELECTION_SHA:
        raise ValueError('the frozen additional epoch list is required')
    selected = json.loads(raw)
    environment, deps = runtime_environment(), sources(root)
    binding, tests = checked(root, REQUEST, sources=deps, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=binding, qualification_tests=tests, recovery=recovery,
                     recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(selection=selection.OUTPUT, preflight_receipt=pilot.PREFLIGHT_RECEIPT, plan=selection.PLAN)
    rows = []
    with closing(ClosedStudy(root, 'data/'+pilot.parent.IDENTITY)) as study:
        if study.completion != selected['preflight'] or not study.summary['passed']:
            raise ValueError('the original satellite support check is required')
        for pick in selected['selected']:
            for task, block in pilot.position_blocks(study, pick):
                task['limits'] = position_limits(task['position_starts'])
                materials[task['input_key']] = gzip.compress(encoded(block), mtime=0)
                rows.append(task)
    if (selected['imu_fit_budget'] != 0 or selected['plan_sha256'] != digest((root/selection.PLAN).read_bytes())
            or selected['position_solve_starts'] != sum(row['position_starts'] for row in rows)):
        raise ValueError('GPS solve limits differ from the frozen selection')
    for key, material in materials.items():
        path = f'data/{ID}-inputs/{key}'
        pilot._write_equal(root/path, material)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, tasks=rows, inputs=inputs, sources=deps,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=300.)
    pilot._write_equal(root/f'data/{ID}-inputs/definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)['limits']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
