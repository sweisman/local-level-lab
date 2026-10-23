# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prevent new per-study command scripts outside the shared library."""
import json
from pathlib import Path
import subprocess
from public_fixtures import reference_fixture


def test_new_study_code_uses_the_common_library():
    root=Path(__file__).resolve().parents[2]
    legacy=json.loads((root/'repro/legacy-entrypoints.json').read_text())['paths']
    names=subprocess.check_output(['git','ls-files','-z','--','analysis/tests'],cwd=root).decode().split('\0')
    unexpected=[name for name in names if name.endswith('.py') and name not in legacy
        and not Path(name).name.startswith('test_') and not Path(name).name.endswith('_fixtures.py')
        and not (name.endswith('_reference.py') and reference_fixture(root/name))]
    assert not unexpected,'Put new study orchestration in lll.studies and evaluators in lll: '+repr(unexpected)
