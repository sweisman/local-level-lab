# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

import airquantumgrav_selection_worker as worker


def test_scope_is_one_development_inventory_without_raw_imu_reads():
    assert worker.LIMITS['maximum_identities']==1
    assert worker.LIMITS['maximum_receiver_epochs']==100000
    assert worker.LIMITS['raw_imu_reads']==worker.LIMITS['optimizer_starts']==worker.LIMITS['native_evaluations']==0


def test_protected_or_unknown_groups_cannot_be_development_inputs():
    ledger={'groups':[{'group_id':'dev','role':'development','record_ids':['esa:187_rqh01.txt']},
        {'group_id':'protected','role':'protected_confirmation','record_ids':['esa:186_rqh01.txt']}]}
    assert worker.development_group(ledger,'187_rqh01.txt')=='dev'
    for filename in ('186_rqh01.txt','unknown.txt'):
        with pytest.raises(ValueError):worker.development_group(ledger,filename)


def test_incomplete_source_inspection_is_not_a_pass():
    valid=dict(source_file='187_rqh01.txt',source_sha256='a',byte_size=123,gaps_above_1p5_nominal_periods=0,
        first_gps_sow_s=100.,last_gps_sow_s=200.)
    receipt=dict(sha256='a',size_bytes=123)
    assert worker.checked_support(valid,receipt)==(100.,200.)
    for field,value in [('source_sha256','b'),('gaps_above_1p5_nominal_periods',1),('byte_size',124)]:
        changed=dict(valid);changed[field]=value
        with pytest.raises(ValueError):worker.checked_support(changed,receipt)


def test_inventory_cannot_restart_a_charged_identity(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path)
    (tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()
