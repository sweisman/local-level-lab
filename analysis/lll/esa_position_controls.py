# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated receiver paths; no aircraft or model comparison."""
import math

SEED=2026102023


class Assessments:
    def __init__(self,maximum,save,check):
        if type(maximum)!=int or not 1<=maximum<=256:raise ValueError('finite assessment ceiling required')
        self.maximum=maximum;self.save=save;self.check=check;self.used=0

    def run(self,call):
        self.check()
        if self.used>=self.maximum:raise ValueError('assessment allowance exhausted')
        ordinal=self.used+1
        self.save(f'assessment-{ordinal:03d}-reservation.json',dict(assessments=ordinal,maximum=self.maximum))
        self.used=ordinal
        return call()


def metric(latitude,height):
    """Independent scalar reference, not the fitted-jet or interval routine."""
    d=1.-6.69437999014e-3*math.sin(latitude)**2
    return (6378137.*(1.-6.69437999014e-3)/d**1.5+height,
        (6378137./math.sqrt(d)+height)*math.cos(latitude))


def path(*,latitude,heading,turn,climb,nonuniform=False):
    import numpy as np
    t=np.linspace(-5.,5.,21)
    if nonuniform:t+=.005*np.sin(np.arange(21)*.71)*np.sin(np.linspace(0.,np.pi,21))
    phi=math.radians(latitude);lam=math.pi-1e-5;height=1000.;angle=math.radians(heading)
    n,e=metric(phi,height);vn=60.*math.cos(angle);ve=60.*math.sin(angle);q=math.radians(turn)
    # Differentiate the independently coded metric by centered differences.
    left=metric(phi-1e-4,height);right=metric(phi+1e-4,height)
    n_phi=(right[0]-left[0])/2e-4;e_phi=(right[1]-left[1])/2e-4
    p=vn/n;l=ve/e
    pp=(-60.*q*math.sin(angle)-(n_phi*p+climb)*p)/n
    ll=(60.*q*math.cos(angle)-(e_phi*p+math.cos(phi)*climb)*l)/e
    unwrapped=np.column_stack((phi+p*t+.5*pp*t*t,lam+l*t+.5*ll*t*t,height+climb*t))
    points=unwrapped.copy();points[:,1]=(points[:,1]+math.pi)%(2*math.pi)-math.pi
    return dict(times=t,coordinates=points,unwrapped=unwrapped,
        truth_jet=np.array([phi,lam,height,p,l,climb,pp,ll,0.]),
        true_course_rate_deg_s=float(turn),speed_mps=60.,climb_mps=float(climb))


def generated(sigma,rho,index):
    import numpy as np
    if sigma not in (.01,.05,.2) or rho not in (0.,.8,.98) or type(index)!=int or not 0<=index<256:
        raise ValueError('predeclared generated family and realization required')
    family=(.01,.05,.2).index(sigma)*3+(0.,.8,.98).index(rho)
    sample=path(latitude=(-60.,0.,60.)[index%3],heading=(0.,106.,177.,359.9)[index%4],
        turn=(0.,.06,0.,-.06)[index%4],climb=2. if index%5==0 else 0.)
    t=sample['times'];tau=None if rho==0. else -.5/math.log(rho)
    time_cov=np.eye(len(t)) if tau is None else np.exp(-abs(t[:,None]-t[None,:])/tau)
    axis_cov=sigma*sigma*np.array([[1.,.25,-.1],[.25,1.4,.15],[-.1,.15,.8]])
    seed=[SEED,family,index];rng=np.random.default_rng(np.random.SeedSequence(seed))
    errors=np.linalg.cholesky(time_cov)@rng.normal(size=(len(t),3))@np.linalg.cholesky(axis_cov).T
    observed=sample['unwrapped'].copy()
    for k,(phi,_,height) in enumerate(sample['unwrapped']):
        n,e=metric(float(phi),float(height));observed[k]+=[errors[k,0]/n,errors[k,1]/e,errors[k,2]]
    unrounded=observed.copy()
    observed[:,:2]=np.radians(np.round(np.degrees(observed[:,:2]),10));observed[:,2]=np.round(observed[:,2],3)
    observed[:,1]=(observed[:,1]+math.pi)%(2*math.pi)-math.pi
    return dict(sample,observed=observed,unrounded_observed=unrounded,seed=seed,
        covariance=np.tile(axis_cov,(len(t),1,1)),time_constant_s=tau,
        declared_coordinate_error_law='Gaussian ENU errors linearized at true coordinate metrics; rounded export')


def coverage(total,covered):
    from scipy.stats import beta
    if type(total)!=int or type(covered)!=int or not 0<=covered<=total or total<1:
        raise ValueError('finite coverage count including misses required')
    lower=float(beta.ppf(.01,covered,total-covered+1)) if covered else 0.
    return dict(covered=covered,total=total,exact_99pct_lower=lower,passed=lower>=.95)


