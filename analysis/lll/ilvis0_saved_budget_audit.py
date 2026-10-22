# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only diagnosis of position allowances; no integration or model fitting."""
import json
import math
from lll.studies.artifacts import ArchiveStore,digest


def budget_row(material):
    result=material['result'];certificate=material['certificate']
    vectors=[certificate[k] for k in ('position_unshared_remainder',
        'lever_unshared_remainder','unshared_remainder')]
    vectors.append(result['future_width_m'])
    if any(len(v)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in v) for v in vectors):
        raise ValueError('finite nonnegative three-axis allowances required')
    position,lever,total,width=vectors
    if any(abs(p+l-t)>1e-10*max(1,t) for p,l,t in zip(position,lever,total)):
        raise ValueError('saved position/lever components do not reconstruct total')
    if type(result['profile']) is not bool or type(result['useful']) is not bool or type(result['numerical_checks_passed']) is not bool:
        raise ValueError('explicit original outcomes required')
    return dict(identity=material['identity'],model=result['model'],profile=result['profile'],
        time_s=certificate['time_s'],prior_useful=result['useful'],
        prior_numerical_checks_passed=result['numerical_checks_passed'],future_width_m=width,
        position_share=[p/t if t else 0.0 for p,t in zip(position,total)],
        position_unshared_remainder=position,lever_unshared_remainder=lever,
        total_unshared_remainder=total,result_sha256=material['result_sha256'],
        bound_sha256=material['bound_sha256'],new_prediction_bound=False)


def read_materials(root,prefix):
    """Verify the closed-study hash chain before consuming its six saved cases."""
    store=ArchiveStore(root)
    def read(name,expected=None):
        raw=store.read(prefix+'/'+name)
        if expected is not None and digest(raw)!=expected:raise ValueError('saved evidence hash mismatch: '+name)
        return json.loads(raw),digest(raw)
    completion,_=read('completion.json')
    _,manifest_sha=read('manifest.json',completion['manifest_sha256'])
    summary,_=read('summary.json',completion['summary_sha256'])
    if summary['passed'] or summary['completed']!=6 or len(summary['results'])!=6:
        raise ValueError('expected the frozen six-case unsuccessful feasibility study')
    materials=[]
    for case in summary['results']:
        envelope,sha=read(case['artifact'],case['artifact_sha256'])
        result=envelope['result'];identity=case['identity']
        if (envelope['manifest_sha256']!=manifest_sha or envelope['identity']!=identity
                or result['identity']!=identity or digest((json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode())!=envelope['result_sha256']
                or result['original_reads']!=0 or result['optimizer_starts']!=0):
            raise ValueError('saved case identity, result hash or scope mismatch')
        name='artifacts/'+identity+'/future-bound.json'
        certificate,bound_sha=read(name,envelope['artifacts'][name])
        materials.append(dict(identity=identity,result=result,certificate=certificate,
            result_sha256=sha,bound_sha256=bound_sha,manifest_sha256=manifest_sha))
    if {(m['result']['model'],m['result']['profile']) for m in materials}!={(i,p) for i in range(3) for p in (False,True)}:
        raise ValueError('all three models and both processing cases required')
    return materials


def evaluate(task,context):
    material=json.loads(context.input_path().read_text())
    row=budget_row(material);context.save('budget-row.json',row)
    return dict(passed=True,scientific_decision='abstain',identity=task['identity'],
        scope='saved allowance arithmetic only',prior_study_qualified=False,
        observational_coverage_qualified=False,optimizer_starts=0,original_reads=0,
        row=row)
