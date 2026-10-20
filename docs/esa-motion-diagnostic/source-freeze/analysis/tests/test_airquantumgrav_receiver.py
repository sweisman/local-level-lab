# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll import airquantumgrav_receiver as receiver


def stream(overrides=None):
    values=['0','65','-50','1500','1','1','4','0','0','0','60','0','0',
        '1','1','1','0','0','0','2','2','8','0','0','0','0','1000','2269','06/07/2023','12:00:00']
    for index,value in (overrides or {}).items():values[index]=str(value)
    values[0]=f'{int(values[0]):08d}'
    return ['Datum: WGS84 (2023.512)\n',' '.join(receiver.COLUMNS)+'\n',' '.join(values)+'\n']


def test_primary_receiver_fields_and_quality_channels_remain_separate():
    row=list(receiver.records(stream()))[0]
    assert row['time_s']==1000. and row['gps_week']==2269
    assert row['north_mps']==60. and row['up_mps']==0.
    assert row['satellites']==8 and row['position_variance_m2']==[1.,1.,4.]
    assert row['utc_date']=='06/07/2023'


@pytest.mark.parametrize('index,value',[(1,'nan'),(26,'inf'),(27,'2269.5'),(21,'7.5'),(22,'-1'),(26,'604800')])
def test_nonfinite_or_unsupported_format_is_rejected(index,value):
    with pytest.raises(ValueError):list(receiver.records(stream({index:value})))


def test_quality_failure_is_preserved_for_selector_not_repaired():
    assert list(receiver.records(stream({4:0})))[0]['position_variance_m2'][0]==0.


def test_header_and_datum_must_match():
    lines=stream();lines[1]=lines[1].replace('VNorth','Other')
    with pytest.raises(ValueError):list(receiver.records(lines))
    lines=stream();lines[0]='Datum: unknown\n'
    with pytest.raises(ValueError):list(receiver.records(lines))


@pytest.mark.parametrize('kind',['duplicate','reverse','truncated','trailer','week'])
def test_corrupt_or_discontinuous_input_fails_strictly(kind):
    lines=stream()
    if kind in ('duplicate','reverse','week'):
        other={0:1,26:1000 if kind=='duplicate' else 999 if kind=='reverse' else 1000.5}
        if kind=='week':other[27]=2270
        lines+=stream(other)[-1:]
    elif kind=='truncated':lines[-1]=' '.join(lines[-1].split()[:-1])+'\n'
    else:lines+=['unexpected trailer\n']
    with pytest.raises(ValueError):list(receiver.records(lines))
