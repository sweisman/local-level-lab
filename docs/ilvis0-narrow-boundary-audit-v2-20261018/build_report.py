# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate saved-clock audit with JSON-native scalar metadata."""
from pathlib import Path
import types

ROOT=Path(__file__).resolve().parents[2]
TEMPLATE=ROOT/'docs/ilvis0-narrow-boundary-audit-20261018/build_report.py'


def executor():
    source=TEMPLATE.read_text()
    edits=[('minimum=64*np.finfo(float).eps','minimum=float(64*np.finfo(float).eps)'),
        ("(Path(__file__),ROOT/'analysis/lll/ilvis0_clock_brackets.py')",
         "(Path(__file__),TEMPLATE,ROOT/'analysis/lll/ilvis0_clock_brackets.py')")]
    for old,new in edits:
        if source.count(old)!=1:raise ValueError('unrecognized saved-audit source layout')
        source=source.replace(old,new)
    module=types.ModuleType('_narrow_geometry_audit_v2');module.__file__=str(Path(__file__).resolve())
    module.TEMPLATE=TEMPLATE
    exec(compile(source,str(TEMPLATE),'exec'),module.__dict__)
    module.OUTPUT=ROOT/'data/ilvis0-narrow-boundary-audit-v2-20261018'
    return module


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    module=executor()
    if parser.parse_args().render_only:module.render()
    else:module.build()
