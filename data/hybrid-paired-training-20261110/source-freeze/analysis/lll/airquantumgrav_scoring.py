# SPDX-License-Identifier: AGPL-3.0-or-later
"""Common descriptive receiver-coordinate errors, separate from model fitting."""
import math


def receiver_errors(prediction,receiver):
    import numpy as np
    from lll.models import radii
    p,g=(np.asarray(v,float) for v in (prediction,receiver))
    if (g.ndim!=2 or not len(g) or g.shape[1:]!=(3,) or p.shape!=g.shape
            or not np.all(np.isfinite(p)) or not np.all(np.isfinite(g))
            or np.any(abs(g[:,0])>=math.pi/2-1e-6) or np.any(abs(p[:,0])>=math.pi/2-1e-6)):
        raise ValueError('complete finite aligned nonpolar coordinates required')
    rm,rn=radii(g[:,0]);north=rm+g[:,2];east=(rn+g[:,2])*np.cos(g[:,0])
    if np.any(north<=0) or np.any(east<=0):raise ValueError('positive common receiver-coordinate metric required')
    delta=p-g;delta[:,1]=np.arctan2(np.sin(delta[:,1]),np.cos(delta[:,1]))
    errors=delta*np.column_stack((north,east,np.ones(len(g))))
    if not np.all(np.isfinite(errors)):raise ValueError('unrepresentable receiver-coordinate errors')
    return errors


def sections(errors,training_epochs):
    import numpy as np
    from lll.airquantumgrav_geographic_report import error_metrics
    from lll.ilvis0_prediction_observed import accuracy_screen
    errors=np.asarray(errors,float);cut=training_epochs
    if (errors.ndim!=2 or errors.shape[1:]!=(3,) or not np.all(np.isfinite(errors))
            or type(cut) is not int or not 0<cut<len(errors)):
        raise ValueError('complete three-axis errors and an interior training split required')
    result={}
    for name,part in [('training',errors[:cut]),('prediction',errors[cut:])]:
        metrics=error_metrics(part.tolist());metrics.update(maximum_horizontal_m=float(np.max(np.linalg.norm(part[:,:2],axis=1))),
            maximum_absolute_up_m=float(np.max(abs(part[:,2]))))
        result[name]=dict(metrics,accuracy=accuracy_screen(metrics))
    return result
