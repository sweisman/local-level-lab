# SPDX-License-Identifier: AGPL-3.0-or-later
"""Feasible-bound continuation of the sealed generated joint-profile replay."""

from pathlib import Path

from . import generated_joint_profile_replay as base

ID = 'generated-joint-profile-replay-v2-20261117'
SCOPE = 'one sealed generated case; exact-boundary joint profile continuation'
PLAN = 'docs/prediction-observed-development/GENERATED_JOINT_PROFILE_REPLAY_V2_PLAN.md'
QUAL = 'docs/prediction-observed-development/qualification/'


def recipe(source):
    return dict(base.study_recipe(source),
                version='generated-joint-profile-replay-v2',
                boundary_policy='normalized-exact-boundary-5e-13-v1')


def feasible_native_point(point, correction):
    import numpy as np
    p = np.asarray(point, float)
    d = np.asarray(correction, float)
    if (p.ndim != 1 or p.shape != d.shape or not np.all(np.isfinite(p))
            or not np.all(np.isfinite(d)) or np.any(abs(p) > 1)):
        raise ValueError('finite complete feasible profile coordinates required')
    raw = p+d
    overshoot = max(0., float(np.max(raw-1)), float(np.max(-1-raw)))
    if not np.all(np.isfinite(raw)) or overshoot > 5e-13:
        raise ValueError('profiled calibration exceeds existing normalized bounds')
    return np.clip(raw, -1., 1.)


def evaluate(task, context):
    return base.evaluate_with_policy(task, context, scope=SCOPE,
        recipe_factory=recipe, point_policy=feasible_native_point)


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_joint_profile_replay_v2.py',
        'analysis/lll/generated_joint_profile_replay.py',
        'analysis/tests/test_generated_joint_profile_replay_v2.py',
        'analysis/tests/test_generated_joint_profile_replay.py',
        'analysis/tests/test_generated_joint_replay_source.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return base.required_tests() + (
        'test_tiny_roundoff_is_projected_to_existing_boundary',
        'test_material_boundary_violation_is_rejected',
        'test_v2_keeps_saved_fit_and_finite_task_limits')


def request_qualification(root, *, recovery=False, study_id=ID,
                          source_list=None):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources as recovery_sources
    root = Path(root).resolve()
    stem = 'recovery' if recovery else 'source'
    sources = qualification_sources(root) if source_list is None else source_list(root)
    return request(root, sources=recovery_sources(root) if recovery else sources,
        environment=runtime_environment() if recovery else environment(),
        output=QUAL+stem+'-'+study_id+'-request.json',
        report=QUAL+stem+'-'+study_id+'-tests.xml')


def prepare(root, *, study_id=ID, scope=SCOPE, recipe_factory=recipe,
            source_list=qualification_sources, tests=required_tests,
            prior_id=base.ID, adapter='analysis/lll/generated_joint_profile_replay_v2.py'):
    import shutil
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .generated_joint_replay_source import verify_source
    from .ilvis0_control_shards import runtime_environment, verify_completion
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources as recovery_sources, REQUIRED_TESTS
    root = Path(root).resolve()
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=1, threads=1):
        raise ValueError('one-thread numerical guard required')
    if shutil.disk_usage(root).free < 2*1024**3:
        raise ValueError('2 GiB free disk required')
    prior = verify_completion(root/'data'/prior_id)
    if (prior['state'] != 'terminal' or prior['completed'] != 1
            or prior['passed'] is not False):
        raise ValueError('sealed prior technical failure required')
    source_request, source_report = checked(root, QUAL+'source-'+study_id+'-request.json',
        sources=source_list(root), environment=env,
        required_tests=tests(), minimum_tests=len(tests()))
    recovery_request, recovery_report = checked(root, QUAL+'recovery-'+study_id+'-request.json',
        sources=recovery_sources(root), environment=runtime_environment(),
        required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    source = verify_source(root, expected_environment=env)
    r = recipe_factory(source)
    directory = root/'data'/(study_id+'-inputs')
    if directory.exists() or (root/'data'/study_id).exists():
        raise ValueError('fresh v2 replay study required')
    directory.mkdir(parents=True)
    values = dict(recipe=encoded(r), environment=encoded(env),
                  source_qualification_request=source_request,
                  source_qualification_report=source_report,
                  recovery_qualification_request=recovery_request,
                  recovery_qualification_report=recovery_report)
    inputs = {}
    for key, raw in values.items():
        path = directory/key
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=study_id, scope=scope,
        adapter=adapter,
        sources=source_list(root), inputs=inputs, tasks=base.tasks(r),
        workers=1, threads=1, maximum_wall_s=3600)
    atomic(directory/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+study_id, allocation=manifest['allocation'],
                limits=manifest['limits'])


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request-source','request-recovery','prepare','run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request-source':
        result = request_qualification(args.root)
    elif args.action == 'request-recovery':
        result = request_qualification(args.root, recovery=True)
    elif args.action == 'prepare':
        result = prepare(args.root)
    else:
        from .ilvis0_control_shards import launch
        result = launch(Path(args.root).resolve()/'data'/ID, reserved_threads=0)
    print(result)


if __name__ == '__main__':
    main()
