# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research continuous-at-GPS-times equation and shared-input linear propagation.

No likelihood weights, fits, eligibility or decisions are changed. Covariance is
conditional on recovered mounting/forward references and independent input seconds.
"""
import numpy as np
from scipy.sparse import csr_matrix, diags, vstack

import acceleration_motion as motion
import joint_acceleration_motion as joint
import matched_measurement_motion as matched
from lll import models

POLICY = dict(version='continuous-measurement-propagation-development-1',
    input_channels=['velocity_n','velocity_e','height','latitude_rad','longitude_rad',
                    'force_x','force_y','force_z','gyro_x','gyro_y','gyro_z'],
    input_window_seconds=30., output_window_seconds=30.,
    support='Fixed observed joint support and common output filter; perturbations never select rows',
    covariance='Independent seconds; GPS speed/bearing covariance, independent position marginals and time-matched force/gyro empirical covariance',
    imu_pair_tolerance_sample_fraction=.1,
    fit_response='Local Gauss-Newton response at saved parameters, old weights and deterministic penalties; not a refit or posterior coverage',
    production_enabled=False,decisions_enabled=False)


def derivative_operator(t,valid):
    rows,cols,values=[],[],[]
    for run in motion.regular_runs(t,valid):
        if len(run)<3:continue
        for i in run[1:-1]:
            before,after=t[i]-t[i-1],t[i+1]-t[i]
            rows.extend([i]*3);cols.extend([i-1,i,i+1])
            values.extend([-after/(before*(before+after)),(after-before)/(before*after),before/(after*(before+after))])
    return csr_matrix((values,(rows,cols)),shape=(len(t),len(t)))


def vee(W):
    return np.column_stack([W[:,2,1]-W[:,1,2],W[:,0,2]-W[:,2,0],W[:,1,0]-W[:,0,1]])/2


def paired_imu_covariance(t, sample_t, force, gyro, epoch, matrices, bias,force_t=None,force_epoch=None):
    """Time-matched empirical covariance for two disjoint-window sample means.

    Nearest matches must be unique, in the same second and epoch, and within 10%
    of one sample period. Cross covariance is scaled by m/(n_force*n_gyro);
    marginal covariance by 1/n_stream, accounting for unmatched sample means.
    """
    force_t=sample_t if force_t is None else force_t
    force_epoch=epoch if force_epoch is None else force_epoch
    if np.any(np.diff(t)<1-1e-7):raise ValueError('overlapping seconds unsupported')
    if np.any(np.diff(sample_t)<=0) or np.any(np.diff(force_t)<=0):raise ValueError('increasing IMU timestamps required')
    covariance=np.zeros((len(t),6,6));valid=np.zeros(len(t),bool)
    period=np.median(np.diff(sample_t));corrected=gyro-bias(sample_t)
    period=min(period,np.median(np.diff(force_t)))
    for i,(a,b) in enumerate(zip(np.searchsorted(sample_t,t-.5),np.searchsorted(sample_t,t+.5))):
        if b-a<max(2,.8/period):continue
        fa,fb=np.searchsorted(force_t,[t[i]-.5,t[i]+.5])
        if fb-fa<max(2,.8/period):continue
        e=epoch[a:b]
        if np.any(e<0) or np.any(e!=e[0]) or np.any(np.diff(sample_t[a:b])>3*period):continue
        if np.any(force_epoch[fa:fb]!=e[0]) or np.any(np.diff(force_t[fa:fb])>3*period):continue
        if sample_t[a]>t[i]-.5+1.5*period or sample_t[b-1]<t[i]+.5-1.5*period:continue
        if force_t[fa]>t[i]-.5+1.5*period or force_t[fb-1]<t[i]+.5-1.5*period:continue
        right=np.clip(np.searchsorted(force_t,sample_t[a:b]),fa,fb-1)
        left=np.maximum(right-1,fa)
        paired=np.where(abs(force_t[left]-sample_t[a:b])<=abs(force_t[right]-sample_t[a:b]),left,right)
        keep=abs(force_t[paired]-sample_t[a:b])<=POLICY['imu_pair_tolerance_sample_fraction']*period
        # Reject repeated nearest neighbors; neither sensor sample is counted twice.
        ids,counts=np.unique(paired[keep],return_counts=True)
        keep &= np.isin(paired,ids[counts==1])
        if keep.sum()<max(2,.8*min(b-a,fb-fa)):continue
        R=matrices[e[0]]
        values=np.column_stack([force[paired[keep]]@R.T,corrected[a:b][keep]@R.T])
        if not np.isfinite(values).all():continue
        sample=np.cov(values,rowvar=False,ddof=1);ng,nf,m=b-a,fb-fa,int(keep.sum())
        covariance[i,:3,:3]=sample[:3,:3]/nf;covariance[i,3:,3:]=sample[3:,3:]/ng
        covariance[i,:3,3:]=sample[:3,3:]*m/(nf*ng);covariance[i,3:,:3]=covariance[i,:3,3:].T
        valid[i]=True
    return covariance,valid


def input_covariance(inputs,imu_covariance):
    """GPS covariance uses published accuracy fields as provisional one-sigma scales."""
    gn=inputs['gnss'];psi=np.radians(gn['bearing_deg'])
    along=gn['speed_acc_mps']**2;lateral=(gn['speed_mps']*np.radians(gn['bearing_acc_deg']))**2
    S=np.zeros((len(psi),11,11));c,s=np.cos(psi),np.sin(psi)
    S[:,0,0]=along*c*c+lateral*s*s;S[:,1,1]=along*s*s+lateral*c*c
    S[:,0,1]=S[:,1,0]=(along-lateral)*c*s
    lat=np.radians(gn['lat']);rm,rn=models.radii(lat)
    S[:,2,2]=gn['v_acc_m']**2
    # Equal independent horizontal component scales are an assumption, not a
    # conversion of receiver radial accuracy into a verified covariance ellipse.
    S[:,3,3]=(gn['h_acc_m']/(rm+gn['alt_m']))**2
    S[:,4,4]=(gn['h_acc_m']/((rn+gn['alt_m'])*np.maximum(np.cos(lat),models.MIN_COS_LAT)))**2
    S[:,5:,5:]=imu_covariance
    if not np.isfinite(S).all():raise ValueError('finite accuracy fields required')
    return S


class ContinuousEquation:
    """Complete sampled science/drift/motion prediction; no minute-value interpolation."""
    def __init__(self,problem,inputs,gyro,gyro_valid):
        self.problem=problem;self.context=problem.context;self.t=inputs['t'];gn=inputs['gnss']
        psi=np.radians(gn['bearing_deg'])
        self.x=np.column_stack([gn['speed_mps']*np.cos(psi),gn['speed_mps']*np.sin(psi),
            gn['alt_m'],np.radians(gn['lat']),np.unwrap(np.radians(gn['lon'])),inputs['force'],gyro])
        input_valid=inputs['valid'] & gyro_valid & np.isfinite(self.x).all(axis=1)
        self.H,h_support=matched.hann_operator(self.t,input_valid,30.)
        # Recovered joint support is frozen: zero-error perturbations cannot acquire
        # rows and nonlinear out-of-envelope trials raise instead of dropping bins.
        self.valid=problem.context.valid & h_support
        _,rate_support=motion.local_derivative(self.t,np.zeros((len(self.t),3)),self.valid)
        self.D=derivative_operator(self.t,h_support)
        self.frame_D=derivative_operator(self.t,self.valid)
        self.Hout,out_support=matched.hann_operator(self.t,rate_support,30.)
        A,keep=joint.integration_matrix(self.t,out_support,self.context.bins)
        if not keep.any():raise ValueError('no complete common support')
        self.keep=keep;self.L=A[keep]@self.Hout
        self.bins=joint.subset_bins(self.context.bins,keep);self.matrices=self.context.matrices[keep]
        self.raw_transforms=[self.H]*8+[self.D@self.H,self.D@self.H,-self.D@self.D@self.H]
        # Local coordinates are [vN,vE,h,lat,longitude_rate,fX,fY,fZ,aN,aE,aD].
        self.raw_transforms[4]=self.D@self.H
        self.raw_channels=[0,1,2,3,4,5,6,7,0,1,2]
        self.runs=[r for r in motion.regular_runs(self.t,self.valid) if len(r)>=3]
        self.epoch=np.full(len(self.t),-1,int);self.gravity=np.full(len(self.t),-1,int)
        for run in self.runs:
            bins=(self.context.bins['t']>=self.t[run[0]]) & (self.context.bins['t']<=self.t[run[-1]])
            if not bins.any():continue
            es=np.unique(self.context.bins['epoch'][bins]);gs=np.unique(self.context.bins['grav'][bins])
            if len(es)!=1 or len(gs)!=1:raise ValueError('support spans mounting/gravity groups')
            self.epoch[run]=es[0];self.gravity[run]=gs[0]
        needed=np.unique(self.L.indices)
        if np.any(self.epoch[needed]<0):raise ValueError('no observed mount assignment for required samples')
        self.bias_B=None if problem.bias_knots is None else joint.interpolate_basis(self.t,problem.bias_knots)[0][:,1:]

    def local_inputs(self,x):
        x=np.nan_to_num(x)
        return np.column_stack([self.H@x[:,:4],self.D@self.H@x[:,4],self.H@x[:,5:8],
            self.D@self.H@x[:,:2],-self.D@self.D@self.H@x[:,2]])

    def local_prediction(self,local,z):
        p=self.problem;v=local[:,:2];q=z[p.p:p.p+p.nc]
        psi=np.arctan2(v[:,1],v[:,0])
        if p.wind_tas is None:
            coeff=p.high_B@q.reshape(-1,2)
            heading=psi+coeff[:,0]*np.sin(psi)+coeff[:,1]*np.cos(psi)
        else:
            air=v-p.high_B@q.reshape(-1,3)[:,:2]
            heading=np.arctan2(air[:,1],air[:,0])
        acceleration=local[:,8:11]+np.nan_to_num(self.context.sigma_a)*z[p.error_slice][:3]
        force=local[:,5:8]+np.nan_to_num(self.context.sigma_f)*z[p.error_slice][3:]
        C=np.zeros((len(self.t),3,3))
        for run in self.runs:
            apparent=motion.unit(force[run]);forward=np.broadcast_to(motion.unit(self.context.forward),apparent.shape);angle=z[-1]
            forward=forward*np.cos(angle)+np.cross(apparent,forward)*np.sin(angle)+apparent*np.sum(apparent*forward,axis=1)[:,None]*(1-np.cos(angle))
            _,C[run],_=motion.recover_up(force[run],acceleration[run],forward,heading[run])
        terms=np.stack(models.terms(local[:,3],local[:,2],local[:,0],local[:,1],local[:,4]),axis=-1)
        science=np.einsum('nij,njk,k->ni',C,terms,z[:3])
        return C,science

    def reference_prediction(self,z,x=None):
        local=self.local_inputs(self.x if x is None else x);C,science=self.local_prediction(local,z)
        dC=(self.frame_D@C.reshape(len(self.t),9)).reshape(-1,3,3)
        rate=vee(-dC@C.transpose(0,2,1))
        p=self.problem
        if p.temp_ref is not None or p.base_p!=3+3*p.layout['n_grav']:raise ValueError('unsupported temperature/bias layout')
        offset=z[3:p.base_p].reshape(-1,3)
        bias=np.zeros((len(self.t),3));active=self.epoch>=0
        sensor=offset[np.maximum(self.gravity,0)]
        if self.bias_B is not None:sensor=sensor+self.bias_B@z[p.bias_drift_slice].reshape(-1,3)
        bias[active]=np.einsum('nij,nj->ni',self.context.bins['mount_matrices'][self.epoch[active]],sensor[active])
        return rate+science+bias

    def output(self,reference):
        return np.einsum('nji,nj->ni',self.matrices,self.L@np.nan_to_num(reference)).ravel()

    def residual(self,z,x=None):
        x=self.x if x is None else x
        return self.output(x[:,8:11]-self.reference_prediction(z,x))

    def auxiliary(self,z,x=None,jac=False):
        p=self.problem;n=len(self.bins['t'])
        if p.wind_tas is None:
            return (np.zeros(0),np.zeros((0,p.npar))) if jac else np.zeros(0)
        B,_=joint.interpolate_basis(self.bins['t'],p.knots)
        ground=self.L@self.H@np.nan_to_num((self.x if x is None else x)[:,:2])
        q=z[p.p:p.p+p.nc].reshape(-1,3);air=ground-B@q[:,:2];norm=np.linalg.norm(air,axis=1)
        tas=p.wind_tas.policy['tas_reference_mps']*np.exp(B@q[:,2]);sigma=p.wind_tas.policy['ground_constraint_sigma_mps']
        value=(norm-tas)/sigma
        if not jac:return value
        J=np.zeros((n,p.npar));small=np.zeros((n,len(p.knots),3))
        small[:,:,0]=-air[:,0,None]*B/(norm[:,None]*sigma)
        small[:,:,1]=-air[:,1,None]*B/(norm[:,None]*sigma)
        small[:,:,2]=-tas[:,None]*B/sigma
        J[:,p.p:p.p+p.nc]=small.reshape(n,-1)
        return value,J

    def parameter_jacobian(self,z):
        lo,hi=self.problem.bounds();J=np.zeros((3*len(self.bins['t']),len(z)))
        for j in range(len(z)):
            step=2e-3 if j in range(self.problem.error_slice.start,self.problem.error_slice.stop) else 2e-3 if self.problem.wind_tas is not None and self.problem.p<=j<self.problem.p+self.problem.nc else 2e-6
            a,b=z.copy(),z.copy();a[j]=min(z[j]+step,hi[j]);b[j]=max(z[j]-step,lo[j])
            # Prediction rather than residual Jacobian.
            J[:,j]=-(self.residual(a)-self.residual(b))/(a[j]-b[j])
        return J

    def input_jacobians(self,z):
        """Point-local finite derivatives chained through exact sparse filters/gradients."""
        local=self.local_inputs(self.x);C,science=self.local_prediction(local,z)
        dC=(self.frame_D@C.reshape(len(self.t),9)).reshape(-1,3,3)
        # d omega = vee(-d(delta C) C^T - dC delta C^T).
        direct=np.zeros((len(self.t),3,9));gradient=direct.copy()
        for k in range(9):
            basis=np.zeros_like(C);basis[:,k//3,k%3]=1.
            direct[:,:,k]=vee(-dC@basis.transpose(0,2,1))
            gradient[:,:,k]=vee(-basis@C.transpose(0,2,1))
        pieces=[csr_matrix((3*len(self.bins['t']),len(self.t))) for _ in range(11)]
        steps=[.002,.002,.02,2e-7,2e-8,2e-5,2e-5,2e-5,2e-5,2e-5,2e-5]
        def rotate(axis_blocks):
            # Matrix block ordering before row interleaving is reference-axis major.
            rows=[]
            for sensor_axis in range(3):
                block=sum(diags(self.matrices[:,ref,sensor_axis])@axis_blocks[ref] for ref in range(3))
                rows.append(block)
            grouped=vstack(rows,format='csr')
            order=np.arange(grouped.shape[0]).reshape(3,-1).T.ravel()
            return grouped[order]
        for j,step in enumerate(steps):
            a,b=local.copy(),local.copy();a[:,j]+=step;b[:,j]-=step
            Ca,sa=self.local_prediction(a,z);Cb,sb=self.local_prediction(b,z)
            dc=((Ca-Cb)/(2*step)).reshape(len(self.t),9);ds=(sa-sb)/(2*step)
            blocks=[]
            for axis in range(3):
                block=self.L@diags(np.sum(direct[:,axis,:]*dc,axis=1)+ds[:,axis])
                for k in range(9):
                    block=block+self.L@diags(gradient[:,axis,k])@self.frame_D@diags(dc[:,k])
                blocks.append(block@self.raw_transforms[j])
            channel=self.raw_channels[j];pieces[channel]=pieces[channel]-rotate(blocks)
        for axis in range(3):
            blocks=[self.L if k==axis else self.L*0 for k in range(3)]
            pieces[8+axis]=rotate(blocks)
        auxiliary=[]
        if self.problem.wind_tas is not None:
            p=self.problem;B,_=joint.interpolate_basis(self.bins['t'],p.knots)
            ground=self.L@self.H@np.nan_to_num(self.x[:,:2]);air=ground-B@z[p.p:p.p+p.nc].reshape(-1,3)[:,:2]
            unit=air/np.linalg.norm(air,axis=1)[:,None]/p.wind_tas.policy['ground_constraint_sigma_mps']
            for j in range(11):auxiliary.append(diags(unit[:,j])@self.L@self.H if j<2 else csr_matrix((len(air),len(self.t))))
        else:auxiliary=[csr_matrix((0,len(self.t))) for _ in range(11)]
        return [vstack([b,e],format='csr') for b,e in zip(pieces,auxiliary)]


def propagate(jacobians,S):
    """Shared channels/seconds stay in one covariance block, without double counting."""
    n=jacobians[0].shape[0];covariance=np.zeros((n,n))
    for i,A in enumerate(jacobians):
        for j,B in enumerate(jacobians):
            if np.any(S[:,i,j]):covariance+=(A.multiply(S[:,i,j])@B.T).toarray()
    return (covariance+covariance.T)/2


def fit_response(J,weights,P,auxiliary_J):
    """Linear estimator response with correlated gyro/auxiliary input noise.

    Penalties are deterministic regularizers. This propagates sampling error only,
    not a Bayesian posterior or uncertainty in prior centers/scales.
    """
    A=np.vstack([J*np.sqrt(weights)[:,None],auxiliary_J,P])
    scale=np.maximum(np.linalg.norm(A,axis=0),1e-30)
    inverse=np.linalg.pinv(A/scale,rcond=1e-10)/scale[:,None]
    normal_inverse=inverse@inverse.T
    K=normal_inverse@(J.T*weights)
    auxiliary_response=-normal_inverse@auxiliary_J.T
    parameter=np.column_stack([K,auxiliary_response])
    residual=np.column_stack([np.eye(len(J))-J@K,-J@auxiliary_response])
    return parameter,residual
