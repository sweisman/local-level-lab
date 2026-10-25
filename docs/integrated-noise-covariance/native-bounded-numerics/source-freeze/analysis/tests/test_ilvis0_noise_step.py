# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
from pathlib import Path
import pytest


def hashes():
    values={name:hashlib.sha256(Path('analysis/lll',name).read_bytes()).hexdigest()
        for name in ('ilvis0_tangent.cpp','ilvis0_wide_tangent.py','ilvis0_noise_bridge.cpp',
            'ilvis0_noise_step.py','native_build.py')}
    values['tests']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    values['plan']=hashlib.sha256(Path('docs/native-noise-linearization/PLAN.md').read_bytes()).hexdigest()
    return values


def test_noise_step_derivation_requires_exact_sources_and_reuses_motion_helpers():
    from lll.ilvis0_noise_step import derive
    source=Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()
    bridge=Path('analysis/lll/ilvis0_noise_bridge.cpp').read_bytes();h=hashes()
    args=dict(expected_source_sha256=h['ilvis0_tangent.cpp'],expected_bridge_sha256=h['ilvis0_noise_bridge.cpp'],
        expected_wide_loader_sha256=h['ilvis0_wide_tangent.py'])
    result=derive(source,bridge,**args)
    assert b'std::array<long double,15>' in result and b'static void step_gravity' in result
    assert b'static int tangent_gravity' not in result
    assert result.endswith(bridge)
    with pytest.raises(ValueError,match='hash'):derive(source,bridge,**dict(args,expected_source_sha256='0'*64))


@pytest.fixture(scope='session')
def kernels(tmp_path_factory):
    import os
    import gzip
    from lll.studies.artifacts import atomic,digest,encoded
    from lll.studies.journal import Journal
    from lll.ilvis0_noise_step import load
    from lll.ilvis0_wide_tangent import load as wide_load
    directory=tmp_path_factory.mktemp('noise-step-kernels');h=hashes()
    path=Path(os.environ.get('LLL_NOISE_STEP_JOURNAL',str(directory/'charges.sqlite')))
    if path.exists():raise ValueError('fresh one-packet qualification journal required')
    freeze=digest(encoded(dict(sources=h,scope='generated one-packet controls',native_calls=500,builds=2)))
    journal=Journal(path,freeze=freeze,limits={'qualification':dict(native_calls=500,builds=2)})
    journal.start('qualification')
    def native(**counts):
        for key,value in counts.items():journal.reserve('qualification',key,value)
    def build():native(builds=1)
    kernel,metadata=load(directory,expected_source_sha256=h['ilvis0_tangent.cpp'],
        expected_bridge_sha256=h['ilvis0_noise_bridge.cpp'],expected_wide_loader_sha256=h['ilvis0_wide_tangent.py'],reserve_build=build)
    build();reference,rm=wide_load(directory,expected_source_sha256=h['ilvis0_tangent.cpp'])
    def reference_call(*args,**kwargs):native(native_calls=1);return reference(*args,**kwargs)
    yield dict(kernel=kernel,metadata=metadata,reference=reference_call,reserve=native,directory=directory)
    journal.verify()
    assert journal.count('qualification','builds')==2
    if 'LLL_NOISE_STEP_JOURNAL' in os.environ:
        artifacts={}
        for label,source_name,binary_name,meta in (
                ('bridge',metadata['source_file'],metadata['binary_file'],metadata),
                ('reference','wide-tangent-'+rm['source_sha256']+'.cpp','wide-tangent-'+rm['source_sha256']+'.so',rm)):
            for kind,name,key in (('source',source_name,'source_sha256'),('binary',binary_name,'binary_sha256')):
                raw=(directory/name).read_bytes();assert digest(raw)==meta[key]
                target=path.with_name(path.stem+'.'+label+'.'+kind+'.gz')
                compressed=gzip.compress(raw,mtime=0);atomic(target,compressed)
                artifacts[target.name]=dict(raw_sha256=digest(raw),gzip_sha256=digest(compressed))
        atomic(path.with_suffix('.compilation.json'),encoded(dict(bridge=metadata,reference=rm,
            artifacts=artifacts,charged_native_calls=journal.count('qualification','native_calls'),
            charged_builds=journal.count('qualification','builds'),journal_freeze=freeze)))


