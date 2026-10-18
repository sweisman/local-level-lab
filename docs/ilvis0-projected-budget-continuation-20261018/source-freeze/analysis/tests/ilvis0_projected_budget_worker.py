# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate two-endpoint generated continuation; completed allowances stay sealed."""
from pathlib import Path
import types


def worker():
    path=Path(__file__).with_name('ilvis0_projected_trust_worker.py');source=path.read_text()
    for old,count,new in (('160',4,'600'),('3888',2,'1204'),('24',7,'2'),('/12',1,'/1')):
        if source.count(old)!=count:raise ValueError('unrecognized preserved numerical scope: '+old)
        source=source.replace(old,new)
    substitutions={
        'ilvis0_projected_trust as candidate':'ilvis0_projected_local as candidate',
        "for name in ('analysis/lll/ilvis0_solver_trust_v2.py'":
            "for name in ('analysis/tests/ilvis0_projected_budget_worker.py','analysis/lll/ilvis0_solver_trust_v2.py'",
        "'analysis/tests/test_ilvis0_projected_trust_qualification.py','--junitxml='":
            "'analysis/tests/test_ilvis0_projected_trust_qualification.py','analysis/tests/test_ilvis0_projected_local.py','--junitxml='",
        'len(checks)!=11':'len(checks)!=16',
        'all eleven constructed software checks required':'all sixteen constructed software checks required',
        "version='ilvis0-projected-trust-qualification-v1'":"version='ilvis0-projected-budget-continuation-v1'",
        "initial=np.zeros(len(truth)) if task['start']=='zero' else -.8*np.sign(truth)":
            "initial=np.array(saved_starts[task['start']],float)",
        "fit=candidate.fit_control(p,task['model'],start=initial,maximum_evaluations=600)":
            "fit=candidate.engine().fit_candidate(p,task['model'],start=initial,maximum_evaluations=600,physical_step=p.physical_step)",
        '# Projected trust-region qualification':'# Generated paired-endpoint budget continuation',
    }
    for before,after in substitutions.items():
        if source.count(before)!=1:raise ValueError('unrecognized preserved continuation layout: '+before)
        source=source.replace(before,after)
    core=types.ModuleType('_projected_budget_worker');core.__file__=str(path)
    exec(compile(source,str(path),'exec'),core.__dict__)
    core.__file__=__file__
    core.OUTPUT=core.ROOT/'data/ilvis0-projected-budget-continuation-20261018'
    core.GUIDE=core.ROOT/'docs'/core.OUTPUT.name
    core.PARENT=core.ROOT/'docs/ilvis0-projected-local-qualification-20261018'
    parent=core.load(core.PARENT/'summary.json');failed=[p for p in parent['pairs'] if not p['passed']]
    if len(failed)!=1 or (failed[0]['model'],failed[0]['clock'],failed[0]['axes'])!=('sphere_still','nominal',['height']):
        raise ValueError('the declared single disagreeing pair is required')
    rows=[r for r in parent['results'] if (r['model'],r['clock'],r['axes'])==('sphere_still','nominal',['height'])]
    if len(rows)!=2 or not all(r['passed'] for r in rows):raise ValueError('two passing saved endpoints required')
    core.saved_starts={r['start']:r['fit']['normalized_parameters'] for r in rows}
    tasks=[dict(identity=r['identity']+'-budget-continuation',model=r['model'],clock=r['clock'],axes=r['axes'],start=r['start']) for r in rows]
    preceding=core.q
    core.q=types.SimpleNamespace(tasks=lambda:tasks,assess_fit=preceding.assess_fit,compare_pair=preceding.compare_pair)
    return core


if __name__=='__main__':worker().main()
