# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from lll.ilvis0_recording_fixture import extend


def parent(model=0,profile=False):
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-recording-adapter-controls/saved-inputs'/f'recording-api-{model}-{int(profile)}.json'
    raw=path.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
def test_extended_case_preserves_original_prefix_and_every_nonclock_limit(model,profile):
    source,digest=parent(model,profile); before=deepcopy(source)
    result=extend(source,packets=96000,clock_offset_s=1.,parent_sha256=digest)
    assert source==before
    assert len(result['dt'])==96000
    for name in ('theta','dv','dt'):
        assert np.array(result[name][:48000],dtype='<f8').tobytes()==np.array(source[name],dtype='<f8').tobytes()
    expected=deepcopy(source['configuration']); expected['limits'][25]=1.
    assert result['configuration']==expected
    assert len(result['center'])==27 and result['center']==source['center']
    p=result['provenance']
    assert p['parent_case_sha256']==digest and p['preserved_prefix_packets']==48000
    assert p['generated_suffix_packets']==48000 and not p['clock_offset_fixed']
    assert not p['training_certificate_transferred'] and 'truth' not in result
    elapsed=0.
    for period in result['dt']:elapsed+=period
    assert p['sequential_endpoint_s']==elapsed
    assert 438.+1.<elapsed and 478.+1.<elapsed


def test_the_suffix_continues_the_recipe_instead_of_repeating_or_zero_padding():
    source,digest=parent(); result=extend(source,packets=96000,clock_offset_s=1.,parent_sha256=digest)
    for index in (48000,60000,95999):
        t=index*.005
        expected_theta=.005*np.array([2e-5+3e-4*np.sin(.03*t),-3e-5+2e-4*np.cos(.02*t),1e-5+5e-4*np.sin(.01*t)])
        expected_dv=.005*np.array([.02*np.sin(.05*t),.02*np.cos(.04*t),-9.81+.01*np.sin(.03*t)])
        np.testing.assert_array_equal(result['theta'][index],expected_theta)
        np.testing.assert_array_equal(result['dv'][index],expected_dv)
    assert result['theta'][48000]!=source['theta'][0]


@pytest.mark.parametrize('packets',[48000,47999,500001,96000.5,True])
def test_rejects_nonextension_or_unsupported_size(packets):
    source,digest=parent()
    with pytest.raises(ValueError):extend(source,packets=packets,clock_offset_s=1.,parent_sha256=digest)


@pytest.mark.parametrize('clock',[-1.,float('nan'),float('inf'),False])
def test_rejects_invalid_clock_declaration(clock):
    source,digest=parent()
    with pytest.raises(ValueError):extend(source,packets=96000,clock_offset_s=clock,parent_sha256=digest)


@pytest.mark.parametrize('change',['measurement','period','clock','scope','hash'])
def test_rejects_changed_parent_recipe_or_unrecognized_source(change):
    source,digest=parent()
    if change=='measurement':source['theta'][10][2]+=.001
    elif change=='period':source['dt'][10]=.006
    elif change=='clock':source['configuration']['limits'][25]=1.
    elif change=='scope':source['provenance']['scope']='aircraft observation'
    else:digest='invalid'
    with pytest.raises(ValueError):extend(source,packets=96000,clock_offset_s=1.,parent_sha256=digest)