def call(kernels,case,*,seed=True):
    from lll.ilvis0_noise_step import evaluate
    return evaluate(kernels['kernel'],**case,derivatives=seed,reserve=kernels['reserve'])


def example(model=0,removal=0.,height=False):
    import numpy as np
    from scipy.spatial.transform import Rotation
    dt=.005 if model!=2 else 1/300
    return dict(coordinates=np.array([.95,-.7,2200.],dtype=np.longdouble),
        velocity=np.array([150.,-45.,-2.],dtype=np.longdouble),
        rotation=Rotation.from_euler('xyz',[.04,-.03,.7]).as_matrix().astype(np.longdouble),
        theta=np.array([.2,-.3,.1],dtype=np.longdouble)*np.longdouble(dt),
        delta_v=np.array([.4,.2,-9.8],dtype=np.longdouble)*np.longdouble(dt),
        dt=np.longdouble(dt),model=model,gravity=np.longdouble(9.8),radius=np.longdouble(6371000.),
        removal=np.longdouble(removal),anchor_height=2200. if height else None,
        lever=np.array([.2,-.1,.05],dtype=np.longdouble))


def test_noise_step_primal_does_not_depend_on_derivative_seeds(kernels):
    import numpy as np
    case=example();a=call(kernels,case);b=call(kernels,case,seed=False)
    for key in ('coordinates','velocity','rotation','observation'):
        assert a[key].dtype==np.dtype(np.longdouble)
        assert np.array_equal(a[key],b[key]) and np.array_equal(np.signbit(a[key]),np.signbit(b[key]))
    assert a['state_jacobian'].shape==(9,15) and a['observation_jacobian'].shape==(3,15)
    assert np.array_equal(b['state_jacobian'],np.zeros((9,15)))
    assert kernels['metadata']['internal_mantissa_bits']>53


def test_noise_step_rejects_invalid_input_before_charging_native_work(kernels):
    import numpy as np
    from lll.ilvis0_noise_step import evaluate
    for changed in (dict(dt=-.005),dict(model=3),dict(theta=np.zeros(2)),dict(rotation=np.zeros((3,3)))):
        def forbidden(**counts):raise AssertionError('invalid inputs must not execute native code')
        with pytest.raises(ValueError):evaluate(kernels['kernel'],**dict(example(),**changed),derivatives=True,reserve=forbidden)


def metric(model,c):
    import math
    phi,h=map(float,(c[0],c[2]));radius=6371000.
    if model==2:return radius,radius*(math.pi/2-phi)
    e=6.69437999014e-3;d=1-e*math.sin(phi)**2
    return 6378137.*(1-e)/d**1.5+h,(6378137./math.sqrt(d)+h)*math.cos(phi)


def reference_case(model,profile,height):
    import numpy as np
    from types import SimpleNamespace
    from lll.ilvis0_shape import PARAMETERS
    limits=np.array([.01]*3+[5.]*3+[10.]*3+[1e-6]*3+[.001]*3+[.01]*6+[2.]*3+[.01,.01,1.])
    active=tuple(PARAMETERS if profile else PARAMETERS[:-1]);point=np.linspace(-.1,.1,len(active))
    point[:3]=0.;point[6:9]=0.;point[25]=0.
    p=np.zeros(27);p[:len(point)]=point*limits[:len(point)]
    case=example(model,height=height);dt=float(case['dt'])
    theta=np.array([.2,-.3,.1])*dt;dv=np.array([.4,.2,-9.8])*dt
    initial=dict(latitude_rad=float(case['coordinates'][0]),longitude_rad=float(case['coordinates'][1]),
        height_m=float(case['coordinates'][2]),velocity_ned_mps=case['velocity'].astype(float),
        attitude_body_to_ned=case['rotation'].astype(float))
    base=SimpleNamespace(bounds=SimpleNamespace(active=active,limits=dict(zip(PARAMETERS,limits)),
        fit_earth_removal=profile,decode=lambda x:None),initial=initial,theta=theta[None,:],dv=dv[None,:],
        dt=np.array([dt]),gps_times=np.array([dt]),gps=np.zeros((1,3)),gravity=9.8,radius=6371000.)
    extended=p.astype(np.longdouble)
    case.update(theta=(theta.astype(np.longdouble)-extended[9:12]*np.longdouble(dt))/(1+extended[15:18]),
        delta_v=(dv.astype(np.longdouble)-extended[12:15]*np.longdouble(dt))/(1+extended[18:21]),
        velocity=case['velocity']+extended[3:6],gravity=np.longdouble(base.gravity)+extended[24],
        lever=extended[21:24],removal=np.longdouble((p[26]+1)/2 if profile else 0.))
    return case,base,point,limits,p


