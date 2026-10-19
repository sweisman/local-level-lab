# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolated local-probe qualification using the preserved complete-matrix runner."""
from pathlib import Path
import types


def worker():
    path=Path(__file__).with_name('ilvis0_projected_trust_worker.py');source=path.read_text()
    substitutions={
        'ilvis0_projected_trust as candidate':'ilvis0_projected_local as candidate',
        "for name in ('analysis/lll/ilvis0_solver_trust_v2.py'":
            "for name in ('analysis/lll/ilvis0_projected_local.py','analysis/tests/test_ilvis0_projected_local.py','analysis/tests/ilvis0_projected_local_worker.py','analysis/lll/ilvis0_solver_trust_v2.py'",
        "'analysis/tests/test_ilvis0_projected_trust_qualification.py','--junitxml='":
            "'analysis/tests/test_ilvis0_projected_trust_qualification.py','analysis/tests/test_ilvis0_projected_local.py','--junitxml='",
        'len(checks)!=11':'len(checks)!=16',
        'all eleven constructed software checks required':'all sixteen constructed software checks required',
        "version='ilvis0-projected-trust-qualification-v1'":"version='ilvis0-projected-local-qualification-v1'",
    }
    for before,after in substitutions.items():
        if source.count(before)!=1:raise ValueError('unrecognized preserved worker layout: '+before)
        source=source.replace(before,after)
    core=types.ModuleType('_projected_local_worker');core.__file__=str(path)
    exec(compile(source,str(path),'exec'),core.__dict__)
    core.__file__=__file__
    core.OUTPUT=core.ROOT/'data/ilvis0-projected-local-qualification-20261018'
    core.GUIDE=core.ROOT/'docs'/core.OUTPUT.name
    core.PARENT=core.ROOT/'docs/ilvis0-projected-trust-qualification-20261018'
    return core


if __name__=='__main__':worker().main()