def evaluate(task,context):
    import gzip
    import json
    import numpy as np
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_sharded_native import plain,read
    from lll.airquantumgrav_position_motion import assess
    definition=read(context.input_path());spec=task['payload'];kind=spec['kind']
    if definition['seed']!=SEED or definition['realizations_per_family']!=256:
        raise ValueError('unchanged generated qualification definition required')
    maximum=24 if kind=='analytic' else 256
    if spec['maximum_assessments']!=maximum or kind not in ('analytic','coverage'):
        raise ValueError('fixed finite qualification identity required')
    budget=Assessments(maximum,context.save,lambda:_check_continue(context.root,context.manifest))
    records=[]
    if kind=='analytic':
        for latitude in (-60.,0.,60.):
            for heading in (0.,106.,177.,359.9):
                for turn in (-.03,.03):
                    def run():
                        sample=path(latitude=latitude,heading=heading,turn=turn,
                            climb=2. if heading<170. else -2.,nonuniform=True)
                        result=assess(sample['times'],sample['coordinates'],
                            np.tile(np.eye(3)*.01,(21,1,1)),center_s=0.,degree=3,maximum_gap_s=.75,rounding_m=[0.]*3)
                        return sample,result
                    sample,result=budget.run(run)
                    error=abs(result['point_course_rate_deg_s']-turn)
                    speed_error=abs(result['point_speed_mps']-60.)
                    record=dict(latitude=latitude,heading=heading,turn=turn,course_error_deg_s=error,
                        speed_error_mps=speed_error,passed=error<=1e-8 and speed_error<=2e-7,
                        sample=sample,result=result)
                    records.append(record)
        summary=dict(passed=len(records)==24 and all(r['passed'] for r in records),
            analytic_paths=len(records),maximum_course_error_deg_s=max(r['course_error_deg_s'] for r in records),
            maximum_speed_error_mps=max(r['speed_error_mps'] for r in records))
    else:
        sigma=spec['sigma'];rho=spec['rho'];counts=dict(independent=0,arbitrary_correlation=0,supplied_correlation=0)
        unsupported=dict(counts);quiet=turning=false_flags=missed_flags=0
        for index in range(256):
            # Generation is inside the charged call: a failed realization cannot be replaced.
            def run():
                sample=generated(sigma,rho,index)
                result=assess(sample['times'],sample['observed'],sample['covariance'],center_s=0.,degree=3,
                    maximum_gap_s=.75,alpha=.01,rounding_m=[1e-5,1e-5,.0005],
                    time_constant_s=sample['time_constant_s'])
                return sample,result
            sample,result=budget.run(run);truth=sample['truth_jet'];outcomes={}
            for name,interval in result['intervals'].items():
                estimate=np.array(interval['geodetic_jet']);half=np.array(interval['geodetic_jet_half_width'])
                # Longitude representation may differ by one full revolution.
                target=truth.copy();target[1]+=round((estimate[1]-target[1])/(2*math.pi))*2*math.pi
                included=bool(np.all(abs(estimate-target)<=half)) and interval['supported']
                if not interval['supported']:unsupported[name]+=1
                if included:counts[name]+=1
                outcomes[name]=included
            is_quiet=sample['true_course_rate_deg_s']==0.;flag=abs(result['point_course_rate_deg_s'])>.02
            quiet+=is_quiet;turning+=not is_quiet
            false_flags+=is_quiet and flag;missed_flags+=(not is_quiet) and not flag
            records.append(dict(sample=sample,result=result,simultaneous_jet_containment=outcomes))
        supplied='independent' if rho==0. else 'supplied_correlation'
        gates={name:coverage(256,counts[name]) for name in (supplied,'arbitrary_correlation')}
        summary=dict(passed=all(v['passed'] for v in gates.values()),sigma=sigma,rho=rho,
            realizations=256,coverage=gates,independence_diagnostic=coverage(256,counts['independent']),
            unsupported=unsupported,quiet=quiet,turning=turning,false_point_flags=false_flags,
            missed_point_flags=missed_flags,observational_covariance_verified=False)
    # Deterministic compressed artifacts retain every input, result and failure.
    artifact=context.directory/'realizations.json.gz';artifact.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(plain(records),sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    from lll.ilvis0_receipt_journal import durable_write
    durable_write(artifact,gzip.compress(payload,mtime=0))
    context.note_file(artifact)
    return dict(identity=task['identity'],kind=kind,**summary,assessments_reserved=budget.used,
        receiver_reads=0,raw_imu_reads=0,native_evaluations=0,optimizer_starts=0,
        eligibility_policy_changed=False,observational_coverage_calibrated=False,scientific_decision='abstain')
