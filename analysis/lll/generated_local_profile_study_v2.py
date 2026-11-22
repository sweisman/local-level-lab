# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receipt-corrected finite local profile of one sealed generated path."""

from pathlib import Path

from . import generated_joint_profile_replay as base
from . import generated_joint_profile_replay_v2 as lifecycle
from . import generated_local_profile_study as previous

ID = 'generated-local-profile-v2-20261118'
SCOPE = 'one sealed generated case; receipt-corrected radius-0.1 local profile'
PLAN = 'docs/prediction-observed-development/GENERATED_LOCAL_PROFILE_V2_PLAN.md'


def recipe(source):
    return dict(previous.recipe(source),
                version='generated-local-profile-v2',
                accounting='sealed-future-read-v1')


def evaluate(task, context):
    return base.evaluate_with_policy(task, context, scope=SCOPE,
        recipe_factory=recipe, point_policy=lifecycle.feasible_native_point,
        trust_radius=previous.RADIUS)


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/generated_local_profile_study_v2.py',
        'analysis/lll/generated_joint_profile_replay.py',
        'analysis/lll/generated_local_profile_study.py',
        'analysis/tests/test_generated_local_profile_study_v2.py',
        'analysis/tests/test_generated_local_profile_study.py',
        'analysis/tests/test_generated_joint_profile_replay.py',
        'analysis/tests/test_generated_joint_profile_replay_v2.py',
        'analysis/tests/test_generated_joint_replay_source.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', PLAN])


def required_tests():
    return previous.required_tests() + (
        'test_replay_does_not_charge_reading_sealed_future',
        'test_corrected_study_keeps_same_radius_and_no_new_fits')


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request-source','request-recovery','prepare','run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'request-source':
        result = lifecycle.request_qualification(args.root, study_id=ID,
                                                  source_list=qualification_sources)
    elif args.action == 'request-recovery':
        result = lifecycle.request_qualification(args.root, recovery=True,
            study_id=ID, source_list=qualification_sources)
    elif args.action == 'prepare':
        result = lifecycle.prepare(args.root, study_id=ID, scope=SCOPE,
            recipe_factory=recipe, source_list=qualification_sources,
            tests=required_tests, prior_id=lifecycle.ID,
            adapter='analysis/lll/generated_local_profile_study_v2.py')
    else:
        from .ilvis0_control_shards import launch
        result = launch(Path(args.root).resolve()/'data'/ID, reserved_threads=0)
    print(result)


if __name__ == '__main__':
    main()
