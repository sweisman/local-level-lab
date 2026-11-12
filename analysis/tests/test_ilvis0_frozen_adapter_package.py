# SPDX-License-Identifier: AGPL-3.0-or-later
"""The real worker must import a package adapter before charging science."""
from pathlib import Path

from lll import ilvis0_control_shards as shards


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_worker_loads_relative_import_adapter(tmp_path):
    project = tmp_path/'project'
    adapter = project/'analysis/lll/relative_adapter.py'
    adapter.parent.mkdir(parents=True)
    adapter.write_text('''from .studies.artifacts import encoded

def evaluate(task, context):
    context.charge(native_calls=1, packet_visits=1)
    context.save_bytes('proof.json', encoded({'loaded': True}))
    return {'passed': True, 'scientific_decision': 'abstain'}
''')
    runner = project/'analysis/tests/ilvis0_control_shards.py'
    runner.parent.mkdir(parents=True)
    runner.write_bytes((ROOT/'analysis/tests/ilvis0_control_shards.py').read_bytes())
    input_file = project/'recipe.json'
    input_file.write_text('{}')
    task = dict(identity='package-000', input_key='recipe',
                payload=dict(case=0), limits=dict(native_calls=1,
                    packet_visits=1, bound_calls=0, bound_steps=0))
    study = tmp_path/'study'
    shards.prepare(study, project_root=project, tasks=[task],
                   sources=['analysis/lll/relative_adapter.py',
                            'analysis/tests/ilvis0_control_shards.py'],
                   inputs={'recipe':'recipe.json'},
                   adapter='analysis/lll/relative_adapter.py',
                   workers=1, threads=1, maximum_wall_s=30,
                   environment=shards.runtime_environment())
    result = shards.launch(study, reserved_threads=0)
    assert result['passed'] is True
    assert result['charged']['native_calls'] == 1
    shards.verify_completion(study)
