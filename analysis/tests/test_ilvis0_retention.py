# SPDX-License-Identifier: AGPL-3.0-or-later
import gzip
import hashlib
import io
import json
from pathlib import Path
import struct

import pytest

from lll import applanix as ap,ilvis0_retention as retention
from test_applanix import packet


def test_only_exact_duplicate_hashes_with_actual_date_preference():
    def row(task,date,actual,hash):
        return dict(task_id=task,date=date,timing=dict(dates=[actual]),screen=dict(state='unresolved'),
                    inspection=dict(source_sha256=hash))
    rows=[row('wrong','2010-04-22','2010-04-21','same'),row('right','2010-04-21','2010-04-21','same'),
          row('other','2010-04-21','2010-04-21','different')]
    assert retention.duplicate_plan(rows,{'wrong','right','other'})=={'wrong':'right'}
    assert retention.duplicate_plan(rows,{'wrong'})=={}


def test_clean_IMU_spans_do_not_bridge_gaps_or_add_disjoint_parts():
    windows=[dict(start_s=10,end_s=130,duration_s=120)]
    checked=retention.intersect_runs([[0,50],[55,90],[95,140]],windows)[0]
    assert checked['clean_imu_seconds']==110
    assert checked['longest_clean_imu_s']==40
    assert checked['coverage_fraction']==pytest.approx(110/120)


def test_fused_motion_diagnostic_does_not_bridge_failed_samples():
    nav=[dict(utc_week_s=t,alignment_status=1,roll_deg=0,speed_mps=100,velocity_down_mps=0,
              velocity_north_mps=100,velocity_east_mps=0) for t in range(150)]
    nav[75]['roll_deg']=10
    result=retention.navigation_context(nav,[],[dict(start_s=0,end_s=149,duration_s=149)])
    assert result['longest_motion_compatible_span_s']<75
    assert not result['earth_model_eligible']
    assert result['alignment_counts']=={1:148}


def test_real_frame_checksum_and_source_hash_preserved_in_retention_audit(tmp_path):
    packets=[]
    for i in range(13001):
        body=bytearray(56); struct.pack_into('<3d',body,0,1+i*.005,.8+i*.005,0)
        body[24]=2; body[51]=6;body[52]=2
        packets.append(packet(4,body))
    raw=b''.join(packets);source=tmp_path/'source.013.gz'
    with gzip.open(source,'wb') as stream:stream.write(raw)
    context=dict(timing=dict(gps_minus_utc_s=15),inspection=dict(source_sha256=hashlib.sha256(raw).hexdigest()))
    result=retention.audit_source(source,context,[dict(start_s=2,end_s=64,duration_s=62)])
    assert result['storage_decision']=='keep' and result['windows_with_60s_clean_imu']==1
    assert not result['scientific_eligible'] and result['imu_types']=={6:13001}
    context['inspection']['source_sha256']='wrong'
    with pytest.raises(ValueError,match='SHA-256'):retention.audit_source(source,context,[])


def duplicate_corpus(tmp_path):
    corpus=tmp_path/'corpus';output=tmp_path/'audit';corpus.mkdir();output.mkdir()
    (corpus/'ownership.json').write_text(json.dumps(dict(owner=retention.OWNERSHIP)))
    raw=b'preserved original';records=[];results=[]
    for task in ('original','copy'):
        records.append(dict(task_id=task,filename=task+'.013'))
        results.append(dict(task_id=task,source_sha256=hashlib.sha256(raw).hexdigest()))
        path=corpus/task/'decoded'/(task+'.013.gz');path.parent.mkdir(parents=True)
        with gzip.open(path,'wb') as stream:stream.write(raw)
    (corpus/'records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    return corpus,output,results


def test_duplicate_removal_verifies_both_originals_and_journals(tmp_path):
    corpus,output,(canonical,rejected)=duplicate_corpus(tmp_path)
    ledger=(corpus/'records.jsonl').read_bytes()
    entry=retention.remove_duplicate(corpus,output,rejected,canonical)
    assert Path(entry['canonical_path']).is_file() and not Path(entry['removed_path']).exists()
    assert (corpus/'records.jsonl').read_bytes()==ledger
    rows=[json.loads(r) for r in (output/'cleanup.jsonl').read_text().splitlines()]
    assert [r['state'] for r in rows]==['prepared','removed']


def test_recovery_after_unlink_before_final_journal(tmp_path):
    corpus,output,(canonical,rejected)=duplicate_corpus(tmp_path)
    entry=retention.remove_duplicate(corpus,output,rejected,canonical)
    journal=output/'cleanup.jsonl';prepared=journal.read_text().splitlines()[0]
    journal.write_text(prepared+'\n')
    assert retention.remove_duplicate(corpus,output,rejected,canonical)['source_sha256']==entry['source_sha256']
    assert json.loads(journal.read_text().splitlines()[-1])['state']=='removed'


def test_corrupt_canonical_prevents_duplicate_deletion(tmp_path):
    corpus,output,(canonical,rejected)=duplicate_corpus(tmp_path)
    path=corpus/'original'/'decoded'/'original.013.gz'
    with gzip.open(path,'wb') as stream:stream.write(b'changed')
    with pytest.raises(ValueError,match='changed'):retention.remove_duplicate(corpus,output,rejected,canonical)
    assert (corpus/'copy'/'decoded'/'copy.013.gz').is_file()
