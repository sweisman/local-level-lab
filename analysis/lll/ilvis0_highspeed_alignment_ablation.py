# SPDX-License-Identifier: AGPL-3.0-or-later
"""The published high-speed selection repeated without the navigation-status requirement.

One retained source is one task. Every other published selection rule is kept.
No gyro residual is inspected and no Earth model is evaluated.
"""
import argparse
import json
from pathlib import Path

from . import ilvis0_segments as segments
from .ilvis0_distance_inventory_study import CONTEXTS, INVENTORY, evaluate_task

ID = 'ilvis0-highspeed-alignment-ablation-v1'
FOLDER = 'docs/ilvis0-highspeed-alignment-ablation/'
ADAPTER = 'analysis/lll/ilvis0_highspeed_alignment_ablation.py'
TEST = 'analysis/tests/test_ilvis0_highspeed_alignment_ablation.py'
PARENT = 'docs/ilvis0-distance-inventory/study-definition.json'
PLAN = FOLDER+'PLAN.md'
POLICY_PATH = FOLDER+'policy.json'
REQUEST = FOLDER+'qualification.json'
TEST_REPORT = FOLDER+'tests.xml'
RECOVERY = 'docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'
SCOPE = '232 retained originals; published high-speed selection without the alignment requirement; no Earth-model fits'
POLICY = dict(segments.POLICY, version=ID, require_alignment_status=False)
WALL_S = 4*3600
TESTS = ('test_policy_changes_only_the_alignment_requirement',
         'test_an_unaligned_sample_no_longer_splits_a_level_interval',
         'test_tasks_are_the_232_sealed_sources_with_no_model_allowance')


def tasks(root):
    """The 232 sealed source bindings of the earlier inventory, unchanged."""
    parent = json.loads((Path(root)/PARENT).read_bytes())
    rows = parent['tasks']
    if (len(rows) != 232 or len({row['identity'] for row in rows}) != 232
            or any(set(row['limits'].values()) != {0} for row in rows)):
        raise ValueError('the complete 232-source inventory is required')
    return sorted(rows, key=lambda row: row['identity'])


def code_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (ADAPTER, TEST, 'analysis/tests/test_ilvis0_segments.py'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=code_sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS as RECOVERY_TESTS, qualification_sources

    root = Path(root).resolve()
    if (root/'data'/ID).exists():
        raise ValueError('the existing inventory must be retained')
    environment = runtime_environment()
    code = code_sources(root)
    qualification, tests = checked(root, REQUEST, sources=code, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=RECOVERY_TESTS, minimum_tests=len(RECOVERY_TESTS))
    rows = tasks(root)
    for row in rows:
        source = safe_path(root, row['source_path'])
        if not source.is_file() or source.stat().st_size != row['compressed_bytes']:
            raise ValueError('retained source missing or changed size')
    policy = root/POLICY_PATH
    raw = encoded(POLICY)
    if policy.is_file():
        if policy.read_bytes() != raw:
            raise ValueError('frozen selection policy changed')
    else:
        atomic(policy, raw)
    inputs = dict(plan=PLAN, parent=PARENT, inventory=INVENTORY, contexts=CONTEXTS, policy=POLICY_PATH)
    folder = root/'data'/(ID+'-inputs')
    folder.mkdir(parents=True, exist_ok=True)
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(max_attempts_per_task=2,
            max_technical_interruptions=8, maximum_wall_s=WALL_S, minimum_free_bytes=1024**3,
            smoke_task_count=0)))
    for key, value in staged.items():
        path = folder/key
        if path.is_file() and path.read_bytes() != value:
            raise ValueError('prepared study materials changed')
        if not path.is_file():
            atomic(path, value)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=sorted(set(code+[PLAN])),
        inputs=inputs, tasks=rows, workers=1, threads=1, maximum_wall_s=WALL_S)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=ID, sources=len(rows), limits=manifest['limits'], allocation=manifest['allocation'])


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE:
        raise ValueError('unchanged selection-only scope required')
    return evaluate_task(task, context, POLICY)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
