# SPDX-License-Identifier: AGPL-3.0-or-later
"""Experimental yaw ambiguity; magnetometer flags locate boundaries, not yaw values."""
import numpy as np

MOUNT_YAW_POLICY = dict(version='mount-yaw-1',angle_sigma_deg=3.,rate_sigma_dph=3.,
    angle_bound_deg=15.,rate_bound_dph=15.,boundary_fraction=.01,
    flag_source='magnetic-watchdog-2',
    basis='step and finite-duration linear yaw within each flagged segment and mount epoch',
    agreement='both scientific paths eligible, identical endpoint decisions and shifts <= 1 sigma',
    provenance='Provisional research assumptions; no independent measurement of mount yaw')


def boundary_keep(bins,segments):
    """Remove first flagged bin per epoch: an instantaneous step has unmodeled gyro impulse."""
    keep=np.ones(len(bins['t']),bool)
    for s in segments:
        for e in np.unique(bins['epoch'][bins['seg']==s]):
            indices=np.flatnonzero((bins['seg']==s)&(bins['epoch']==e))
            if len(indices): keep[indices[0]]=False
    return keep


class MountYaw:
    """Positive yaw rotates the IMU about measured up; q alternates radians and rad/s."""
    def __init__(self,bins,segments):
        t=np.asarray(bins['t'],float); seg=np.asarray(bins['seg']); epoch=np.asarray(bins['epoch'])
        if not np.isfinite(t).all() or np.any(np.diff(t)<=0):
            raise ValueError('mount yaw requires increasing finite bin times')
        if any(not isinstance(s,(int,np.integer)) for s in segments) or len(set(segments))!=len(segments):
            raise ValueError('mount yaw requires unique integer segment IDs')
        if not set(segments)<=set(seg): raise ValueError('mount yaw segment unavailable')
        self.groups=[]; angles=[]; rates=[]
        dt=np.broadcast_to(np.asarray(bins['dt'],float),t.shape)
        if not np.isfinite(dt).all() or np.any(dt<=0): raise ValueError('invalid mount yaw bin duration')
        for s in sorted(segments):
            for e in np.unique(epoch[seg==s]):
                select=(seg==s)&(epoch==e); indices=np.flatnonzero(select)
                if len(indices)<2: raise ValueError('mount yaw interval needs at least two bins')
                start=t[indices[0]]-dt[indices[0]]/2.; end=t[indices[-1]]+dt[indices[-1]]/2.
                inside=(epoch==e)&(t>=start); ramp=inside& (t<=end)
                angles.extend([inside.astype(float),np.where(inside,np.clip(t-start,0.,end-start),0.)])
                rates.extend([np.zeros(len(t)),ramp.astype(float)])
                self.groups.append(dict(seg=int(s),epoch=int(e),start_s=float(start),end_s=float(end)))
        self.B=np.column_stack(angles) if angles else np.zeros((len(t),0))
        self.D=np.column_stack(rates) if rates else np.zeros((len(t),0))
        self.npar=self.B.shape[1]

    def penalty(self,widen=1.):
        if not np.isfinite(widen) or widen<=0: raise ValueError('positive mount yaw prior widening required')
        sd=np.tile(np.radians([MOUNT_YAW_POLICY['angle_sigma_deg'],MOUNT_YAW_POLICY['rate_sigma_dph']/3600.]),len(self.groups))
        return np.diag(1/(sd*widen))

    def bounds(self):
        hi=np.tile(np.radians([MOUNT_YAW_POLICY['angle_bound_deg'],MOUNT_YAW_POLICY['rate_bound_dph']/3600.]),len(self.groups))
        return -hi,hi

    def near_boundary(self,q):
        if not self.npar: return False
        lo,hi=self.bounds()
        return bool(np.min(np.minimum(q-lo,hi-q)/(hi-lo))<=MOUNT_YAW_POLICY['boundary_fraction'])

    def states(self):
        states=[('nominal',np.zeros(self.npar))]
        for i in range(self.npar):
            sigma=np.radians(MOUNT_YAW_POLICY['angle_sigma_deg'] if i%2==0 else MOUNT_YAW_POLICY['rate_sigma_dph']/3600.)
            for sign in (-1,1):
                q=np.zeros(self.npar); q[i]=sign*3*sigma
                states.append((f'mount-{i}-{sign}',q))
        return states

    def report(self,q):
        return dict(policy=MOUNT_YAW_POLICY,groups=self.groups,
            per_bin_yaw_deg=np.degrees(self.B@q).tolist(),
            per_bin_yaw_rate_dph=(np.degrees(self.D@q)*3600.).tolist(),
            near_boundary=self.near_boundary(q),
            limitations='Within-segment affine yaw; instantaneous boundary motion and nonlinear creep are not reconstructed')


