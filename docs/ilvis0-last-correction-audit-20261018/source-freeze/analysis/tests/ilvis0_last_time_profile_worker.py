# SPDX-License-Identifier: AGPL-3.0-or-later
"""Final-stretch matched fixed-time profiles; full comparisons remain separate."""
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_remaining_time_profile_worker as template

parent=template.parent
TEMPLATE=template.TEMPLATE
ORIGINAL=template.ORIGINAL
SID='b4e44ddc0f130ecd45674c78'
OUTPUT=ROOT/'data/ilvis0-last-time-profile-20261018'
GUIDE=ROOT/'docs/ilvis0-last-time-profile-20261018'
FIELD=ROOT/'data/ilvis0-last-field-boundary-20261018'
FIELD_GUIDE=ROOT/'docs/ilvis0-last-field-boundary-20261018'
VERSION='ilvis0-last-two-case-time-profile-v1'

_planner=types.ModuleType('_last_time_profile_planner');_planner.__file__=str(Path(__file__).resolve())
exec(compile(Path(template.__file__).read_text(),str(Path(template.__file__)),'exec'),_planner.__dict__)
_planner.SID=SID;_planner.VERSION=VERSION
_make_plan=_planner.make_plan
_executor_source=_planner.executor_source


def make_plan(previous,original):
    # This source manifest also contains unfinished specified-field fits.
    # Only zero-field identities belong to the conditional timing profiles.
    selected=dict(original,plan=dict(original['plan'],tasks=[t for t in original['plan']['tasks']
        if not t['source_identity'].startswith(SID+'::') or t['source_identity'].split('::')[2]=='sphere_still']))
    plan=_make_plan(previous,selected)
    for task in plan['tasks']:
        if task['kind']=='control':task['identity']=task['identity'].replace('::remaining_time_control','::last_time_control')
        else:task['identity']+='::last_profile_v1'
    plan.update(prerequisite_field_stage=str(FIELD.relative_to(ROOT)),full_field_qualification_required=True)
    return plan


def field_evidence():
    parent.prior.sealed(FIELD,published=FIELD_GUIDE)
    result=parent.load(FIELD/'summary.json');manifest=parent.load(FIELD/'manifest.json')
    if (not result['qualification_passed'] or len(result['results'])!=6
            or any(r['status']!='complete' or not r['passed'] for r in result['results'])
            or not result['repeatability']['agreement_passed']
            or set(result['repeatability']['cases'])!=set(template.CASES)
            or not all(r['agreement_passed'] and r['both_endpoints_passed'] for r in result['repeatability']['cases'].values())):
        raise ValueError('completed two-case field qualification is required first')
    control=parent.load(parent.PARENT/'manifest.json')
    if any(manifest[k]!=control[k] for k in ('environment','extended_kernel','ordinary_value_kernel')):
        raise ValueError('profile/control/field environment and kernels must agree')
    values={str(FIELD/n):parent.sha(FIELD/n) for n in ('manifest.json','summary.json','completion.json')}
    values[str(FIELD_GUIDE/'evidence-receipt.json')]=parent.sha(FIELD_GUIDE/'evidence-receipt.json')
    return values


def executor_source(source):
    source=_executor_source(source)
    edits=[("str(ROOT/'analysis/tests/test_ilvis0_remaining_time_profile_worker.py')",
            "str(ROOT/'analysis/tests/test_ilvis0_last_time_profile_worker.py')"),
        ("values=sources();inputs=prior.scientific_inputs(parent['inputs'])",
            "values=sources();inputs=prior.scientific_inputs(parent['inputs']);inputs.update(field_evidence())")]
    for old,new in edits:
        if source.count(old)!=1:raise ValueError('unrecognized frozen profile executor: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    _planner.OUTPUT=OUTPUT;_planner.GUIDE=GUIDE;_planner.make_plan=make_plan;_planner.executor_source=executor_source
    executor=_planner.build_executor();executor.TESTS=26;executor.field_evidence=field_evidence
    previous_sources=executor.sources
    def sources():
        values=previous_sources()
        for name in ('analysis/tests/ilvis0_last_time_profile_worker.py','analysis/tests/test_ilvis0_last_time_profile_worker.py'):
            values[str(ROOT/name)]=executor.sha(ROOT/name)
        values.update(field_evidence());executor.prior.check_hashes(values)
        return values
    executor.sources=sources
    return executor


if __name__=='__main__':build_executor().main()
