"""A cooperative in-task wall stop is a sealed failure, not resumable work."""
import json

from lll import ilvis0_control_shards as shards
from test_ilvis0_control_shards import fixture


def test_in_task_wall_stop_seals_failure_and_preserves_saved_artifact(tmp_path, monkeypatch):
    output, _, _ = fixture(tmp_path, workers=4)
    for name, value in shards.verify(output)['numerical_environment'].items():
        monkeypatch.setenv(name, value)

    def evaluate(task, context):
        context.save('wide-fit.json', dict(phase='complete'))
        raise shards.BudgetStopped('original cooperative deadline exhausted')

    shards.run_shard(output, 0, evaluate=evaluate)
    result_path = output/'shards/000/results/task-0.json'
    envelope = json.loads(result_path.read_text())
    assert envelope['status'] == 'complete'
    assert envelope['result']['error_type'] == 'BudgetStopped'
    assert envelope['result']['passed'] is False
    assert envelope['artifacts']['artifacts/task-0/wide-fit.json']
    assert result_path.with_suffix('.seal.json').is_file()
