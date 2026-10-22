# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import numpy as np
import pytest


def test_counter_identifies_an_exact_boundary_without_calling_it_motion_failure():
    from lll.ilvis0_packet_boundary_flags import validate
    assert validate(status=0,counter=1,dt=[.125]*32,time_s=2.,clock_offset_s=.25)['packet_boundary']
    assert not validate(status=0,counter=0,dt=[.125]*32,time_s=2.01,clock_offset_s=.25)['packet_boundary']


@pytest.mark.parametrize('values',[
    dict(status=1,counter=0,dt=[.125]*32,time_s=2.,clock_offset_s=0.),
    dict(status=0,counter=2,dt=[.125]*32,time_s=2.,clock_offset_s=0.),
    dict(status=0,counter=0,dt=[.125]*32,time_s=2.,clock_offset_s=0.),
    dict(status=0,counter=1,dt=[.125]*32,time_s=2.01,clock_offset_s=0.),
    dict(status=0,counter=0,dt=[.125,0.],time_s=.1,clock_offset_s=0.),
    dict(status=0,counter=0,dt=[.125]*32,time_s=5.,clock_offset_s=0.),
    dict(status=0,counter=0,dt=[.125]*32,time_s=-1.,clock_offset_s=0.),
])
def test_status_counter_support_and_timestamp_mismatch_are_rejected(values):
    from lll.ilvis0_packet_boundary_flags import validate
    with pytest.raises(ValueError):validate(**values)


def test_all_six_failed_starts_were_successful_queries_at_packet_boundaries():
    from lll.ilvis0_packet_boundary_flags import validate
    root=Path(__file__).parents[2]/'docs/ilvis0-long-staged-feasibility'
    # This is a sealed saved-data regression, not another native evaluation.
    if not (root/'manifest.json').exists():pytest.skip('saved diagnostic unavailable')
    manifest=json.loads((root/'manifest.json').read_text())
    for task in manifest['tasks']:
        case=json.loads((root/manifest['inputs'][task['payload']['case_key']]['path']).read_text())
        record=json.loads((root/'artifacts'/task['identity']/'native-01.json').read_text())
        checked=validate(status=record['status'],counter=record['warning'],dt=case['dt'],time_s=record['time_s'],
            clock_offset_s=case['configuration']['limits'][25]*record['point'][25])
        assert checked['packet_boundary'] and checked['query_supported']


def test_classification_matches_real_native_kernel_and_preserves_derivatives(tmp_path):
    from lll.ilvis0_packet_boundary_flags import validate
    from lll.ilvis0_shape import load_tangent
    import ctypes
    from test_ilvis0_native_box_bounds import configuration
    kernel,_=load_tangent(tmp_path);c=configuration();n=32
    dt=np.full(n,.125);theta=np.zeros((n,3));dv=np.tile([0.,0.,-9.81*.125],(n,1))
    for t in (2.,2.01):
        out=np.empty((1,3));jac=np.empty((3,27));counter=ctypes.c_int();point=np.zeros(27)
        status=kernel(n,theta,dv,dt,1,np.array([t]),c['initial_c'],c['initial_v'],c['initial_r'],c['limits'],
            point,c['model'],int(c['profile']),c['gravity'],c['radius'],out,jac,ctypes.byref(counter))
        checked=validate(status=status,counter=counter.value,dt=dt,time_s=t,clock_offset_s=0.)
        assert checked['packet_boundary']==(t==2.)
        assert np.all(np.isfinite(out)) and np.all(np.isfinite(jac))