def compare_paths(retained,excluded,flags=(),excluded_flags=()):
    """Development agreement veto; each fit retains its own eligibility gates."""
    from .policy import _scientific_path_exclusions,MODEL_PAIRS
    from . import models
    derived={'inference_nonconvergence','prior_dominated','crab_sensitive','single_heading','k_not_identified','k_rot_not_identified','k_disc_not_identified'}
    def path_flags(f,source):
        values=set(source)-derived
        if not f.get('convergence',{}).get('converged'): values.add('inference_nonconvergence')
        if f.get('prior_sensitivity',{}).get('prior_dominated'): values.add('prior_dominated')
        if (f.get('crab_sensitivity') or {}).get('course_groups')==1: values.add('single_heading')
        return sorted(values)
    def ready(f,pair=None):
        source=flags if f is retained else excluded_flags
        return _scientific_path_exclusions({'fit':f,'flags':path_flags(f,source)},pair) if f else ['exclusion path unavailable']
    report=dict(version='magnetic-two-path-1',primary_agree=False,pairwise={},
                retained_exclusions=ready(retained),excluded_exclusions=ready(excluded))
    if not excluded:
        report['pairwise']={name:dict(agree=False,reasons=['exclusion path unavailable']) for name in MODEL_PAIRS}
        return report
    def difference(a,b,sa,sb):
        try:
            values=np.asarray([a,b,sa,sb],float)
            if not np.isfinite(values).all() or min(sa,sb)<=0: return float('inf')
            return float((a-b)/max(sa,sb))
        except (ValueError,TypeError): return float('inf')
    shifts={n:difference(retained['k'][n],excluded['k'][n],retained['k_sd'][n],excluded['k_sd'][n]) for n in retained['k']}
    decisions=[f.get('rejected') for f in (retained,excluded)]
    report.update(k_shift_sigma=shifts,primary_agree=bool(not report['retained_exclusions'] and
        not report['excluded_exclusions'] and isinstance(decisions[0],dict) and set(decisions[0])==set(models.MODELS) and decisions[0]==decisions[1] and
        all(isinstance(v,(bool,np.bool_)) for v in decisions[0].values()) and
        all(np.isfinite(v) and abs(v)<=1 for v in shifts.values())))
    # Build evidence using the path gate, without bypassing public decision eligibility.
    for name in MODEL_PAIRS:
        a=(retained.get('pairwise_profile') or {}).get(name); b=(excluded.get('pairwise_profile') or {}).get(name)
        reasons=ready(retained,name)+ready(excluded,name)
        if not a or not b:
            reasons.append('pair profile unavailable'); shift=None; same=False
        else:
            def endpoint_decisions(entry):
                values=entry.get('p_diagnostic') or {}
                if set(values)!=set(MODEL_PAIRS[name]) or any(not isinstance(p,(float,int)) or not np.isfinite(p) or not 0<=p<=1 for p in values.values()): return None
                return {m:p<.0027/(2*len(MODEL_PAIRS)) for m,p in values.items()}
            shift=difference(a['estimate'],b['estimate'],a['sd'],b['sd'])
            left,right=endpoint_decisions(a),endpoint_decisions(b)
            same=left is not None and left==right
            if not same: reasons.append('pair endpoint decisions disagree')
            if not np.isfinite(shift) or abs(shift)>1: reasons.append('pair estimates disagree')
        report['pairwise'][name]=dict(agree=bool(not reasons and same),reasons=list(dict.fromkeys(reasons)),shift_sigma=shift)
    return report
