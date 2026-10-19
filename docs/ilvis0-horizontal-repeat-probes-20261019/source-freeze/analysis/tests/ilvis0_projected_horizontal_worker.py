# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned horizontal-only capability and full-calibration qualification."""
import copy
import fcntl
from pathlib import Path
import shutil
import sys
import types

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from ilvis0_projection_sequence import sha,load,write,complete
from lll.ilvis0_projected_trust_qualification import tasks

REVIEW='ilvis0-projected-horizontal-review-20261018'


def key(row):return row['model'],row['clock'],tuple(row['axes']),row.get('start')


def horizontal_inventory(parent):
    rows=[r for r in parent['results'] if r['axes']==['latitude','longitude']]
    pairs=[p for p in parent['pairs'] if p['axes']==['latitude','longitude']]
    expected=[r for r in tasks() if len(r['axes'])==2]
    if (len(rows)!=12 or len({key(r) for r in rows})!=12 or {key(r) for r in rows}!={key(r) for r in expected}
            or len(pairs)!=6 or len({key(p) for p in pairs})!=6
            or not all(r['passed'] for r in rows) or not all(p['passed'] for p in pairs)):
        raise ValueError('every declared horizontal fit and paired comparison must pass')
    return dict(state='complete',passed=True,results=copy.deepcopy(rows),pairs=copy.deepcopy(pairs),
        qualified_axes=[['latitude','longitude']],unqualified_axes=[['height']],
        preceding_overall_passed=parent['passed'],policy_version='projected-horizontal-capability-v1',
        native_evaluations=0,observed_starts=0,original_recording_reads=0,scientific_decision='abstain')


def ensure_review():
    data=ROOT/'data'/REVIEW;public=ROOT/'docs'/REVIEW
    data.mkdir(parents=True,exist_ok=True);public.mkdir(parents=True,exist_ok=True)
    with (data/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (data/'completion.json').exists():
            done=load(data/'completion.json')
            if done['manifest_sha256']!=sha(data/'manifest.json') or done['summary_sha256']!=sha(data/'summary.json'):
                raise ValueError('horizontal review hash mismatch')
            return load(data/'summary.json')
        if (data/'start.json').exists():raise ValueError('charged review cannot restart')
        name='ilvis0-projected-local-qualification-20261018';parent=complete(name)
        if parent is None:raise ValueError('verified preceding matrix required')
        p=ROOT/'docs'/name;m=load(p/'manifest.json');done=load(p/'completion.json')
        if done['manifest_sha256']!=sha(p/'manifest.json') or done['summary_sha256']!=sha(p/'summary.json'):
            raise ValueError('parent publication hashes disagree')
        sources=dict(m['sources'])
        for filename in ('analysis/tests/ilvis0_projected_horizontal_worker.py','analysis/tests/test_ilvis0_projected_horizontal.py'):
            sources[filename]=sha(ROOT/filename)
        for filename,digest in sources.items():
            if sha(ROOT/filename)!=digest:raise ValueError('horizontal review source mismatch')
        result=horizontal_inventory(parent)
        write(data/'manifest.json',dict(version='projected-horizontal-capability-v1',sources=sources,
            environment=m['environment'],inputs={str((p/n).relative_to(ROOT)):sha(p/n) for n in ('manifest.json','summary.json','completion.json')},
            qualified_axes=[['latitude','longitude']],optimizer_starts=0,native_evaluations=0))
        write(data/'start.json',dict(manifest_sha256=sha(data/'manifest.json')))
        write(data/'summary.json',result)
        write(data/'completion.json',dict(state='complete',manifest_sha256=sha(data/'manifest.json'),summary_sha256=sha(data/'summary.json')))
        for n in ('manifest.json','summary.json','completion.json','start.json'):shutil.copy2(data/n,public/n)
        for filename in sources:
            target=public/'source-freeze'/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/filename,target)
        (public/'README.md').write_text('# Horizontal-only software capability\n\nAll twelve predeclared horizontal fits and all six horizontal paired-start comparisons pass. This saved-only review qualifies that coordinate mode for further full-calibration software controls. **Height-only remains unqualified**, and the preceding overall failed qualification is unchanged. No numerical thresholds, raw observations or scientific decisions change.\n\nThe review makes zero native predictions, optimizer starts or original-recording reads.\n\n[Preceding complete matrix](../'+name+'/README.md) · [Full-calibration scope](../ilvis0-projected-horizontal-fullcal-20261018/PLAN.md).\n')
        write(public/'evidence-receipt.json',dict(artifacts={n:sha(public/n) for n in ('manifest.json','summary.json','completion.json','start.json','README.md')}))
        return result


def worker():
    review=ensure_review()
    if review['qualified_axes']!=[['latitude','longitude']]:raise ValueError('horizontal capability required')
    path=Path(__file__).with_name('ilvis0_projected_fullcal_worker.py');source=path.read_text()
    replacements={
        "core.PARENT=core.ROOT/'docs/ilvis0-projected-local-qualification-20261018'":
            "core.PARENT=core.ROOT/'docs/ilvis0-projected-horizontal-review-20261018'",
        "len(summary['results'])!=24":"len(summary['results'])!=12",
        "len(summary['pairs'])!=12":"len(summary['pairs'])!=6",
        "'analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py'":
            "'analysis/tests/ilvis0_projected_horizontal_worker.py','analysis/tests/test_ilvis0_projected_horizontal.py','analysis/lll/ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_fullcal.py'",
        "'analysis/tests/test_ilvis0_projected_fullcal.py','--junitxml='":
            "'analysis/tests/test_ilvis0_projected_fullcal.py','analysis/tests/test_ilvis0_projected_horizontal.py','--junitxml='",
        'len(checks)!=20':'len(checks)!=22',
        'all twenty constructed software checks required':'all twenty-two constructed software checks required',
        "version='ilvis0-projected-fullcal-qualification-v1'":"version='ilvis0-projected-horizontal-fullcal-v1'",
    }
    for before,after in replacements.items():
        if source.count(before)!=1:raise ValueError('unrecognized preserved horizontal launcher layout: '+before)
        source=source.replace(before,after)
    anchor="    core=types.ModuleType('_projected_fullcal_worker')"
    insert="""    for old,count,new in (('24',7,'12'),('3888',2,'1944'),('/12 paired-start',1,'/6 paired-start')):
        if source.count(old)!=count:raise ValueError('unrecognized horizontal numerical scope: '+old)
        source=source.replace(old,new)
"""
    if source.count(anchor)!=1:raise ValueError('preserved runner layout changed')
    source=source.replace(anchor,insert+anchor)
    module=types.ModuleType('_horizontal_fullcal_launcher');module.__file__=__file__
    exec(compile(source,str(path),'exec'),module.__dict__)
    core=module.worker();core.__file__=__file__
    core.OUTPUT=ROOT/'data/ilvis0-projected-horizontal-fullcal-20261018';core.GUIDE=ROOT/'docs'/core.OUTPUT.name
    fullcal=core.fullcal
    core.q=types.SimpleNamespace(tasks=lambda:[r for r in fullcal.tasks() if len(r['axes'])==2],
        assess_fit=lambda r:r['axes']==['latitude','longitude'] and fullcal.assess_fit(r),
        compare_pair=fullcal.compare_pair)
    return core


if __name__=='__main__':worker().main()
