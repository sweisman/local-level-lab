# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import numpy as np
import pytest
from scipy.linalg import expm
from test_ilvis0_source_norm_preflight import fixture


def test_streaming_source_reference_exists():
    assert importlib.util.find_spec('lll.ilvis0_source_stream') is not None


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    from lll.ilvis0_source_stream import load_stream
    return load_stream(tmp_path_factory.mktemp('source-stream'))[0]


def oracle(case,point,time):
    """Independent complex matrix exponentials, not native Dual arithmetic."""
    p=np.asarray(case['configuration']['limits'])*point
    def skew(v):
        x,y,z=v
        return np.array([[0,-z,y],[z,0,-x],[-y,x,0]],dtype=np.result_type(v))
    r=np.asarray(case['configuration']['initial_r'])@expm(skew(p[:3]))
    f=(np.asarray(case['dv'][0])-p[12:15]*case['dt'][0])/(1+p[18:21])/case['dt'][0]
    body=np.eye(3,dtype=np.result_type(point));start=0.;query=time+p[25];result=[]
    for raw,dt in zip(case['theta'],case['dt'],strict=True):
        end=start+dt
        if start<query.real<=end or start==query.real==0:fraction=(query-start)/dt
        else:fraction=1 if query.real>end else 0
        angle=(np.asarray(raw)-p[9:12]*dt)/(1+p[15:18])*fraction
        stages=[]
        for part in (.5,1.):
            current=body@expm(skew(angle*part))
            stages.append([r@f,r@(current-np.eye(3))@f])
        body=current;result.append(stages);start=end
    return np.asarray(result)


def test_all_prefix_midpoints_and_endpoints_match_independent_columns(kernel):
    from lll.ilvis0_source_stream import SourceStream
    case,_,_,_=fixture();case['configuration']['limits'][25]=.001
    case['dt']=[.004,.006,.005,.007];case['theta']=case['theta'][:4];case['dv']=case['dv'][:4]
    point=np.linspace(-.1,.2,27);time=.01123
    with SourceStream(kernel,case,point,time,maximum_packets=4) as stream:
        reports=[stream.append() for _ in range(4)]
        assert stream.visits==4 and stream.state_bytes<16384
        with pytest.raises(ValueError,match='allowance'):stream.append()
    expected=oracle(case,point.astype(complex),time).real
    jac=np.empty(expected.shape+(27,))
    for axis in range(27):
        probe=point.astype(complex);probe[axis]+=1e-24j
        jac[...,axis]=oracle(case,probe,time).imag/1e-24
    for index,report in enumerate(reports):
        np.testing.assert_allclose(report['values'],expected[index],atol=2e-12,rtol=1e-9)
        np.testing.assert_allclose(report['jacobian'],jac[index],atol=2e-11,rtol=2e-8)
        assert report['packet_index']==index and report['parameter_count']==27
    with pytest.raises(ValueError,match='closed'):stream.append()


def test_exact_boundary_and_first_timestamp_keep_native_slope(kernel):
    from lll.ilvis0_source_stream import SourceStream
    case,_,_,_=fixture();case['configuration']['limits'][25]=.001
    case['dt']=[.005,.005];case['theta']=[[0,.001,0],[0,.005,0]];case['dv']=[[0,0,-.04905]]*2
    for time,slopes in ((.005,[200.,0.]),(0.,[200.,0.])):
        with SourceStream(kernel,case,np.zeros(27),time,maximum_packets=2) as stream:
            reports=[stream.append(),stream.append()]
        assert [r['time_slope'] for r in reports]==slopes
        expected=oracle(case,np.zeros(27,dtype=complex),time)
        probe=np.zeros(27,dtype=complex);probe[25]=1e-24j
        derivative=oracle(case,probe,time).imag/1e-24
        np.testing.assert_allclose([r['values'] for r in reports],expected.real,atol=1e-12)
        np.testing.assert_allclose(np.array([r['jacobian'] for r in reports])[...,25],derivative,atol=1e-11)


def test_clock_support_and_packet_allowance_are_enforced(kernel):
    from lll.ilvis0_source_stream import SourceStream
    case,_,_,_=fixture()
    with pytest.raises(ValueError,match='support'):SourceStream(kernel,case,np.zeros(27),2.,maximum_packets=13)
    with pytest.raises(ValueError,match='allowance'):SourceStream(kernel,case,np.zeros(27),.04,maximum_packets=14)


def test_source_inputs_are_not_changed_by_caller_mutation(kernel):
    from lll.ilvis0_source_stream import SourceStream
    case,_,_,_=fixture();case['theta']=np.asarray(case['theta']);case['dt']=np.asarray(case['dt'])
    expected=oracle(case,np.zeros(27),.04)[0]
    with SourceStream(kernel,case,np.zeros(27),.04,maximum_packets=13) as stream:
        case['theta'][:]=.5;case['dt'][:]=.1
        np.testing.assert_allclose(stream.append()['values'],expected,atol=1e-12)


def test_independent_stream_oracle_exists():
    assert importlib.util.find_spec('lll.ilvis0_source_stream_controls') is not None


def test_analytic_stream_matches_complex_matrix_exponentials():
    from lll.ilvis0_source_stream_controls import analytic_prefixes
    case,_,_,_=fixture();case['configuration']['limits'][25]=.001
    case['dt']=[.004,.006,.005];case['theta']=case['theta'][:3];case['dv']=case['dv'][:3]
    point=np.linspace(-.1,.1,27);time=.00671
    rows=list(analytic_prefixes(case,point,time));expected=oracle(case,point.astype(complex),time)
    np.testing.assert_allclose([r['values'] for r in rows],expected.real,atol=1e-12)
    jac=np.asarray([r['jacobian'] for r in rows])
    for column in range(27):
        probe=point.astype(complex);probe[column]+=1e-24j
        np.testing.assert_allclose(jac[...,column],oracle(case,probe,time).imag/1e-24,atol=2e-11,rtol=2e-8)
