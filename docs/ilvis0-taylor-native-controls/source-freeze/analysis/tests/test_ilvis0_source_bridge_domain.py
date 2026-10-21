# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib,importlib.util
from pathlib import Path
from fractions import Fraction as F
import json
import numpy as np
from lll.ilvis0_sharded_native import read
from lll.ilvis0_transform_native import make_reference
from lll.ilvis0_initial_source_bridge import certify as old_certify


def original_broad_case():
    root=Path(__file__).resolve().parents[2]/'docs/ilvis0-transform-native-controls'
    manifest=json.loads((root/'manifest.json').read_text())
    task=next(t for t in manifest['tasks'] if t['payload']['kind']=='broad')
    case=read(root/manifest['inputs'][task['input_key']]['path'])
    config={k:np.asarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    case=dict(case,configuration=config)
    reference=make_reference(config,case['theta'],case['dv'],case['dt'],
        lower=case['lower'],upper=case['upper'],center=case['center'])
    return case,reference


def test_actual_asymmetric_box_certifies_the_unchanged_cap():
    name='lll.ilvis0_initial_source_bridge_v2'
    assert importlib.util.find_spec(name) is not None,'asymmetric-domain source proof is not implemented'
    candidate=importlib.import_module(name)
    case,reference=original_broad_case()
    old=old_certify(reference,case['lower'],case['upper'])
    report=candidate.certify(reference,case['lower'],case['upper'])
    assert not old['nonlinear_cap_sufficient']
    assert report['nonlinear_cap_sufficient']
    assert F(report['nonlinear_remainder'])<=F(report['original_nonlinear_cap'])<F(old['nonlinear_remainder'])
    for field in ('center_lower','center_upper','row_lower','row_upper','padding','reference_binding','source_id'):
        assert report[field]==old[field]
    assert report['original_nonlinear_cap']==old['original_nonlinear_cap']
    assert not report['nonlinear_cap_expanded']


def test_broad_source_domain_is_handled_without_a_forced_vertical_branch(tmp_path):
    from lll.ilvis0_rounded_body_interval_v2 import RoundedBodyInterval
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_source_value_stream import SourceValueStream
    from lll.ilvis0_source_stream import SourceStream,load_stream
    case,reference=original_broad_case();lo=case['lower'];hi=case['upper'];time=case['time_s']
    conditioning=DirectionalAcceleration(reference,lo,hi)
    adapter=RoundedBodyInterval(reference,conditioning,lo,hi)
    kernel=load_stream(tmp_path)[0]
    with SourceValueStream(case,reference,lo,hi,time,maximum_packets=1) as physical,SourceStream(
            kernel,case,case['center'],time,maximum_packets=1) as nominal:
        proof=physical.append()['phases'][0];frame=nominal.append()
    result=adapter.bound(proof,frame,phase=0)
    assert result.jacobian.shape==(2,3,27)
