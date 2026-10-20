# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import json
from pathlib import Path
import pytest
from lll.ilvis0_support_accounting import check_case


def fixture(tmp_path):
    steps=[(1,3)]*6+[(0,6)]+[(1,3)]*6+[(0,6)]
    counters=[0,0];artifacts={}
    for i,step in enumerate(steps,1):
        counters=[a+b for a,b in zip(counters,step)]
        name=f'artifacts/case/reservation-{i:02d}.json';path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(dict(lp_proposals=counters[0],exact_supports=counters[1])))
        artifacts[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    record=dict(artifacts=artifacts,result=dict(identity='case',passed=True,
        lp_proposals_reserved=12,exact_supports_reserved=48))
    return record,steps


def test_checks_every_precharged_step_and_final_allowance(tmp_path):
    record,steps=fixture(tmp_path)
    result=check_case(tmp_path,record,steps=steps,maximum_proposals=12,maximum_supports=48)
    assert result==dict(identity='case',reservation_events=14,lp_proposals=12,exact_supports=48,passed=True)


@pytest.mark.parametrize('change',['missing','hash','counter','summary','extra','maximum','outside'])
def test_rejects_unverifiable_or_excess_reservations(tmp_path,change):
    record,steps=fixture(tmp_path);maximum=48
    name='artifacts/case/reservation-01.json';path=tmp_path/name
    if change=='missing':del record['artifacts'][name]
    elif change=='hash':path.write_text('{}')
    elif change=='counter':
        path.write_text(json.dumps(dict(lp_proposals=0,exact_supports=0)))
        record['artifacts'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
    elif change=='summary':record['result']['exact_supports_reserved']=47
    elif change=='extra':record['artifacts']['artifacts/case/reservation-15.json']='0'*64
    elif change=='maximum':maximum=47
    else:record['artifacts']['../reservation-15.json']='0'*64
    with pytest.raises(ValueError):check_case(tmp_path,record,steps=steps,maximum_proposals=12,maximum_supports=maximum)
