# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full-calibration launcher gated on the separately verified complete review."""
from pathlib import Path
import types


def worker():
    path=Path(__file__).with_name('ilvis0_projected_fullcal_worker.py');source=path.read_text()
    replacements={
        "core.PARENT=core.ROOT/'docs/ilvis0-projected-local-qualification-20261018'":
            "core.PARENT=core.ROOT/'docs/ilvis0-projected-complete-review-20261018'",
        "'analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py'":
            "'analysis/tests/ilvis0_projected_fullcal_review_worker.py','analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py'",
    }
    for before,after in replacements.items():
        if source.count(before)!=1:raise ValueError('unrecognized preserved full-calibration launcher layout')
        source=source.replace(before,after)
    module=types.ModuleType('_fullcal_review_launcher');module.__file__=__file__
    exec(compile(source,str(path),'exec'),module.__dict__)
    core=module.worker();core.__file__=__file__;return core


if __name__=='__main__':worker().main()
