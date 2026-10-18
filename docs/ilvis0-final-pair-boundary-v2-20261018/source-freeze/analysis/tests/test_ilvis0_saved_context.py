# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import gzip
import json

import pytest


def inputs():
    saved=dict(active_parameters=['gravity_delta','time_offset'],normalized_parameters=[.2,.1],
        residual=[1.,2.,3.,4.,5.,6.],jacobian=[[.1,.2]]*6)
    fixes=[dict(time_s=100.25,latitude_rad=.5,longitude_rad=-1.,height_m=1000.),
        dict(time_s=101.25,latitude_rad=.51,longitude_rad=-1.01,height_m=1001.)]
    return saved,dict(times_s=[.25,1.25]),fixes


def test_receiver_records_become_exact_numeric_lat_lon_height_rows():
    from lll.ilvis0_saved_context import context_bytes
    values=inputs();before=copy.deepcopy(values)
    result=json.loads(gzip.decompress(context_bytes(*values,initial_time_s=100.)))
    assert values==before
    assert result['gps']==[[.5,-1.,1000.],[.51,-1.01,1001.]]
    assert result['times_s']==[.25,1.25]
    assert all(result[k]==v for k,v in values[0].items())
    assert context_bytes(*values,initial_time_s=100.)==context_bytes(*values,initial_time_s=100.)


@pytest.mark.parametrize('bad',['stale_time','reordered','missing_height','nonfinite','layout','stale_gps','stale_saved_time'])
def test_wrong_context_or_array_layout_fails_without_repair(bad):
    from lll.ilvis0_saved_context import context_bytes
    saved,epochs,fixes=inputs()
    if bad=='stale_time':epochs['times_s'][0]+=.01
    if bad=='reordered':fixes.reverse()
    if bad=='missing_height':del fixes[0]['height_m']
    if bad=='nonfinite':fixes[0]['latitude_rad']=float('nan')
    if bad=='layout':saved['jacobian'][0]=[.1]
    if bad=='stale_gps':saved['gps']=fixes
    if bad=='stale_saved_time':saved['times_s']=[.3,1.3]
    with pytest.raises(ValueError):context_bytes(saved,epochs,fixes,initial_time_s=100.)


def test_reference_packet_time_and_saved_relative_epochs_agree_for_both_real_sources():
    import hashlib
    from pathlib import Path
    from lll.ilvis0_saved_context import context_bytes
    root=Path(__file__).resolve().parents[2]
    manifest=json.loads((root/'data/ilvis0-final-pair-boundary-20261018/manifest.json').read_text())
    targets=[t for t in manifest['plan']['tasks'] if t['kind']=='target']
    assert len(targets)==2
    for task in targets:
        arrays=[]
        for artifact in (task['original_linearization'],task['context_epoch']):
            path=Path(artifact['path'])
            assert hashlib.sha256(path.read_bytes()).hexdigest()==artifact['sha256']
            arrays.append(json.loads(gzip.decompress(path.read_bytes())))
        fixes=task['task']['selected']['segment']['receiver_fixes']
        origin=task['task']['provenance']['first_interval_start_utc_s']
        result=json.loads(gzip.decompress(context_bytes(*arrays,fixes,initial_time_s=origin)))
        assert result['gps']==[[r['latitude_rad'],r['longitude_rad'],r['height_m']] for r in fixes]
        assert result['times_s']==[r['time_s']-origin for r in fixes]
