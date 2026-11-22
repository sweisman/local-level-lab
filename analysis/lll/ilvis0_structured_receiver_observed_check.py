# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare dense and structured receiver laws on a sealed training prefix."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

from .ilvis0_error_model import factor
from .ilvis0_gps_sensitivity import assumptions,coordinate_covariance
from .ilvis0_structured_receiver_likelihood import from_legacy_assumption
from .studies.artifacts import atomic,encoded

CASE='bb8061a43b4f14b6262ceda1-outer-0-header_elapsed-1'
PARENT='data/ilvis0-remaining-prediction-transfer-20261118'
MANIFEST='3cc9a72f3c3f3fa10c3f867fe31443fecfb7ee320dcb3567692d0af678c2863e'
OUTPUT='docs/prediction-observed-development/structured-receiver-observed-prefix.json'


def load_prefix(prior,*,epochs):
    """Read the frozen training input and predicted path, never scoring data."""
    segment=CASE.split('-')[0]
    recipe=prior.input('recipe')
    common=json.loads(gzip.decompress(prior.input(segment+'-common',raw=True)))
    training=prior.input(segment+'-outer-training')
    forecast=prior.artifact(CASE,'forecast.json')
    time=np.asarray(common['times'],float)
    receiver=np.asarray(training['training_gps'],float)
    predicted=np.asarray(forecast['coordinates'],float)
    query=np.asarray(forecast['times'],float)
    cut=training['cut_epoch']
    if (type(epochs) is not int or epochs<3 or cut<epochs or
            receiver.shape!=(cut,3) or predicted.shape!=(len(query),3) or
            len(time)<len(query) or forecast['training_epochs']!=cut or
            not np.array_equal(query,time[:len(query)]) or
            not np.all(np.isfinite(receiver)) or
            not np.all(np.isfinite(predicted))):
        raise ValueError('complete unchanged training-only receiver prefix required')
    return dict(times=query[:epochs],receiver=receiver[:epochs],
                predicted=predicted[:epochs],recipe=recipe)


def compare_prefix(times,receiver,predicted,*,independent_neu_m,
                   assumption_name):
    """Use actual coordinate residuals and a declared surrogate 26-column design."""
    t=np.asarray(times,float)
    gps=np.asarray(receiver,float)
    path=np.asarray(predicted,float)
    scale=np.asarray(independent_neu_m,float)
    if (t.ndim!=1 or len(t)<3 or gps.shape!=(len(t),3) or path.shape!=gps.shape
            or scale.shape!=(3,) or np.any(scale<=0) or
            not all(np.all(np.isfinite(x)) for x in (t,gps,path,scale)) or
            np.any(np.diff(t)<=0)):
        raise ValueError('complete finite ordered prefix and positive formal scales required')
    law=next((row for row in assumptions() if row.name==assumption_name),None)
    if law is None:raise ValueError('declared original receiver law required')
    formal=np.broadcast_to(np.diag(scale*scale),(len(t),3,3)).copy()
    delta=path-gps
    delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi
    residual=delta.ravel()
    phase=(t-t[0])/(t[-1]-t[0])
    design=np.zeros((len(t),3,26))
    for j in range(26):
        design[:,j%3,j]=(np.sin((1+j//3)*np.pi*phase)*
                         (1e-7 if j%3<2 else 1.))
    jac=design.reshape(3*len(t),26)
    structured=from_legacy_assumption(t,gps[:,0],gps[:,2],formal,law)
    actual=structured.apply(residual,jac)
    lower=factor(coordinate_covariance(t,gps[:,0],gps[:,2],formal,law))
    dense_residual=solve_triangular(lower,residual,lower=True)
    dense_jac=solve_triangular(lower,jac,lower=True)
    return dict(version='observed-prefix-receiver-algebra-v1',epochs=len(t),
        surrogate_columns=26,assumption=law.name,
        maximum_whitened_residual_difference=float(np.max(abs(
            actual['residual']-dense_residual))),
        maximum_whitened_design_difference=float(np.max(abs(
            actual['jacobian']-dense_jac))),
        quadratic_difference=float(abs(actual['quadratic']-
                                    dense_residual@dense_residual)),
        log_determinant_difference=float(abs(actual['log_determinant']-
            2*np.log(np.diag(lower)).sum())),
        receiver_positions_role='training_only',
        design_role='fixed_surrogate_not_native_calibration_jacobian',
        withheld_positions_read=False,model_fit_performed=False,
        error_law_calibrated=False,scientific_decision='abstain')


def publish(root,*,output=OUTPUT):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    target=root/output
    if target.exists():raise ValueError('fresh output path required')
    parent=ClosedStudy(root,PARENT)
    try:
        if parent.completion['manifest_sha256']!=MANIFEST:
            raise ValueError('unchanged sealed parent required')
        prefix=load_prefix(parent,epochs=120)
        report=compare_prefix(prefix['times'],prefix['receiver'],
            prefix['predicted'],
            independent_neu_m=prefix['recipe']['independent_neu_m'],
            assumption_name=prefix['recipe']['training_weight'])
    finally:parent.close()
    report.update(parent_manifest_sha256=MANIFEST,case=CASE,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        adapter_sha256=hashlib.sha256((root/'analysis/lll/'
            'ilvis0_structured_receiver_likelihood.py').read_bytes()).hexdigest())
    if (report['maximum_whitened_residual_difference']>1e-6 or
            report['maximum_whitened_design_difference']>1e-6 or
            report['quadratic_difference']>1e-6):
        raise ValueError('dense/structured observed-prefix equivalence failed')
    atomic(target,encoded(report))
    return report


if __name__=='__main__':
    result=publish(Path('.'))
    print(json.dumps({k:result[k] for k in ('epochs','assumption',
        'maximum_whitened_residual_difference',
        'maximum_whitened_design_difference')},sort_keys=True))
