# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolated full-calibration control matrix; starts only after local qualification."""
from pathlib import Path
import types


def worker():
    path=Path(__file__).with_name('ilvis0_projected_trust_worker.py');source=path.read_text()
    substitutions={
        'ilvis0_projected_trust as candidate':'ilvis0_projected_local as candidate',
        "for name in ('analysis/lll/ilvis0_solver_trust_v2.py'":
            "for name in ('analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py','analysis/tests/ilvis0_projected_fullcal_worker.py','analysis/lll/ilvis0_solver_trust_v2.py'",
        "'analysis/tests/test_ilvis0_projected_trust_qualification.py','--junitxml='":
            "'analysis/tests/test_ilvis0_projected_trust_qualification.py','analysis/tests/test_ilvis0_projected_local.py','analysis/tests/test_ilvis0_projected_fullcal.py','--junitxml='",
        'len(checks)!=11':'len(checks)!=20',
        'all eleven constructed software checks required':'all twenty constructed software checks required',
        "version='ilvis0-projected-trust-qualification-v1'":"version='ilvis0-projected-fullcal-qualification-v1'",
        'base=geographic.problem(f,kernel,tangent)':'base=fullcal.problem(task,f,kernel,tangent)',
        'truth=geographic.truth_point(f,base)':'truth=fullcal.truth_point(task,f,base)',
        "initial=np.zeros(len(truth)) if task['start']=='zero' else -.8*np.sign(truth)":'initial=fullcal.start(task,base)',
        "r['axes']==a['axes'] and r['start']=='opposed'":"r['axes']==a['axes'] and r.get('case_id')==a.get('case_id') and r['start']=='opposed'",
        "pairs.append(dict(model=a['model'],clock=a['clock'],axes=a['axes'],**q.compare_pair(a,b)))":
            "pairs.append(dict(model=a['model'],clock=a['clock'],axes=a['axes'],case_id=a['case_id'],**q.compare_pair(a,b)))",
        '# Projected trust-region qualification':'# Full-calibration projected qualification',
        "{r['model']} | {r['clock']}":"{r['model']} / {r['case_id']} | {r['clock']}",
    }
    for before,after in substitutions.items():
        if source.count(before)!=1:raise ValueError('unrecognized preserved worker layout: '+before)
        source=source.replace(before,after)
    core=types.ModuleType('_projected_fullcal_worker');core.__file__=str(path)
    exec(compile(source,str(path),'exec'),core.__dict__)
    from lll import ilvis0_projected_fullcal as fullcal
    core.fullcal=fullcal;core.q=fullcal;core.__file__=__file__
    core.OUTPUT=core.ROOT/'data/ilvis0-projected-fullcal-qualification-20261018'
    core.GUIDE=core.ROOT/'docs'/core.OUTPUT.name
    core.PARENT=core.ROOT/'docs/ilvis0-projected-local-qualification-20261018'
    done=core.load(core.PARENT/'completion.json');summary=core.load(core.PARENT/'summary.json')
    if (done['summary_sha256']!=core.sha(core.PARENT/'summary.json') or not summary['passed']
            or len(summary['results'])!=24 or len(summary['pairs'])!=12):
        raise ValueError('complete passing local qualification required before full-calibration controls')
    return core


if __name__=='__main__':worker().main()
