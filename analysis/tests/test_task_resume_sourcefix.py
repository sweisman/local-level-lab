# SPDX-License-Identifier: AGPL-3.0-or-later
"""A continuation can freeze recovery sources already present in its parent."""
from pathlib import Path

from lll import ilvis0_control_shards as runner
from lll.studies.task_resume_sourcefix import (SOURCE, TEST, TEST_NAME,
                                               deduplicating_prepare, install)


def test_prepared_stage_accepts_already_frozen_recovery_sources(tmp_path):
    project = Path(tmp_path)
    (project/'adapter.py').write_text('def evaluate(task, context): return {"passed": True}\n')
    entry = project/runner.RUNNER
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text('# toy frozen worker\n')
    (project/'recipe.json').write_text('{}')
    task = dict(identity='case', input_key='recipe', payload={},
                native_kind='tangent', limits=dict(native_calls=1,
                packet_visits=1, bound_calls=0, bound_steps=0))
    prepare = deduplicating_prepare(runner.prepare)
    manifest = prepare(project/'stage', project_root=project, tasks=[task],
                       sources=['adapter.py', runner.RUNNER, 'adapter.py'],
                       inputs={'recipe': 'recipe.json'}, adapter='adapter.py',
                       workers=1, threads=1, maximum_wall_s=30,
                       environment=runner.runtime_environment())
    assert set(manifest['sources']) == {'adapter.py', runner.RUNNER}
    assert runner.verify(project/'stage')['sources'] == manifest['sources']


def test_repair_is_bound_to_recovery_qualification():
    from lll.studies import task_resume as base
    original_prepare = base.runner.prepare
    original_sources = base.qualification_sources
    original_tests = base.REQUIRED_TESTS
    try:
        install()
        assert base.runner.prepare is not original_prepare
        assert {SOURCE, TEST} <= set(base.qualification_sources(Path('.')))
        assert TEST_NAME in base.REQUIRED_TESTS
        install()
        assert len(base.qualification_sources(Path('.'))) == len(
            set(base.qualification_sources(Path('.'))))
    finally:
        base.runner.prepare = original_prepare
        base.qualification_sources = original_sources
        base.REQUIRED_TESTS = original_tests
