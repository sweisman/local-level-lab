# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite one-case local nonlinear compatibility check at a frozen radius."""

from pathlib import Path

from . import generated_joint_profile_replay as base
from . import generated_joint_profile_replay_v2 as preceding

ID = 'generated-local-profile-v1-20261118'
SCOPE = 'one sealed generated case; radius-0.1 future-path compatibility control'
PLAN = 'docs/prediction-observed-development/GENERATED_LOCAL_PROFILE_PLAN.md'
RADIUS = .1


def recipe(source):
    return dict(preceding.recipe(source),
                version='generated-local-profile-v1', trust_radius=RADIUS)


def evaluate(task, context):
    return base.evaluate_with_policy(task, context, scope=SCOPE,
        recipe_factory=recipe, point_policy=preceding.feasible_native_point,
        trust_radius=RADIUS)


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_local_profile_study.py',
        'analysis/lll/generated_joint_profile_replay.py',
        'analysis/lll/generated_joint_profile_replay_v2.py',
        'analysis/tests/test_generated_local_profile_study.py',
        'analysis/tests/test_generated_joint_profile_replay.py',
        'analysis/tests/test_generated_joint_profile_replay_v2.py',
        'analysis/tests/test_generated_joint_replay_source.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return preceding.required_tests() + (
        'test_local_radius_is_fixed_and_finite',)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request-source','request-recovery','prepare','run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request-source':
        result = preceding.request_qualification(args.root, study_id=ID,
                                                 source_list=qualification_sources)
    elif args.action == 'request-recovery':
        result = preceding.request_qualification(args.root, recovery=True,
            study_id=ID, source_list=qualification_sources)
    elif args.action == 'prepare':
        result = preceding.prepare(args.root, study_id=ID, scope=SCOPE,
            recipe_factory=recipe, source_list=qualification_sources,
            tests=required_tests, prior_id=preceding.ID,
            adapter='analysis/lll/generated_local_profile_study.py')
    else:
        from .ilvis0_control_shards import launch
        result = launch(Path(args.root).resolve()/'data'/ID, reserved_threads=0)
    print(result)


if __name__ == '__main__':
    main()
