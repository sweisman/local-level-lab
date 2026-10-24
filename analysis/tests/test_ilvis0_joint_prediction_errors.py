# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.fixture(scope='session')
def joint_kernels(tmp_path_factory):
    import gzip,json,os,time
    from pathlib import Path
    from lll.studies.artifacts import atomic,digest,encoded
    from lll.studies.journal import Journal
    from lll.ilvis0_noise_step import load
    from lll.ilvis0_wide_tangent import load as wide_load
    directory=tmp_path_factory.mktemp('joint-prediction-errors')
    files=['analysis/lll/ilvis0_tangent.cpp','analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/lll/ilvis0_wide_tangent.py','analysis/lll/ilvis0_noise_step.py',
        'analysis/lll/ilvis0_noise_history.py','analysis/lll/receiver_noise_states.py',
        'analysis/tests/test_ilvis0_joint_prediction_errors.py','docs/native-noise-linearization/COMBINED_PLAN.md']
    sources={n:digest(Path(n).read_bytes()) for n in files}
    path=Path(os.environ.get('LLL_JOINT_ERRORS_JOURNAL',str(directory/'charges.sqlite')))
    if path.exists():raise ValueError('fresh combined-error qualification journal required')
    limits=dict(native_calls=108,packet_steps=144,builds=2)
    freeze=digest(encoded(dict(sources=sources,scope='generated combined native and receiver errors',limits=limits)))
    journal=Journal(path,freeze=freeze,limits={'qualification':limits});journal.start('qualification')
    started=time.monotonic()
    def reserve(**counts):
        if time.monotonic()-started>300:raise ValueError('cooperative combined-error allowance exhausted')
        for key,value in counts.items():journal.reserve('qualification',key,value)
    def build():reserve(builds=1)
    kernel,metadata=load(directory,expected_source_sha256=sources[files[0]],
        expected_bridge_sha256=sources[files[1]],expected_wide_loader_sha256=sources[files[2]],reserve_build=build)
    build();_,rm=wide_load(directory,expected_source_sha256=sources[files[0]])
    result=dict(kernel=kernel,directory=directory,reserve=reserve,sources=sources,results=[])
    yield result
    journal.verify()
    assert {k:journal.count('qualification',k) for k in limits}==limits
    if 'LLL_JOINT_ERRORS_JOURNAL' in os.environ:
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
            artifacts=artifacts,charged=limits,journal_freeze=freeze,results=result['results'],elapsed_s=time.monotonic()-started)))


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[False,True])
def test_native_receiver_covariance_design_and_earlier_only_prediction(joint_kernels,model,profile,height):
    import numpy as np
    from test_ilvis0_noise_history import generated_history,settings
    from lll.ilvis0_noise_history import NativeNoiseHistory,PacketNoise
    from lll.receiver_noise_states import ReceiverAugmentation
    from lll.state_space_covariance import LinearInnovations
    from lll.ilvis0_error_model import Spec,covariance
    from lll.ilvis0_wide_tangent import load,evaluate
    base,point,args=generated_history(model,profile,height,4);k=joint_kernels;n=4
    spec=Spec(white=np.eye(3)*.2,offset=np.eye(3)*.3,drift=np.eye(3)*.1,
        components=((.009,np.diag([.4,.3,.2])),(.02,np.diag([.6,.4,.5]))),
        drift_origin_s=-.002,drift_span_s=.03)
    units=np.array([1e-9,2e-9,.002])
    transforms=np.array([units[:,None]*np.array([[1.+i/20,.02,0.],[.01,1.1,0.],[0.,.02,.9-i/100]]) for i in range(n)])
    history=NativeNoiseHistory(kernel=k['kernel'],**args,noise=PacketNoise(**settings()),
        white_loadings=transforms*np.sqrt(.2),reserve=k['reserve'])
    steps=list(history.steps())
    def operator(stream,initial,dimension):
        return LinearInnovations(stream,epoch_count=n,state_dimension=dimension,observation_dimension=3,
            initial_loading=initial,maximum_bytes=100000,design_is_fixed=True,
            error_distribution='gaussian',observation_form='before_transition_shared_noise')
    native=operator(steps,history.noise.initial_loading(),15);u=native.unwhiten(np.eye(12))
    expected=u@u.T+covariance(base.gps_times,spec,transforms)
    for i,step in enumerate(steps):expected[3*i:3*i+3,3*i:3*i+3]-=step['white_loading']@step['white_loading'].T
    augmentation=ReceiverAugmentation(iter(steps),times=base.gps_times,spec=spec,transforms=transforms,
        state_dimension=15,initial_loading=history.noise.initial_loading(),maximum_epochs=4)
    combined=operator(augmentation.steps(),augmentation.initial_loading,augmentation.state_dimension)
    scale=np.tile(1/units,n);expected=expected*scale[:,None]*scale[None,:]
    u=combined.unwhiten(np.eye(12))*scale[:,None]
    np.testing.assert_allclose(u@u.T,expected,rtol=5e-12,atol=5e-12)
    reference,_=load(k['directory'],expected_source_sha256=k['sources']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=args['anchor_height'])
    def counted(*a,**kw):k['reserve'](native_calls=1,packet_steps=4);return reference(*a,**kw)
    prediction,_,jacobian,_=evaluate(base,point,('sphere_rotating','sphere_still','flat_still')[model],kernel=counted)
    np.testing.assert_array_equal(history.observations.astype(float),prediction)
    assert jacobian.shape==(12,27 if profile else 26)
    independent=np.linalg.solve(np.linalg.cholesky(expected),jacobian*scale[:,None])
    whitened=combined.whiten(jacobian)
    np.testing.assert_allclose(whitened,independent,rtol=5e-11,atol=2e-8)
    earlier=np.sin(np.arange(6)/4)/scale[:6]
    _,checkpoint=combined.apply_block(earlier,first_epoch=0)
    future=combined.conditional_marginals(state=checkpoint)
    mean=expected[6:,:6]@np.linalg.solve(expected[:6,:6],earlier*scale[:6])
    conditional=expected[6:,6:]-expected[6:,:6]@np.linalg.solve(expected[:6,:6],expected[:6,6:])
    np.testing.assert_allclose(future['mean'].ravel()*scale[6:],mean,rtol=2e-11,atol=2e-11)
    for i,block in enumerate(future['covariance']):
        s=scale[6+3*i:9+3*i]
        np.testing.assert_allclose(block*s[:,None]*s[None,:],conditional[3*i:3*i+3,3*i:3*i+3],rtol=2e-11,atol=2e-11)
    assert future['later_observations_used'] is False and future['parameter_uncertainty_included'] is False
    error=float(np.max(abs(whitened-independent))/max(1.,np.max(abs(independent))))
    k['results'].append(dict(model=model,profile=profile,height=height,packets=4,queries=4,
        native_mean_equal=True,calibration_columns=jacobian.shape[1],maximum_relative_whitening_error=error,
        conditioning_epochs=2,state_dimension=27,parameter_uncertainty_included=False))
