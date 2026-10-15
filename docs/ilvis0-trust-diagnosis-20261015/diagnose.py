# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four bounded software replays to diagnose the failed, preserved candidate."""
import hashlib
import json
from pathlib import Path

import numpy as np
from lll import ilvis0_solver_trust as solver
from lll.ilvis0_boundary_controls import problem_for,starts

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
target=HERE/'diagnosis.json'
if target.exists(): raise ValueError('completed diagnosis cannot rerun')
manifest=dict(software_starts=4,maximum_evaluations_per_start=200,archival_starts=0,
              sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__),Path(solver.__file__))})
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
rows=[]
for index in range(4):
    problem,optimum,expected,_=problem_for('nonlinear27')
    result=solver.fit_candidate(problem,'control',start=starts(27)[index],maximum_evaluations=200,
                                physical_step=lambda delta:np.column_stack((delta,np.zeros((len(delta),2)))))
    row=dict(start=index,expected_cost=expected,prediction_error=float(np.linalg.norm(problem.residual(np.array(result['normalized_parameters']))-problem.residual(optimum))),fit=result)
    rows.append(row)
    print(json.dumps(dict(start=index,converged=result['converged'],cost=result['residual_sum_squares'],
                         evaluations=result['evaluations'],message=result['message'],probe=result['stability_probe'],
                         last_steps=result['step_history'][-2:])),flush=True)
target.write_text(json.dumps(dict(manifest=manifest,results=rows),indent=2,sort_keys=True)+'\n')
