# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native prediction/derivative diagnostics; no fitting or automatic decisions."""
import numpy as np

from . import ilvis0_estimator as estimator, ilvis0_error_model as error
from . import ilvis0_uncertainty_geometry as geometry

VERSION='ilvis0-native-uncertainty-adapter-v1'


class SweepBudget:
    """Charge before execution. Observed callers must persist charges themselves."""
    def __init__(self,maximum_tangent_sweeps,maximum_value_sweeps,charge_callback=None):
        if (type(maximum_tangent_sweeps) is not int or maximum_tangent_sweeps<1
                or type(maximum_value_sweeps) is not int or maximum_value_sweeps<0):
            raise ValueError('explicit positive tangent/nonnegative value limits required')
        self.maximum={'tangent':maximum_tangent_sweeps,'value':maximum_value_sweeps}
        self.counts={'tangent':0,'value':0};self.journal=[];self.charge_callback=charge_callback

    def call(self,kind,function,*args):
        if kind not in self.maximum:raise ValueError('unknown native sweep kind')
        if self.counts[kind]>=self.maximum[kind]:raise estimator.EvaluationLimit('uncertainty sweep allowance exhausted')
        self.counts[kind]+=1
        row=dict(kind=kind,ordinal=self.counts[kind],status='started')
        if args and isinstance(args[0],np.ndarray):row['normalized_parameters']=args[0].tolist()
        self.journal.append(row)
        try:
            if self.charge_callback:self.charge_callback(dict(row))
            value=function(*args)
        except BaseException:
            row['status']='failed';raise
        row['status']='complete'
        return value


def physical_delta(values,reference,metric):
    x=np.asarray(values,dtype=float);r=np.asarray(reference,dtype=float);scale=np.asarray(metric,dtype=float)
    if (x.ndim!=2 or x.shape[1]!=3 or r.shape!=x.shape or scale.shape!=x.shape
            or not all(np.all(np.isfinite(a)) for a in (x,r,scale)) or np.any(scale<=0)):
        raise ValueError('finite aligned receiver coordinates and positive common metric required')
    d=x-r
    d[:,1]=(d[:,1]+np.pi)%(2*np.pi)-np.pi
    return d*scale


def layout(metric,covariance,training_epochs):
    metric=np.asarray(metric,dtype=float);c=np.asarray(covariance,dtype=float)
    if (metric.ndim!=2 or metric.shape[1]!=3 or not np.all(np.isfinite(metric)) or np.any(metric<=0)
            or type(training_epochs) is not int or not 1<training_epochs<len(metric)
            or c.shape!=(metric.size,metric.size)):
        raise ValueError('common metric, covariance and nonempty chronological split required')
    error.factor(c)
    return metric,c,3*training_epochs


def from_predictions(point,probes,metric,physical_covariance,training_epochs,parameter_names,
        center_coordinates,coordinate_jacobian,probe_coordinates):
    metric,c,cut=layout(metric,physical_covariance,training_epochs)
    point=np.asarray(point,dtype=float);probes=np.asarray(probes,dtype=float)
    names=tuple(parameter_names);center=np.asarray(center_coordinates,dtype=float)
    jac=np.asarray(coordinate_jacobian,dtype=float);supplied=np.asarray(probe_coordinates,dtype=float)
    if (point.shape!=(len(names),) or len(set(names))!=len(names) or center.shape!=metric.shape
            or jac.shape!=(metric.size,len(names)) or not np.all(np.isfinite(jac))
            or supplied.shape!=(len(probes),*metric.shape)):
        raise ValueError('native values, active parameter order and derivatives disagree')
    physical_jac=jac*metric.ravel()[:,None]
    deltas=np.array([physical_delta(values,center,metric).ravel() for values in supplied])
    diagnostic=geometry.assess(point,-np.ones(len(names)),np.ones(len(names)),
        physical_jac[:cut],c[:cut,:cut],probes,deltas[:,:cut],np.zeros(cut))
    return dict(version=VERSION,parameter_names=list(names),training_epochs=training_epochs,
        prediction_epochs=len(metric)-training_epochs,geometry=diagnostic,
        center_coordinates=center.copy(),physical_jacobian=physical_jac,
        future_probe_deltas_m=deltas[:,cut:],parameter_uncertainty_calibrated=False,
        profiles_reoptimized=False,scientific_decision='abstain')


def evaluate(problem,model,point,probes,metric,physical_covariance,training_epochs,budget):
    """One central tangent plus one value pass per noncentral supplied probe.

    Caller supplies a common physical covariance/metric and training-only fitted
    center. The function does not estimate covariance, refit, or read future errors.
    Native kernels evaluate predictions; Group1 fused navigation is not an input.
    """
    metric,_,_=layout(metric,physical_covariance,training_epochs)
    point=np.asarray(point,dtype=float);probes=np.asarray(probes,dtype=float)
    problem.bounds.decode(point)
    if probes.ndim!=2 or not len(probes) or probes.shape[1:]!=point.shape:
        raise ValueError('explicit finite probe ledger required')
    for row in probes:problem.bounds.decode(row)
    if not np.any(np.all(probes==point,axis=1)):raise ValueError('probe ledger must include fitted center')
    if metric.shape!=problem.gps.shape:raise ValueError('receiver epoch layout mismatch')
    center,jac,boundaries=budget.call('tangent',problem.prediction_tangent,point,model)
    predictions=np.array([center if np.array_equal(row,point) else budget.call('value',problem.predict,row,model)
        for row in probes])
    out=from_predictions(point,probes,metric,physical_covariance,training_epochs,
        problem.bounds.active,center,jac,predictions)
    out['gps_epochs_at_packet_boundaries']=int(boundaries)
    out['latency_boundary_warning']=bool(boundaries)
    return out