def inverse3(r):
    import numpy as np
    cross=np.column_stack([np.cross(r[1],r[2]),np.cross(r[2],r[0]),np.cross(r[0],r[1])])
    return cross/np.dot(r[0],cross[:,0])


def perturb(case,index,amount):
    import numpy as np
    result={key:value.copy() if isinstance(value,np.ndarray) else value for key,value in case.items()}
    amount=np.longdouble(amount)
    if index<3:
        axis=np.eye(3,dtype=np.longdouble)[index];x,y,z=axis
        skew=np.array([[0,-z,y],[z,0,-x],[-y,x,0]],dtype=np.longdouble)
        rotation=np.eye(3,dtype=np.longdouble)+np.sin(amount)*skew+(1-np.cos(amount))*(skew@skew)
        result['rotation']=case['rotation']@rotation
    elif index<6:result['velocity'][index-3]+=amount
    elif index<9:result['coordinates'][index-6]+=amount
    elif index<12:result['theta'][index-9]+=amount
    else:result['delta_v'][index-12]+=amount
    return result


def finite_difference(kernels,case,nominal,index,amount):
    import numpy as np
    plus=call(kernels,perturb(case,index,amount),seed=False)
    minus=call(kernels,perturb(case,index,-amount),seed=False)
    denominator=2*np.longdouble(amount)
    rotation=inverse3(nominal['rotation'])@((plus['rotation']-minus['rotation'])/denominator)
    attitude=np.array([rotation[2,1]-rotation[1,2],rotation[0,2]-rotation[2,0],rotation[1,0]-rotation[0,1]])/2
    state=np.concatenate([attitude,(plus['velocity']-minus['velocity'])/denominator,
        (plus['coordinates']-minus['coordinates'])/denominator])
    observation=(plus['observation']-minus['observation'])/denominator
    return state.astype(float),observation.astype(float)


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_noise_step_matches_wide_calibration_chain_and_all_finite_differences(kernels,model,profile,height):
    import numpy as np
    from lll.ilvis0_wide_tangent import evaluate
    names=('sphere_rotating','sphere_still','flat_still');case,base,point,limits,p=reference_case(model,profile,height)
    # The reference kernel's height mode is a fixed closure argument. Bind it
    # to the same library/function with an explicit anchor for this one call.
    from lll.ilvis0_wide_tangent import load as wide_load
    reference,_=wide_load(kernels['directory'],expected_source_sha256=hashes()['ilvis0_tangent.cpp'],
        gravity_anchor_height_m=case['anchor_height'])
    def counted(*args,**kwargs):kernels['reserve'](native_calls=1);return reference(*args,**kwargs)
    out,_,old_j,_=evaluate(base,point,names[model],kernel=counted)
    answer=call(kernels,case);unseeded=call(kernels,case,seed=False)
    assert np.array_equal(answer['observation'].astype(float),out[0])
    for key in ('coordinates','velocity','rotation','observation'):
        assert np.array_equal(answer[key],unseeded[key])
    jac=answer['observation_jacobian'];mapped=np.empty((3,21));mapped[:,:6]=jac[:,:6]*limits[:6]
    mn,me=metric(model,case['coordinates'])
    mapped[:,6:9]=jac[:,6:9]*np.array([limits[6]/mn,limits[7]/me,-limits[8]])
    for i in range(3):
        mapped[:,9+i]=jac[:,9+i]*float(-case['dt']/(1+p[15+i]))*limits[9+i]
        mapped[:,12+i]=jac[:,12+i]*float(-case['dt']/(1+p[18+i]))*limits[12+i]
        mapped[:,15+i]=jac[:,9+i]*float(-case['theta'][i]/(1+p[15+i]))*limits[15+i]
        mapped[:,18+i]=jac[:,12+i]*float(-case['delta_v'][i]/(1+p[18+i]))*limits[18+i]
    mn,me=metric(model,answer['coordinates']);coordinate_scale=np.array([mn,me,1.])
    np.testing.assert_allclose(mapped*coordinate_scale[:,None],old_j[:,:21]*coordinate_scale[:,None],rtol=2e-9,atol=1e-9)
    steps=np.array([2e-4]*3+[1e-3]*3+[2e-6,2e-6,.1]+[2e-4]*3+[1e-4]*3)
    state_scale=np.array([1.]*6+[mn,me,1.])
    for index,step in enumerate(steps):
        numeric,observed=finite_difference(kernels,case,answer,index,step)
        np.testing.assert_allclose(answer['state_jacobian'][:,index]*state_scale,numeric*state_scale,rtol=2e-6,atol=1e-7)
        np.testing.assert_allclose(jac[:,index]*coordinate_scale,observed*coordinate_scale,rtol=2e-6,atol=1e-7)
        if not profile and not height:
            again,again_observed=finite_difference(kernels,case,answer,index,step/2)
            np.testing.assert_allclose(again*state_scale,numeric*state_scale,rtol=2e-6,atol=2e-7)
            np.testing.assert_allclose(again_observed*coordinate_scale,observed*coordinate_scale,rtol=2e-6,atol=2e-7)


