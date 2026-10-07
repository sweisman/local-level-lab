# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-data bandwidth/covariance diagnostics, outside the decision pipeline.

Both gyro observations and the complete reconstructed prediction receive the same
additional output filter. This is not an exact nonlinear measurement likelihood.
"""
import numpy as np
from scipy.sparse import csr_matrix

import acceleration_motion as motion
from joint_acceleration_motion import integration_matrix

POLICY = dict(version='matched-output-measurement-diagnostic-1', window_seconds=30.,
    scope='Six saved recordings and their frozen free fits; no optimization or synthesis',
    prediction='Reconstructed joint motion plus within-epoch linear lift of saved science/bias minute predictions',
    filter='Identical additional centered Hann on observation and complete prediction before minute integration',
    covariance='Within-second empirical gyro mean covariance propagated assuming independent disjoint seconds',
    production_enabled=False, decisions_enabled=False)


def hann_operator(t, valid, window_seconds):
    """Explicit version of matched_filter, with zero unsupported rows."""
    t = np.asarray(t, float)
    half = max(1, int(np.ceil(window_seconds/np.median(np.diff(t))/2)))
    if window_seconds <= 0: raise ValueError('positive filter duration required')
    kernel = np.hanning(2*half+1); kernel /= kernel.sum()
    rows, columns, weights = [], [], []
    supported = np.zeros(len(t), bool)
    for run in motion.regular_runs(t, valid):
        for index in run[half:len(run)-half]:
            supported[index] = True
            rows.extend([index]*len(kernel)); columns.extend(range(index-half,index+half+1)); weights.extend(kernel)
    return csr_matrix((weights,(rows,columns)),shape=(len(t),len(t))), supported


def gyro_seconds(t, sample_t, gyro, epoch, matrices, bias):
    """Map calibrated gyro to reference frame, then disjoint one-second means.

    Covariance includes observed motion within each second; it is not a sensor
    white-noise estimate. All samples must belong to the same recovered epoch.
    """
    t, sample_t = np.asarray(t), np.asarray(sample_t)
    if np.any(np.diff(t)<1-1e-7): raise ValueError('overlapping one-second windows are unsupported')
    if np.any(np.diff(sample_t)<=0): raise ValueError('increasing IMU timestamps required')
    period = np.median(np.diff(sample_t))
    values = np.full((len(t),3),np.nan); covariance = np.zeros((len(t),3,3)); valid = np.zeros(len(t),bool)
    corrected = gyro-bias(sample_t)
    for j,(left,right) in enumerate(zip(np.searchsorted(sample_t,t-.5),np.searchsorted(sample_t,t+.5))):
        if right-left < max(2,motion.MOTION_POLICY['minimum_imu_coverage_fraction']/period): continue
        epochs = epoch[left:right]
        if np.any(epochs<0) or np.any(epochs!=epochs[0]): continue
        if np.any(np.diff(sample_t[left:right])>3*period): continue
        if sample_t[left] > t[j]-.5+1.5*period or sample_t[right-1] < t[j]+.5-1.5*period: continue
        samples = corrected[left:right]@matrices[epochs[0]].T
        if not np.isfinite(samples).all(): continue
        values[j] = samples.mean(axis=0)
        covariance[j] = np.cov(samples,rowvar=False,ddof=1)/len(samples)
        valid[j] = True
    return values,covariance,valid


def rotate_covariance(operator, sample_covariance, matrices):
    """Exact L S L^T under independent seconds, including cross-axis terms.

    Flattened output ordering is bin-major xyz in each bin's sensor frame.
    """
    n = operator.shape[0]
    reference = np.empty((n,3,n,3))
    for a in range(3):
        for b in range(3):
            reference[:,a,:,b] = (operator.multiply(sample_covariance[:,a,b])@operator.T).toarray()
    return np.einsum('iap,iajb,jbq->ipjq',matrices,reference,matrices).reshape(3*n,3*n)


def high_prediction(problem,z):
    """Independent high-rate reconstruction with explicit slow-term approximation."""
    context = problem.context
    acceleration = context.prepared['acceleration']+context.sigma_a*z[problem.error_slice][:3]
    force = context.prepared['force']+context.sigma_f*z[problem.error_slice][3:]
    C = np.full((len(context.t),3,3),np.nan)
    heading = problem.high_heading(z)
    for run in motion.regular_runs(context.t,context.valid):
        if len(run)<3: continue
        apparent = motion.unit(force[run]); forward = np.broadcast_to(motion.unit(context.forward),apparent.shape)
        angle = z[-1]
        forward = forward*np.cos(angle)+np.cross(apparent,forward)*np.sin(angle)+apparent*np.sum(apparent*forward,axis=1)[:,None]*(1-np.cos(angle))
        _,C[run],_ = motion.recover_up(force[run],acceleration[run],forward,heading[run])
    derivative,support = motion.local_derivative(context.t,C,context.valid)
    W = -derivative@np.swapaxes(C,1,2)
    rate = np.column_stack([W[:,2,1]-W[:,1,2],W[:,0,2]-W[:,2,0],W[:,1,0]-W[:,0,1]])/2
    average = context.operator@np.nan_to_num(rate)
    _,saved_rate = context.state(heading,z[-1],z[problem.error_slice])
    reconstructed = np.einsum('nji,nj->ni',context.matrices,average)
    closure = float(np.max(abs(reconstructed-saved_rate)))
    slow = problem.prediction(z).reshape(-1,3)-saved_rate
    slow_reference = np.einsum('nij,nj->ni',context.matrices,slow)
    lift = np.full_like(rate,np.nan)
    # This interpolation never crosses a mount boundary. It is a diagnostic lift,
    # not the continuous science or sensor-bias observation equation for refitting.
    for run in motion.regular_runs(context.t,support):
        bins = (context.bins['t']>=context.t[run[0]]) & (context.bins['t']<=context.t[run[-1]])
        if not bins.any(): continue
        if len(np.unique(context.bins['epoch'][bins]))!=1: raise ValueError('motion support crosses a mount boundary')
        centers = context.bins['t'][bins]
        for axis in range(3): lift[run,axis] = np.interp(context.t[run],centers,slow_reference[bins,axis])
    return rate+lift,support & np.isfinite(lift).all(axis=1),closure


def paired_bandwidth(t,gyro,prediction,valid,bins,matrices,window_seconds=30.):
    """Filter full prediction and observation identically on fixed common support."""
    valid = valid & np.isfinite(gyro).all(axis=1) & np.isfinite(prediction).all(axis=1)
    H,support = hann_operator(t,valid,window_seconds)
    A,keep = integration_matrix(t,support,bins)
    A = A[keep]; L = A@H
    rotation = matrices[keep]
    def output(operator,values):
        return np.einsum('nji,nj->ni',rotation,operator@np.nan_to_num(values))
    return dict(keep=keep,operator=L,unfiltered_gyro=output(A,gyro),unfiltered_prediction=output(A,prediction),
        matched_gyro=output(L,gyro),matched_prediction=output(L,prediction),matrices=rotation)


def covariance_summary(covariance):
    diagonal = np.diag(covariance)
    correlation = covariance/np.sqrt(np.maximum(diagonal[:,None]*diagonal[None,:],1e-300))
    off = correlation.copy(); np.fill_diagonal(off,0.)
    return dict(minimum_eigenvalue=float(np.linalg.eigvalsh(covariance).min()),
                maximum_absolute_off_diagonal_correlation=float(np.max(abs(off))),
                rms_marginal_sigma=float(np.sqrt(np.mean(diagonal))))


def residual_correlation(residual,t,matrices):
    reference = np.einsum('nij,nj->ni',matrices,residual)
    centered = reference-reference.mean(axis=0)
    covariance = centered.T@centered/max(1,len(centered)-1)
    scale = np.sqrt(np.maximum(np.diag(covariance),1e-300))
    contiguous = abs(np.diff(t)-60)<1e-5
    left,right = centered[:-1][contiguous],centered[1:][contiguous]
    lag = np.sum(left*right,axis=0)/np.sqrt(np.maximum(np.sum(left**2,axis=0)*np.sum(right**2,axis=0),1e-300))
    return dict(reference_axis_correlation=(covariance/scale[:,None]/scale[None,:]).tolist(),
        adjacent_minute_pairs=int(contiguous.sum()),adjacent_minute_axis_correlation=lag.tolist(),
        interpretation='Descriptive fitted-residual correlations; no independent-flight or significance claim')
