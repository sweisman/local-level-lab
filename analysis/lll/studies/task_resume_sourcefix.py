# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned source-list repair for the paired-bound task continuation."""


SOURCE = 'analysis/lll/studies/task_resume_sourcefix.py'
TEST = 'analysis/tests/test_task_resume_sourcefix.py'
TEST_NAME = 'test_prepared_stage_accepts_already_frozen_recovery_sources'


def deduplicating_prepare(original):
    """Preserve the frozen source set when recovery paths already belong to it."""
    def prepare(output, **kwargs):
        kwargs['sources'] = list(dict.fromkeys(kwargs['sources']))
        return original(output, **kwargs)
    prepare._sourcefix = True
    return prepare


def install():
    from . import task_resume as base
    if not getattr(base.runner.prepare, '_sourcefix', False):
        base.runner.prepare = deduplicating_prepare(base.runner.prepare)
    if not getattr(base.qualification_sources, '_sourcefix', False):
        original = base.qualification_sources
        def sources(root):
            return list(dict.fromkeys((*original(root), SOURCE, TEST)))
        sources._sourcefix = True
        base.qualification_sources = sources
    base.REQUIRED_TESTS = tuple(dict.fromkeys((*base.REQUIRED_TESTS, TEST_NAME)))


if __name__ == '__main__':
    install()
    from . import task_resume
    raise SystemExit(task_resume.main())
