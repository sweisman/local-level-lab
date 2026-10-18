# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-point arithmetic diagnostics; no fitted result or decision promotion."""
import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import lsq_linear

from .ilvis0_solver_position import physical_metric
from .ilvis0_solver_refinement import projected_stationarity

VERSION='ilvis0-fixed-endpoint-precision-v1'
FRACTIONS=(1.,.5,.25,.125,.0625)


def inspect_endpoint(problem,point,model,direction,ordinary,extended,call):
    point=np.asarray(point,float);direction=np.asarray(direction,float)
    if (point.ndim!=1 or direction.shape!=point.shape
            or not np.all(np.isfinite(point)) or not np.all(np.isfinite(direction))
            or np.any(abs(point)>1) or np.any(abs(point+direction)>1+1e-14)):
        raise ValueError('finite feasible saved point and full correction required')
    metric=physical_metric(problem.gps)
    def evaluate(u,kernel):
        problem.tangent_kernel=kernel
        coordinates,jac,boundaries=call(problem.prediction_tangent,u,model)
        residual=problem.whiten(coordinates-problem.gps)
        jacobian=solve_triangular(problem.cholesky,jac,lower=True)
        return dict(coordinates=coordinates,jac=jac,residual=residual,whitened_jac=jacobian,
                    cost=float(residual@residual),boundaries=boundaries,
                    stationarity=projected_stationarity(u,residual,jacobian)[0])
    def difference(a,b):
        out=np.asarray(a)-np.asarray(b)
        out[:,1]=(out[:,1]+np.pi)%(2*np.pi)-np.pi
        return out*metric
    def stats(error):
        return dict(rms_neu_m=np.sqrt(np.mean(error**2,axis=0)).tolist(),
                    maximum_neu_m=np.max(abs(error),axis=0).tolist())
    centers=[evaluate(point,kernel) for kernel in (ordinary,extended)]
    probe_rows=[]
    def inspect(u,current,central,arithmetic,fraction):
        delta=u-point
        linear=(central['jac']@delta).reshape(problem.gps.shape)*metric
        physical=difference(current['coordinates'],central['coordinates'])
        affine=central['residual']+central['whitened_jac']@delta
        return dict(arithmetic=arithmetic,fraction=fraction,cost=current['cost'],
                    cost_relative_change=abs(current['cost']-central['cost'])/max(current['cost'],central['cost'],1.),
                    affine_predicted_cost=float(affine@affine),stationarity=current['stationarity'],
                    position_change=stats(physical),linear_prediction_error=stats(physical-linear),
                    boundary_epochs=current['boundaries'])
    for fraction in FRACTIONS:
        u=np.clip(point+fraction*direction,-1,1)
        for arithmetic,kernel,center in zip(('ordinary','extended'),(ordinary,extended),centers):
            current=evaluate(u,kernel)
            probe_rows.append(inspect(u,current,center,arithmetic,fraction))
    central=centers[1]
    correction=lsq_linear(central['whitened_jac'],-central['residual'],bounds=(-1-point,1-point),
                         method='bvls',tol=1e-10,max_iter=100)
    if not correction.success or not np.all(np.isfinite(correction.x)):
        raise ValueError('extended bounded affine correction unfinished')
    u=np.clip(point+correction.x,-1,1)
    new=[]
    for arithmetic,kernel,center in zip(('ordinary','extended'),(ordinary,extended),centers):
        current=evaluate(u,kernel)
        new.append(inspect(u,current,center,arithmetic,1.))
    scale=metric.ravel()[:,None]
    jac_difference=(centers[1]['jac']-centers[0]['jac'])*scale
    return dict(version=VERSION,ordinary_center_cost=centers[0]['cost'],
                extended_center_cost=centers[1]['cost'],
                central_coordinate_difference=stats(difference(centers[1]['coordinates'],centers[0]['coordinates'])),
                physical_jacobian_difference_frobenius=float(np.linalg.norm(jac_difference)),
                central_stationarity=[c['stationarity'] for c in centers],
                fixed_correction_probes=probe_rows,extended_correction=correction.x.tolist(),
                extended_correction_probes=new,native_evaluations=14,observed_fit_starts=0,
                qualifies_original_fit=False,scientific_decision='abstain')
