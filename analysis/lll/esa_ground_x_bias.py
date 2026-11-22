# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ground-only support for the ESA X-axis accelerometer endpoint."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_doppler_force import DIRECTORY, FOLDER
from .esa_gyro_calibration_endpoints import BOUNDS, BOUNDS_SHA
from .studies.artifacts import atomic, digest, encoded

PLAN = FOLDER+'ESA_GROUND_X_BIAS_PLAN.md'
GROUND = FOLDER+'esa-ground-force-support-result.json'
GROUND_SHA = 'b8dbbe6bf7ac8565cf7379ffae39f8358850994f38e5b1d8dec005766b06e1be'
REPORT = FOLDER+'esa-ground-x-bias-result.json'


def spread(stops,bias,gain):
    import numpy as np

    bias, gain = np.asarray(bias,float), np.asarray(gain,float)
    values = [np.linalg.norm((stop-bias)/(1.+gain),axis=1) for stop in stops]
    by_stop = [dict(mean_mps2=float(v.mean()),half_spread_mps2=float(np.ptp(v)/2),
                    squared_half_spread_mps4=float(np.ptp(v**2)/2))
               for v in values]
    return dict(bias_mps2=list(bias),gain=list(gain),stops=by_stop,
        max_squared_half_spread_mps4=max(row['squared_half_spread_mps4'] for row in by_stop))


def ground_profile(stops,bias_limits,gain_limits,fixed_x):
    """A linear program for squared force spread about unknown site constants."""
    import numpy as np
    from scipy.optimize import linprog

    stops = [np.asarray(stop,float) for stop in stops]
    limit, gain = np.asarray(bias_limits,float), np.asarray(gain_limits,float)
    if (not stops or any(s.ndim!=2 or s.shape[1]!=3 or len(s)<3 or not np.isfinite(s).all() for s in stops)
            or limit.shape!=gain.shape or limit.shape!=(3,) or np.any(limit<0)
            or np.any(gain<0) or np.any(gain>=1)
            or (fixed_x is not None and abs(fixed_x)>limit[0])):
        raise ValueError('finite matched ground vectors and bounded sensor terms required')
    rows = []
    size = 7+len(stops)
    for index,stop in enumerate(stops):
        center = stop.mean(axis=0)
        row = np.zeros((len(stop),size))
        row[:,:3] = (stop-center)*(stop+center)
        row[:,3:6] = -2*(stop-center)
        row[:,6+index] = -1.
        rows.extend((row,-row))
    inequalities = np.vstack(rows)
    inequalities[:,-1] = -1.
    linked = np.zeros((6,size))
    linked[:3,:3] = linked[3:,:3] = -np.diag(limit)
    linked[:3,3:6] = np.eye(3)
    linked[3:,3:6] = -np.eye(3)
    inequalities = np.vstack((inequalities,linked))
    equality = None
    if fixed_x is not None:
        equality = np.zeros((1,size))
        equality[0,0],equality[0,3] = -fixed_x,1.
    bounds = [*zip((1.+gain)**-2,(1.-gain)**-2), *([(None,None)]*(size-4)), (0.,None)]
    cost = np.zeros(size)
    cost[-1] = 1.
    solved = linprog(cost,A_ub=inequalities,b_ub=np.zeros(len(inequalities)),
        A_eq=equality,b_eq=None if equality is None else [0.],
        bounds=bounds,method='highs',options={'maxiter':2000})
    info = dict(settled=bool(solved.success),status=int(solved.status),iterations=int(solved.nit))
    if not solved.success:
        return info
    scale = solved.x[:3]
    proposed_gain = np.clip(scale**(-.5)-1.,-gain,gain)
    proposed_bias = np.clip(solved.x[3:6]/scale,-limit,limit)
    if fixed_x is not None:
        proposed_bias[0] = fixed_x
    witness = spread(stops,proposed_bias,proposed_gain)
    if abs(witness['max_squared_half_spread_mps4']-solved.fun)>1e-7:
        raise ValueError('physical correction spread differs from the affine program')
    return info|witness


def build(ground,calibration):
    import numpy as np

    raw = [np.asarray(row['minute_means_body_m_s2']) for row in ground['ground']['stops']]
    if [len(s) for s in raw]!=[45,30]:
        raise ValueError('all 75 original minute mean force vectors required')
    limits = calibration['working_limits']
    bias,gain = limits['accel_bias'],limits['accel_gain']
    if bias[0]!=.1:
        raise ValueError('existing reversing bias allowance required')
    sets = {}
    for name,stops in (('first',raw[:1]),('second',raw[1:]),('shared',raw)):
        sets[name] = dict(nominal=spread(stops,[0.]*3,[0.]*3),
            fixed_endpoint=spread(stops,[bias[0],0.,0.],[0.]*3),
            free=ground_profile(stops,bias,gain,None),
            profiled_endpoint=ground_profile(stops,bias,gain,bias[0]))
    return dict(sets=sets,linear_programs=6,ground_minutes=[45,30],source_original_reads=0,
                absolute_gravity_supplied=False,new_earth_model_fits=0,reserved_reads=0,
                independently_calibrated=False,scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(k)!=v for k,v in threads.items()):
        raise ValueError('configure exactly one numerical thread')
    import numpy as np
    import scipy

    root = Path.cwd()
    prior = (root/GROUND).read_bytes()
    calibration = json.loads((root/BOUNDS).read_bytes())['result']
    if digest(prior)!=GROUND_SHA or digest(encoded(calibration))!=BOUNDS_SHA:
        raise ValueError('same sealed ground stops and ESA calibration definition required')
    folder = root/DIRECTORY
    sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_ground_x_bias.py',
               root/'analysis/tests/test_esa_ground_x_bias_list_inputs.py',
               root/(FOLDER+'esa-ground-x-bias-v1-failure.json'),
               root/'analysis/lll/studies/artifacts.py',root/'analysis/lll/compute_budget.py']
    freeze = encoded(dict(inputs=dict(ground=GROUND_SHA,calibration=BOUNDS_SHA),
        sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
            os=platform.system(),arch=platform.machine(),threads=threads),
        max_programs=6,max_iterations_per_program=2000,max_force_vectors=75,max_earth_model_fits=0))
    with (folder/'ground-x-bias.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        binding = folder/'ground-x-bias-v2-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding,freeze)
        if binding.read_bytes()!=freeze:
            raise ValueError('frozen ground-bias check differs')
        if args.action=='freeze':
            print(digest(freeze))
            return
        path = root/REPORT
        charge = folder/'ground-x-bias-v2-charge.json'
        allowance = encoded(dict(freeze_sha256=digest(freeze),linear_programs=6))
        if not path.exists():
            if charge.exists():
                raise ValueError('ground bias programs already charged')
            atomic(charge,allowance)
            result = build(json.loads(prior),calibration)
            atomic(path,encoded(dict(freeze=json.loads(freeze),freeze_sha256=digest(freeze),
                result=result,result_sha256=digest(encoded(result)))))
        saved = json.loads(path.read_bytes())
        if (charge.read_bytes()!=allowance or saved['freeze_sha256']!=digest(freeze)
                or digest(encoded(saved['freeze']))!=digest(freeze)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed ground-bias comparison differs')
        print('75 ground vectors, SHA-256 '+saved['result_sha256'])


if __name__=='__main__':
    main()
