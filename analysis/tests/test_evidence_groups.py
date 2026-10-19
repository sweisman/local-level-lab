# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll import evidence_groups as groups


POLICY=dict(version='test',development_files=['dev.txt'],confirmation_files=['a.txt','b.txt'])


def nasa(identity,start='2009-10-20T00:00:00Z',end='2009-10-20T00:05:00Z',source=None):
    return dict(segment_id=identity,filename=identity+'.013',source_sha256=source or identity,
        start_utc=start,end_utc=end,imu_type='8',mounting_epoch='same_configuration',shared_leg_id='')


def esa(filename,date='2023-07-01',flights='a'):
    return dict(filename=filename,date=date,flight_ids=flights,local_sha256='')


def test_same_day_is_conservative_split_group_not_verified_instrument_or_flight():
    result=groups.build([nasa('x'),nasa('y',start='2009-10-20T01:00:00Z',end='2009-10-20T01:05:00Z')],[],[],POLICY)
    assert len(result['groups'])==1
    assert result['groups'][0]['identity_status']=='conservative split group; physical flight/installation not verified'
    assert all(r['physical_instrument_id'] is None for r in result['records'])
    assert any(r['kind']=='same_utc_day' for r in result['relations'])


def test_equal_mounting_configuration_does_not_merge_distinct_dates():
    result=groups.build([nasa('x'),nasa('y','2009-10-21T00:00:00Z','2009-10-21T00:05:00Z')],[],[],POLICY)
    assert len(result['groups'])==2


def test_byte_aliases_remain_together_even_across_dates():
    result=groups.build([nasa('x',source='alias'),nasa('y','2009-10-21T00:00:00Z','2009-10-21T00:05:00Z','alias')],[],[],POLICY)
    assert len(result['groups'])==1
    assert any(r['kind']=='same_source_hash' for r in result['relations'])


def test_midnight_overlap_remains_together():
    result=groups.build([nasa('x','2009-10-20T23:59:00Z','2009-10-21T00:02:00Z'),
        nasa('y','2009-10-21T00:01:00Z','2009-10-21T00:05:00Z')],[],[],POLICY)
    assert len(result['groups'])==1
    assert any(r['kind']=='utc_overlap' for r in result['relations'])


def test_shared_leg_candidate_is_labeled_candidate_not_confirmed():
    pair=dict(left_segment_id='x',right_segment_id='y',same_track_candidate='True',shared_leg_id='leg')
    result=groups.build([nasa('x'),nasa('y')],[pair],[],POLICY)
    edge=next(r for r in result['relations'] if r['kind']=='candidate_shared_leg')
    assert edge['confidence']=='candidate'


def test_esa_shared_file_flight_labels_and_dates_cannot_inflate_units():
    result=groups.build([],[],[esa('a.txt',flights='a;b'),esa('b.txt',flights='b')],POLICY)
    assert len(result['groups'])==1 and result['groups'][0]['role']=='protected_confirmation'
    assert result['groups'][0]['reported_flight_labels']==['a','b']


def test_reservation_rejects_mixed_group():
    with pytest.raises(ValueError,match='development.*confirmation'):
        groups.build([],[],[esa('dev.txt'),esa('a.txt')],POLICY)


def test_unknown_esa_filename_and_invalid_policy_fail_closed():
    with pytest.raises(ValueError,match='unassigned'):
        groups.build([],[],[esa('unknown.txt')],POLICY)
    with pytest.raises(ValueError,match='overlap'):
        groups.build([],[],[],dict(POLICY,confirmation_files=['dev.txt']))


def test_order_independent_stable_ids_and_group_counts():
    rows=[nasa('x'),nasa('y')]
    assert groups.build(rows,[],[],POLICY)==groups.build(list(reversed(rows)),[],[],POLICY)


def test_invalid_intervals_duplicate_ids_and_unknown_pair_endpoints_rejected():
    with pytest.raises(ValueError):groups.build([nasa('x',end='2009-10-19T00:00:00Z')],[],[],POLICY)
    with pytest.raises(ValueError):groups.build([nasa('x'),nasa('x')],[],[],POLICY)
    with pytest.raises(ValueError):groups.build([nasa('x')],[dict(left_segment_id='x',right_segment_id='missing')],[],POLICY)


def test_development_guard_rejects_confirmation_group_and_unknown_identity():
    result=groups.build([],[],[esa('dev.txt',date='2023-07-06')],POLICY)
    identity=result['groups'][0]['group_id']
    groups.require_development(result,[identity])
    protected=groups.build([],[],[esa('a.txt')],POLICY)
    with pytest.raises(ValueError):groups.require_development(protected,[protected['groups'][0]['group_id']])
    with pytest.raises(ValueError):groups.require_development(result,['missing'])
