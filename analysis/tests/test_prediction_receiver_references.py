# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_reference_primary_uses_training_order_and_preserves_unavailable_cases():
    from lll.prediction_receiver_references import primary

    assert primary([(1., 1, 'b'), (1., 0, 'a')]) == (1., 0, 'a')
    assert primary([(100., 0, 'a'), (2., 1, 'b')]) == (2., 1, 'b')
    assert primary([]) is None
    with pytest.raises(ValueError, match='training'):
        primary([(float('nan'), 0, 'a')])


def test_calibration_scope_preserves_independent_seed_and_scenario_counts():
    from lll.prediction_receiver_references import SCENARIOS, tasks
    from lll.prediction_receiver_replay import SEED

    rows = tasks([SEED, SEED+1])
    assert len(SCENARIOS) == 12 and len(set(SCENARIOS)) == 12
    assert [row['payload']['seed'] for row in rows] == [SEED, SEED+1]
    assert all(row['limits']['native_calls'] == 0 and row['limits']['bound_calls'] == 36 for row in rows)
    assert rows[0]['limits']['bound_steps'] < rows[1]['limits']['bound_steps']
    with pytest.raises(ValueError, match='distinct'):
        tasks([SEED, SEED])


def test_reference_summary_keeps_unavailable_seeds_in_the_denominator():
    from lll.prediction_receiver_references import summarize

    seeds = [17, 19]
    first = dict(seed=17, model='sphere_still', input_law='increment', profile=False,
                 forecast_to_truth_3d_rms_m=1., forecast_to_receiver_3d_rms_m=1.2)
    cases = summarize(seeds, [first])
    assert len(cases) == 12 and sum(row['available'] for row in cases) == 1
    case = next(row for row in cases if row['available'])
    assert case['planned'] == 2 and case['unavailable'] == 1
    assert case['receiver_rms_m']['median'] == 1.2
    assert all(row['receiver_rms_m'] is None for row in cases if not row['available'])
    with pytest.raises(ValueError, match='duplicate'):
        summarize(seeds, [first, first])


def test_original_study_and_recovery_stage_share_the_same_archive_root(tmp_path):
    from lll.prediction_receiver_references import ID, project_directory

    assert project_directory(tmp_path/'data'/ID) == tmp_path
    assert project_directory(tmp_path/'data'/(ID+'-recovery')/'stage-000') == tmp_path
    with pytest.raises(ValueError, match='replay directory'):
        project_directory(tmp_path/'data'/'unrelated')


def test_reference_evaluator_seals_result_with_scientific_abstention(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from lll import prediction_receiver_references as replay
    from lll.ilvis0_control_shards import TaskContext, prepare

    seed = replay.SEED+1
    grid = {(*case, start): str(number*2+start)
            for number, case in enumerate(replay.SCENARIOS) for start in (0, 1)}
    archive = SimpleNamespace(
        rows={identity: {'status': 'complete'} for identity in grid.values()},
        envelope=lambda identity: {'result': {'converged': True, 'training_cost': int(identity)}},
        cache={}, envelopes={})
    monkeypatch.setattr(replay, '_parent', lambda root: (archive, {seed: grid}))
    monkeypatch.setattr(replay, '_score', lambda *args: dict(
        receiver_sha256='a'*64, forecast_to_truth_3d_rms_m=1., forecast_to_receiver_3d_rms_m=1.2))
    (tmp_path/'adapter.py').write_text('pass\n')
    (tmp_path/'prior.json').write_text('{}')
    task = replay.tasks([seed])[0]
    directory = tmp_path/'data'/replay.ID
    prepare(directory, project_root=tmp_path, tasks=[task], sources=['adapter.py'],
            inputs={'previous':'prior.json'}, adapter='adapter.py', workers=1, threads=1,
            environment={'fixture': True}, maximum_wall_s=30., scope=replay.SCOPE)
    context = TaskContext(directory, 0, task['identity'])
    result = replay.evaluate(context.task, context)
    assert len(result['records']) == 12
    context.finish(result)
    assert context.finished