def test_noise_step_analytic_level_signs_and_half_increment_effect(kernels):
    import numpy as np
    case=example(model=2);dt=case['dt'];g=case['gravity']
    case.update(velocity=np.zeros(3,dtype=np.longdouble),rotation=np.eye(3,dtype=np.longdouble),
        theta=np.zeros(3,dtype=np.longdouble),delta_v=np.array([0,0,-g*dt],dtype=np.longdouble),
        lever=np.zeros(3,dtype=np.longdouble))
    a=call(kernels,case);j=a['state_jacobian'];mn,me=metric(2,case['coordinates'])
    assert j[4,0]==pytest.approx(float(g*dt),rel=1e-12)
    assert j[3,1]==pytest.approx(float(-g*dt),rel=1e-12)
    assert j[4,9]==pytest.approx(float(g*dt/2),rel=1e-12)
    assert j[3,10]==pytest.approx(float(-g*dt/2),rel=1e-12)
    assert j[6,1]*mn==pytest.approx(float(-g*dt*dt/2),rel=1e-12)
    assert j[7,0]*me==pytest.approx(float(g*dt*dt/2),rel=1e-12)
    assert j[8,14]==pytest.approx(float(-dt/2),rel=1e-12)


def test_native_build_cache_reuses_verified_binary_without_new_build(kernels):
    from lll.ilvis0_noise_step import load
    h=hashes()
    def forbidden():raise AssertionError('verified cache reuse must not rebuild')
    _,again=load(kernels['directory'],expected_source_sha256=h['ilvis0_tangent.cpp'],
        expected_bridge_sha256=h['ilvis0_noise_bridge.cpp'],expected_wide_loader_sha256=h['ilvis0_wide_tangent.py'],
        reserve_build=forbidden)
    assert again==kernels['metadata']


def test_native_build_cache_rejects_changed_binary_without_repair(kernels,tmp_path):
    from lll.native_build import cpp
    meta=kernels['metadata'];directory=kernels['directory']
    source=directory/meta['source_file'];binary=directory/meta['binary_file'];record=binary.with_suffix('.json')
    for path in (source,binary,record):(tmp_path/path.name).write_bytes(path.read_bytes())
    changed=tmp_path/binary.name;changed.write_bytes(changed.read_bytes()+b'corrupt')
    def forbidden():raise AssertionError('corrupted cache must not silently rebuild')
    with pytest.raises(ValueError,match='binary/compiler'):
        cpp(tmp_path,source.read_bytes(),prefix='noise-step',expected_sha256=meta['source_sha256'],reserve_build=forbidden)
