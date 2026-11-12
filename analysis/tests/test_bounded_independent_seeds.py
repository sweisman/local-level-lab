"""Every original bounded-aircraft condition is repeated under both new seeds."""


def test_independent_seed_matrix_preserves_all_24_original_conditions():
    from lll.bounded_independent_seeds import SEEDS, tasks, seeded_recipe
    from lll.bounded_nonlinear_study import tasks as original_tasks
    rows = tasks()
    assert SEEDS == (314159, 161803)
    assert len(rows) == 48
    assert len({row['identity'] for row in rows}) == 48
    assert all(row['input_key'] == 'protocol' for row in rows)
    for seed in SEEDS:
        selected = [row for row in rows if row['payload']['seed'] == seed]
        assert len(selected) == 24
        assert {row['payload']['parent_identity'] for row in selected} == {
            row['identity'] for row in original_tasks()}
        recipe = seeded_recipe(seed)
        assert recipe['noise_by_law']['increment']['seed'] == seed
        assert recipe['noise_by_law']['point']['seed'] == seed


def test_independent_seed_adapter_strips_only_seed_metadata():
    from lll.bounded_independent_seeds import adapted_task, tasks
    from lll.bounded_nonlinear_study import tasks as original_tasks
    original = {row['identity']: row for row in original_tasks()}
    for row in tasks():
        adapted = adapted_task(row)
        baseline = original[row['payload']['parent_identity']]
        assert adapted['identity'] == row['identity']
        assert adapted['payload'] == baseline['payload']
        assert adapted['limits'] == baseline['limits']
        assert row['payload']['seed'] not in (271828,)


def test_independent_seed_result_contract_rejects_missing_abstention():
    import pytest
    from lll.bounded_independent_seeds import require_result
    with pytest.raises(ValueError, match='abstention'):
        require_result({'passed': True, 'model_decision': 'abstain'})
    value = {'passed': True, 'scientific_decision': 'abstain'}
    assert require_result(value) is value


def test_independent_seed_protocol_has_finite_four_thread_allocation():
    from lll.bounded_independent_seeds import protocol, tasks
    value = protocol()
    assert value['seeds'] == [314159, 161803]
    assert value['workers'] * value['threads'] == 4
    assert value['maximum_wall_s'] == 18000.
    assert value['maximum_evaluations_per_fit'] == 200
    assert value['scientific_decision'] == 'abstain'
    assert len(tasks()) == value['total_tasks']


def test_independent_seed_evaluate_passes_exact_seed_to_shared_worker(monkeypatch, tmp_path):
    import json
    from types import SimpleNamespace
    from lll.airquantumgrav_inventory import environment
    from lll.bounded_independent_seeds import SCOPE, evaluate, protocol, tasks
    import lll.bounded_nonlinear_study as shared
    task = dict(tasks()[0], index=0, shard=0)
    records = {'protocol': protocol(), 'qualification_environment': environment()}
    paths = {}
    for key, value in records.items():
        path = tmp_path / key
        path.write_text(json.dumps(value))
        paths[key] = path
    context = SimpleNamespace(manifest={'scope': SCOPE},
                              input_path=lambda key: paths[key])
    calls = []

    def worker(adapted, received, *, r):
        calls.append((adapted, received, r))
        return {'passed': True, 'scientific_decision': 'abstain'}

    monkeypatch.setattr(shared, 'run_case', worker)
    assert evaluate(task, context)['scientific_decision'] == 'abstain'
    assert len(calls) == 1 and calls[0][1] is context
    assert 'seed' not in calls[0][0]['payload']
    assert calls[0][2]['noise_by_law']['increment']['seed'] == task['payload']['seed']
