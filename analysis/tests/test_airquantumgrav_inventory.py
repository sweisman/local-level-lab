# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import io

import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_inventory') is not None, 'development inventory adapter is missing'
    return __import__('lll.airquantumgrav_inventory',fromlist=['recipe'])


def metadata():
    return dict(groups=dict(groups=[dict(group_id='dev',role='development',record_ids=['esa:187_rqh01.txt'])]),
        reservation=dict(development_files=['187_rqh01.txt'],confirmation_files=['186_rqh01.txt']),
        inspection=dict(source_file='187_rqh01.txt',source_sha256='a'*64,byte_size=100,
            records=30001,gaps_above_1p5_nominal_periods=0,first_gps_sow_s=100.,last_gps_sow_s=200.),
        receipt=dict(sha256='a'*64,size_bytes=100),
        receiver_report=dict(source_file='187_air1_ppp_2Hz_final.txt',sha256='b'*64,epochs=10))


def test_inventory_context_enforces_explicit_development_and_matching_support():
    result=library().validate_context(**metadata())
    assert result['group_id']=='dev' and result['imu_support_s']==[100.,200.]
    assert result['expected_receiver_epochs']==10 and result['receiver_sha256']=='b'*64


@pytest.mark.parametrize('fault',['protected','unknown','overlap','hash','size','gap','time','receiver_name'])
def test_inventory_rejects_protected_or_unsupported_context_before_reading(fault):
    values=metadata()
    if fault=='protected':values['groups']['groups'][0]['role']='protected_confirmation'
    elif fault=='unknown':values['groups']['groups'][0]['record_ids']=[]
    elif fault=='overlap':values['reservation']['confirmation_files'].append('187_rqh01.txt')
    elif fault=='hash':values['inspection']['source_sha256']='c'*64
    elif fault=='size':values['receipt']['size_bytes']=101
    elif fault=='gap':values['inspection']['gaps_above_1p5_nominal_periods']=1
    elif fault=='time':values['inspection']['last_gps_sow_s']=99.
    else:values['receiver_report']['source_file']='186_air1_ppp.txt'
    with pytest.raises(ValueError):library().validate_context(**values)


def text_rows(count):
    from lll.airquantumgrav_receiver import COLUMNS
    header='Datum: WGS84\n'+' '.join(COLUMNS)+'\n';lines=[]
    for i in range(count):
        v=[f'{i+1:08d}',65.,-50.,1500.,1.,1.,4.,0.,0.,0.,60.,0.,0.,1.,1.,1.,0.,0.,0.,2.,2.,8,2,2,0,0,1000.+i*.5,2269,'06/07/2023','12:00:00']
        lines.append(' '.join(map(str,v))+'\n')
    return (header+''.join(lines)).encode()


def test_bounded_decoder_charges_before_parsing_and_verifies_complete_hash():
    import hashlib
    raw=text_rows(3);charges=[];checks=[]
    result=library().decode(io.BytesIO(raw),expected_sha256=hashlib.sha256(raw).hexdigest(),
        maximum_epochs=4,block_size=2,reserve=lambda **v:charges.append(v),check_continue=lambda:checks.append(True))
    assert len(result['rows'])==3 and result['decoder_calls']==4 and result['reserved_decoder_calls']==4
    assert sum(v.get('decoder_calls',0) for v in charges)==4 and checks
    assert result['source_sha256']==hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('fault',['excess','hash','truncated_row','order'])
def test_bounded_decoder_rejects_incomplete_or_changed_sources(fault):
    import hashlib
    raw=text_rows(3);expected=hashlib.sha256(raw).hexdigest();maximum=4
    if fault=='excess':maximum=2
    elif fault=='hash':expected='0'*64
    elif fault=='truncated_row':raw=raw.rsplit(b' ',1)[0]+b'\n';expected=hashlib.sha256(raw).hexdigest()
    else:raw=raw.replace(b'1000.5',b'1000.0');expected=hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):library().decode(io.BytesIO(raw),expected_sha256=expected,maximum_epochs=maximum,
        block_size=2,reserve=lambda **v:None,check_continue=lambda:None)


