# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite trial of range-scaled affine corrections, with unchanged native gates."""
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_final_pair_v2_worker as parent

OUTPUT=ROOT/'data/ilvis0-scaled-pair-boundary-20261018'
GUIDE=ROOT/'docs/ilvis0-scaled-pair-boundary-20261018'
VERSION='ilvis0-range-scaled-pair-boundary-v1'


def make_plan(*args):
    plan=parent.make_plan(*args);plan.update(version=VERSION,local_linear_solver_changed=True)
    for task in plan['tasks']:
        old='::final_pair_context_v2_check'
        if not task['identity'].endswith(old):raise ValueError('unrecognized frozen source identity')
        task['identity']=task['identity'][:-len(old)]+'::scaled_branch_v1_check'
    return plan


def sources():
    values=parent.sources()
    for name in ('analysis/lll/ilvis0_scaled_branch.py','analysis/tests/test_ilvis0_scaled_branch.py',
        'analysis/tests/ilvis0_scaled_pair_worker.py','analysis/tests/test_ilvis0_scaled_pair_worker.py'):
        values[str(ROOT/name)]=parent.parent.sha(ROOT/name)
    # The saved systems are qualification fixtures as well as the motivating
    # evidence. Pin them before testing, not just their test-loader source.
    for name in ('ilvis0-final-pair-boundary-v2-20261018','ilvis0-correction-audit-20261018'):
        directory=ROOT/'docs'/name;receipt=parent.parent.load(directory/'evidence-receipt.json')
        names=['manifest.json','summary.json','completion.json','evidence-receipt.json']
        if name=='ilvis0-final-pair-boundary-v2-20261018':
            names.extend(r['linearization_file'] for r in parent.parent.load(directory/'summary.json')['results'] if r['kind']=='target')
        for filename in names:
            path=directory/filename;digest=parent.parent.sha(path)
            if filename!='evidence-receipt.json' and receipt['artifacts'][filename]!=digest:
                raise ValueError('sealed qualification fixture changed')
            values[str(path)]=digest
    return values


def executor_source(source):
    source=parent.executor_source(source)
    edits=[('from lll.ilvis0_representable_boundary import check_endpoint',
            'from lll.ilvis0_scaled_branch import check_endpoint'),
        ("str(ROOT/'analysis/tests/test_ilvis0_representable_boundary.py')",
            "str(ROOT/'analysis/tests/test_ilvis0_scaled_branch.py')"),
        ("str(ROOT/'analysis/tests/test_ilvis0_final_pair_v2_worker.py')",
            "str(ROOT/'analysis/tests/test_ilvis0_scaled_pair_worker.py')"),
        (",str(ROOT/'analysis/tests/test_ilvis0_saved_context.py')",''),
        ('# Corrected-context pair results','# Scaled-affine pair results')]
    for old,new in edits:
        if source.count(old)!=1:raise ValueError('unrecognized frozen executor: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    module=types.ModuleType('_scaled_pair_boundary_executor');module.__file__=str(Path(__file__).resolve())
    original=Path(parent.parent.__file__)
    exec(compile(original.read_text(),str(original),'exec'),module.__dict__)
    for key,value in dict(OUTPUT=OUTPUT,GUIDE=GUIDE,VERSION=VERSION,make_plan=make_plan,
            source_context=parent.source_context,sources=sources,executor_source=executor_source).items():
        setattr(module,key,value)
    executor=module.build_executor()
    return executor


if __name__=='__main__':build_executor().main()
