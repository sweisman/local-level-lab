# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only audit of completed v2 generated profiles and their failed receipt."""

from pathlib import Path
import sqlite3

from .generated_joint_replay_source import CASE, MODELS, SOURCE
from .generated_joint_profile_replay_v2 import ID


def expected_replay_construction(source_recipe):
    from .generated_joint_profile_replay import replay_construction_expected
    return replay_construction_expected(source_recipe)


def audit(root):
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.journal import inspect_snapshot
    root = Path(root).resolve()
    source = ClosedStudy(root, SOURCE)
    replay = ClosedStudy(root, 'data/'+ID)
    try:
        identity = 'straight-level-profile'
        result = replay.envelope(identity)['result']
        if (replay.completion['state'] != 'terminal' or result.get('passed') is not False
                or result.get('reason') != 'generated construction accounting differs'):
            raise ValueError('exact sealed v2 accounting failure required')
        passed = replay.artifact(identity, 'all-input-replays-passed.json')
        if (passed['candidates'] != list(MODELS) or passed['later_observations_opened'] is not False
                or passed['source_completion_sha256'] != digest(encoded(source.completion))):
            raise ValueError('three input replays did not precede later observations')
        raw = replay.artifact(identity, 'construction.sqlite', raw=True)
        verified = inspect_snapshot(raw, replay.completion['manifest_sha256'])
        db = sqlite3.connect(':memory:')
        try:
            db.deserialize(raw)
            db.execute('PRAGMA query_only=ON')
            counts = dict(db.execute('SELECT resource,total FROM counts'))
        finally:
            db.close()
        expected = expected_replay_construction(source.input('recipe'))
        if verified['starts'] != 1 or counts != expected:
            raise ValueError('replay construction charges differ from exact source-free amount')
        native = replay.artifact(identity, 'native-prepayment.json')
        subset = {key: replay.tasks[identity]['limits'][key]
                  for key in ('native_calls', 'packet_visits')}
        if native['state'] != 'complete' or native['prepaid'] != subset:
            raise ValueError('native replay block did not close with frozen limits')
        profiles = {}
        for model in MODELS:
            replay.artifact(identity, 'replay-'+model+'.json')
            linear = replay.artifact(identity, 'linear-profile-'+model+'.json')
            completed = replay.artifact(identity, 'profile-'+model+'.json')
            if (not linear['solver_success'] or completed['profile'] != linear
                    or completed['native_point_boundary_adjustment_max'] > 5e-13
                    or abs(completed['applied_profile_cost']-
                           linear['profiled_squared_residual']) >
                       1e-8*(1+linear['profiled_squared_residual'])):
                raise ValueError('saved profile or exact-boundary check differs: '+model)
            profiles[model] = dict(linear_cost=linear['profiled_squared_residual'],
                applied_cost=completed['applied_profile_cost'],
                rank=linear['rank'], at_bound_columns=linear['at_bound_columns'],
                maximum_correction=max(abs(x) for x in linear['correction']),
                boundary_adjustment_max=completed['native_point_boundary_adjustment_max'],
                native_tangent_rms_m=completed['native_tangent_rms_m'],
                native_tangent_max_abs_m=completed['native_tangent_max_abs_m'])
        return dict(version='generated-joint-saved-audit-v1',
            source_completion_sha256=digest(encoded(source.completion)),
            replay_completion_sha256=digest(encoded(replay.completion)),
            replay_state='terminal', replay_failure=result['reason'],
            construction_journal=verified,
            actual_construction_charges=counts,
            expected_construction_charges=expected,
            source_future_generation_omitted=source.input('recipe')['queries'],
            profiles=profiles, no_native_recalculation=True,
            future_data_used_for_profiles=True, error_law_calibrated=False,
            scientific_decision='abstain')
    finally:
        replay.close()
        source.close()


def main():
    from .studies.artifacts import atomic, encoded
    result = audit(Path(__file__).resolve().parents[2])
    path = Path('docs/prediction-observed-development/generated-joint-saved-audit.json')
    atomic(path, encoded(result))
    print({key: result[key] for key in ('replay_state','replay_failure',
                                        'source_future_generation_omitted')})


if __name__ == '__main__':
    main()
