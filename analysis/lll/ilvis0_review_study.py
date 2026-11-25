# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared freeze steps for the small review studies that run no Earth-model fit."""
from pathlib import Path

RECOVERY = 'docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'
RECOVERY_POLICY = dict(max_attempts_per_task=2, max_technical_interruptions=8,
                       minimum_free_bytes=1024**3, smoke_task_count=0)
NO_MODEL_WORK = dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)


def code_sources(root, *seeds):
    from .studies.dependencies import source_closure

    return source_closure(root, seeds)


def request(root, *, sources, output, report):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources, environment=runtime_environment(), output=output, report=report)


def prepare(root, *, identity, scope, adapter, plan, sources, qualification, tests, inputs, tasks, wall_s):
    """Check the software and recovery qualifications, stage them and freeze one single-worker study."""
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    root = Path(root).resolve()
    if (root/'data'/identity).exists():
        raise ValueError('the existing study must be retained')
    environment = runtime_environment()
    bound, report = checked(root, qualification, sources=sources, environment=environment,
                            required_tests=tests, minimum_tests=len(tests))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(inputs, plan=plan)
    folder = root/'data'/(identity+'-inputs')
    folder.mkdir(parents=True, exist_ok=True)
    staged = dict(qualification=bound, qualification_tests=report, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=wall_s)))
    for key, value in staged.items():
        path = folder/key
        if path.is_file() and path.read_bytes() != value:
            raise ValueError('prepared study materials changed')
        if not path.is_file():
            atomic(path, value)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity, scope=scope, adapter=adapter, sources=sorted(set(sources+[plan])),
        inputs=inputs, tasks=tasks, workers=1, threads=1, maximum_wall_s=wall_s)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=identity, tasks=len(tasks), limits=manifest['limits'], allocation=manifest['allocation'])
