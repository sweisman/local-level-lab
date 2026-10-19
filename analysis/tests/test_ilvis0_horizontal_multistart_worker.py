# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
from test_ilvis0_horizontal_multistart import selection


def worker():
    p=Path(__file__).with_name('ilvis0_horizontal_multistart_worker.py')
    spec=importlib.util.spec_from_file_location('matched_worker_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_full_recorded_and_independent_seed_families_are_kept_separate():
    m=worker();plan=m.policy.plan(selection());references={};rows=[]
    for sid in ('target','control'):
        for case in ('bias1_unsubtracted','bias1_profiled_removal'):
            for model in ('sphere_rotating','sphere_still','flat_still'):
                key='::'.join((sid,case,model));references[key]=dict(normalized_parameters=[.1,.2,.3])
                for role in ('primary','repeat'):
                    rows.append(dict(identity=key+'::'+role,start_point=[-.1,-.2,-.3],fit=dict(
                        normalized_parameters=[.4,.5,.6],active_parameters=['bias','time_offset','null'])))
    vectors,pre=m.seeds(plan,dict(references=references),rows)
    assert len(vectors)==38 and len(pre)==8
    for t in plan['tasks']:
        point=vectors[t['identity']]
        if t['control']:assert point==[.4,.5,.6]
        elif t['role']=='primary':assert point==[.1,t['timing_start'],.3]
        else:assert point==[-.1,t['timing_start'],-.3]


def test_receipt_adapter_accepts_the_actual_start_and_both_call_phases(tmp_path):
    m=worker();book=m.new_ledger(tmp_path,'freeze',['x']);book.start('x')
    events=[]
    def counted(value):
        assert len(book.read('sweeps'))==len(events)+1
        events.append(value);return value
    assert book.call('x','fit','tangent',counted,1)==1
    assert book.call('x','diagnostic','tangent',counted,2)==2
    assert book.count('x','fit')==1 and book.count('x','diagnostic')==1


def test_preflight_ledger_has_one_separately_charged_call(tmp_path):
    m=worker();book=m.new_ledger(tmp_path,'freeze',['center'],preflight=True);book.start('center')
    book.call('center','diagnostic','tangent',lambda:None)
    assert len(book.read('starts'))==1 and len(book.read('sweeps'))==1
