# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib

import pytest


def policy():return importlib.import_module('lll.timing_matrix_assembly')


def fixture():
    from lll import timing_feasible_matrix_study as m
    from test_timing_matrix_completion import fixture as left_fixture
    a=left_fixture();keys=sorted({m.pair_key(t) for t in m.tasks()});missing={m.pair_key(t) for t in m.tasks()[:4]}
    a['pairs']=[dict(m.pair_metadata(k),passed=k not in missing) for k in keys]
    b=dict(verified=True,selected=4,complete=4,native_qualified=True,original_binding_replays_exact=True,
        manifest_sha256='4ca0a4bdc1da3b05f9c5d116af34ee52bc2915c7075961f2b1c12e55c4d216e2',
        summary_sha256='52c7b8c090bb755eda35b8fed87779bec4544667a28f80e3d303306613454d29',
        rows=[dict(identity=t['identity'],passed=True) for t in m.tasks()[:4]],
        pairs=[dict(m.pair_metadata(k),passed=True) for k in sorted(missing)],failures=[],verification_failures=[])
    return a,b


@pytest.mark.parametrize('change',[None,'missing','duplicate','fit','pair','pair_duplicate','replay','manifest','summary','qualified'])
def test_matrix_assembly_requires_all_48_distinct_cases_and_24_pairs(change):
    p=policy();a,b=fixture()
    if change=='missing':b['rows'].pop()
    elif change=='duplicate':b['rows'][0]['identity']=a['rows'][0]['identity']
    elif change=='fit':b['rows'][0]['passed']=False
    elif change=='pair':b['pairs'][0]['passed']=False
    elif change=='pair_duplicate':b['pairs'][0]=copy.deepcopy(a['pairs'][2])
    elif change=='replay':b['original_binding_replays_exact']=False
    elif change=='manifest':b['manifest_sha256']='0'*64
    elif change=='summary':b['summary_sha256']='0'*64
    elif change=='qualified':b['native_qualified']=False
    if change is None:
        r=p.assemble(a,b)
        assert r['qualified'] and r['cases']==48 and r['start_pairs']==24
        assert r['interrupted_source_study_qualified'] is False and r['original_labels_changed'] is False
        assert len(r['rows'])==48 and len(r['preserved_interruptions'])==4
    else:
        with pytest.raises(ValueError):p.assemble(a,b)


@pytest.mark.parametrize('change',[None,'source','current','missing','environment','empty'])
def test_matrix_assembly_requires_identical_shared_execution_sources_and_environment(change):
    p=policy();left={'physical':'a'*64,'worker':'b'*64};right=dict(left,policy='c'*64);current=dict(right)
    le={'same':True};re=dict(le);now=dict(le)
    if change=='source':right['physical']='d'*64
    elif change=='current':current['worker']='d'*64
    elif change=='missing':right.pop('physical')
    elif change=='environment':re={}
    elif change=='empty':left={}
    if change is None:assert p.verify_shared(left,right,current,le,re,now)==2
    else:
        with pytest.raises(ValueError):p.verify_shared(left,right,current,le,re,now)