def test_inventory_definition_has_no_model_or_native_allowance():
    r=library().recipe();tasks=library().tasks()
    assert len(tasks)==1 and all(v==0 for v in tasks[0]['limits'].values())
    assert r['maximum_receiver_epochs']==100000 and r['maximum_decoder_calls']==100001
    assert r['workers']==r['threads']==1 and r['raw_imu_reads']==r['observed_optimizer_starts']==0


def test_inventory_prepare_rejects_absent_qualification_before_inputs(tmp_path):
    with pytest.raises(ValueError,match='qualification'):library().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def evaluation_fixture(tmp_path,monkeypatch,count):
    import hashlib
    import json
    from types import SimpleNamespace
    from lll import ilvis0_control_shards
    mod=library();raw=text_rows(count);values=metadata()
    values['inspection'].update(first_gps_sow_s=1000.,last_gps_sow_s=4000.)
    values['receiver_report'].update(epochs=count,sha256=hashlib.sha256(raw).hexdigest())
    root=tmp_path/'data'/'inventory';root.mkdir(parents=True)
    (root/'manifest.json').write_text('{}')
    directory=root/'artifacts';directory.mkdir();inputs=root/'inputs';inputs.mkdir()
    material=dict(values,recipe=mod.recipe(),context=mod.validate_context(**values),
        **{'qualification-environment':mod.environment(),'source-reference':dict(path=mod.RECEIVER_PATH,
            filename=mod.RECEIVER_NAME,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))})
    for name,value in material.items():(inputs/(name+'.json')).write_text(json.dumps(value))
    original=tmp_path/mod.RECEIVER_PATH;original.parent.mkdir(parents=True);original.write_bytes(raw)
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *args:None)
    saved={};noted=[]
    def save(name,payload):
        assert name not in saved
        saved[name]=payload;(directory/name).write_bytes(payload)
    context=SimpleNamespace(root=root,directory=directory,manifest={'scope':mod.SCOPE},
        input_path=lambda name='source-reference':inputs/(name+'.json'),save_bytes=save,note_file=noted.append)
    return mod,context,saved,noted,original


@pytest.mark.parametrize('count,eligible',[(10,0),(2401,1)])
def test_inventory_evaluator_preserves_outputs_and_exact_accounting(tmp_path,monkeypatch,count,eligible):
    import csv
    import gzip
    import json
    mod,context,saved,noted,original=evaluation_fixture(tmp_path,monkeypatch,count)
    result=mod.evaluate(dict(mod.tasks()[0],index=0,shard=0),context)
    assert result['passed'] and result['eligible_count']==eligible
    assert result['receiver_epochs']==count and result['decoder_calls']==count+1
    assert result['charged_work']==dict(receiver_file_passes=1,selection_passes=1,
        decoder_calls=((count+1+1023)//1024)*1024)
    assert result['raw_imu_reads']==result['native_calls']==result['protected_reads']==0
    assert result['scientific_decision']=='abstain' and original.exists()
    selected=json.loads(gzip.decompress(saved['selection.json.gz']))
    assert selected['total_receiver_epochs']==count and len(selected['eligible'])==eligible
    assert len(list(csv.DictReader(io.StringIO(saved['eligible.csv'].decode()))))==eligible
    epochs=list(csv.DictReader(io.StringIO(gzip.decompress(saved['epoch-reasons.csv.gz']).decode())))
    assert len(epochs)==count and epochs[0]['sequence']=='1'
    assert len(noted)==1 and noted[0].is_file()


def test_inventory_evaluator_rejects_protected_group_before_opening_source(tmp_path,monkeypatch):
    import json
    mod,context,_,_,original=evaluation_fixture(tmp_path,monkeypatch,10)
    path=context.input_path('groups');value=json.loads(path.read_text())
    value['groups'][0]['role']='protected_confirmation';path.write_text(json.dumps(value));original.unlink()
    with pytest.raises(ValueError,match='development membership'):mod.evaluate(mod.tasks()[0],context)
    assert not (context.directory/'inventory-work.sqlite').exists()
