# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated means and joint Gaussian errors; no flight simulator."""
import numpy as np

from lll.ilvis0_error_model import Spec,covariance,factor
from lll.ilvis0_structured_covariance import Innovations
from lll.ilvis0_structured_prediction import Forecast

CASES=('fixed_linear','boundary_linear','unidentified_27','bounded_nonlinear','adaptive_design','finite_covariance_union')
SEED=2026101907


def specification(times,alternative=0):
    a=np.array([[1.,.2,.1],[.2,1.3,-.15],[.1,-.15,1.8]])
    b=np.array([[.7,-.1,.05],[-.1,1.,.1],[.05,.1,.9]])
    taus=(2.,30.) if alternative==0 else (10.,300.)
    return Spec(white=.2*a,components=((taus[0],a),(taus[1],.4*b)),offset=.2*b,drift=.1*a,
        drift_origin_s=0.,drift_span_s=float(times[-1]+1.))


def fixture(name):
    if name not in CASES:raise ValueError('predeclared software control required')
    index=CASES.index(name);p=27 if name=='unidentified_27' else 1 if name=='adaptive_design' else 4
    nt,nc,nf=(16,20,6) if p==27 else (12,12,4)
    times=np.arange(max(nc,nt+nf),dtype=float)+.07*np.sin(np.arange(max(nc,nt+nf)))
    rng=np.random.default_rng(np.random.SeedSequence([SEED,index,0]))
    xt=rng.normal(size=(3*nt,p));xp=rng.normal(size=(3*nf,p))
    if p==27:
        xt[:,-3:]=0.;xt[:,-4]=xt[:,0];xt[:,-5]*=1e-12
    if p==1:xp[:]=1.
    theta=np.resize(np.array([.2,-.3,.1,.25]),p)
    if name in ('boundary_linear','unidentified_27'):theta=np.resize([1.,-1.],p)
    if name=='bounded_nonlinear':theta=np.array([1.,-1.,.8,-.7])
    if p==1:theta[:]=0.
    bounds=np.tile([-1.,1.],(p,1)) if p!=1 else np.array([[0.,10.]])
    xcal=np.kron(np.ones((nc,1)),np.eye(3));family={}
    for alternative in range(2 if name=='finite_covariance_union' else 1):
        key='common' if name!='finite_covariance_union' else ('a','b')[alternative]
        spec=specification(times,alternative)
        op=Innovations(times[:nt],spec);cal=Innovations(times[:nc],spec)
        forecast=Forecast(op,times[nt:nt+nf])
        family[key]=dict(operator=op,calibration=cal,forecast=forecast,
            science_root=factor(covariance(times[:nt+nf],spec)),calibration_root=factor(covariance(times[:nc],spec)),
            whitened_design=op.whiten(xt),conditional_design=forecast.mean(xt),calibration_design=cal.whiten(xcal))
    bt=.1 if name=='bounded_nonlinear' else 0.;bc=.03 if bt else 0.
    vt=np.sin(np.arange(3*nt)*.19+.3);vc=np.cos(np.arange(3*nc)*.13+.1)
    vt=vt*bt/max(np.linalg.norm(v['operator'].whiten(vt)) for v in family.values())
    vc=vc*bc/max(np.linalg.norm(v['calibration'].whiten(vc)) for v in family.values())
    future_error=np.full(3*nf,.02 if bt else 0.)
    return dict(name=name,index=index,nt=nt,nc=nc,nf=nf,parameters=p,training_design=xt,future_design=xp,
        theta=theta,bounds=bounds,calibration_design=xcal,calibration_theta=np.array([.4,-.2,.1]),
        training_remainder_shape=vt,calibration_remainder=vc,training_remainder_radius=bt,
        calibration_remainder_radius=bc,future_remainder_bounds=future_error,family=family,scale=.7,
        prediction_ids=tuple(f'epoch-{i//3}-axis-{i%3}' for i in range(3*nf)))


def realization(control,replicate):
    keys=list(control['family']);truth_id=keys[replicate%len(keys)];truth=control['family'][truth_id]
    cal_rng=np.random.default_rng(np.random.SeedSequence([SEED,control['index'],replicate,1]))
    joint_rng=np.random.default_rng(np.random.SeedSequence([SEED,control['index'],replicate,2]))
    calibration=(control['calibration_design']@control['calibration_theta']+control['calibration_remainder']
        +control['scale']*(truth['calibration_root']@cal_rng.normal(size=3*control['nc'])))
    joint=control['scale']*(truth['science_root']@joint_rng.normal(size=3*(control['nt']+control['nf'])))
    xt=control['training_design'];theta=control['theta'];cut=3*control['nt']
    if control['name']=='adaptive_design':
        xt=joint[:cut,None]/np.linalg.norm(truth['operator'].whiten(joint[:cut]))
    nonlinear=float(np.mean(theta**2))
    training=xt@theta+nonlinear*control['training_remainder_shape']+joint[:cut]
    future=(control['future_design']@theta+theta[0]**2*control['future_remainder_bounds']
        *np.cos(np.arange(3*control['nf']))+joint[cut:])
    return dict(calibration=calibration,training=training,future=future,training_design=xt,
        covariance_truth=truth_id,replicate=replicate)


def envelope(control,*,calibration,training,training_design):
    """Prediction path accepts no future observations or generating covariance ID."""
    from lll.ilvis0_bounded_prediction import known_scale,shared_scale_bound,Region,predict,union
    alternatives={}
    for key,member in control['family'].items():
        if control['name'] in ('fixed_linear','adaptive_design'):
            scale=known_scale(control['scale'],source_id='independent-software-calibration',covariance_id=key)
        else:
            scale=shared_scale_bound(member['calibration'].whiten(calibration),member['calibration_design'],
                alpha=.01,source_id='independent-software-calibration',covariance_id=key,
                remainder_radius=control['calibration_remainder_radius'],design_is_fixed=True)
        operator=member['operator'];forecast=member['forecast']
        region=Region(operator.whiten(training),operator.whiten(training_design),control['bounds'],
            scale=scale,covariance_id=key,remainder_radius=control['training_remainder_radius'],
            alpha=.02,design_is_fixed=control['name']!='adaptive_design')
        alternatives[key]=predict(region,forecast.mean(training),
            control['future_design']-forecast.mean(training_design),conditional_variance=forecast.variance,
            training_response_norm=forecast.training_response_norm,
            future_remainder_bounds=control['future_remainder_bounds'],alpha=.02,
            prediction_ids=control['prediction_ids'])
    return union(alternatives)
