# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check one persistent heading-step error direction on fixed ESA forecasts."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_HEADING_STEP_PLAN.md'
FREEZE = FOLDER+'esa-heading-step-freeze.json'
RESULT = FOLDER+'esa-heading-step-result.json'
ANCHOR = 59


def heading_mode(path_m, *, anchor):
    """Return the first derivative of a fixed heading change after one epoch."""
    import numpy as np

    path = np.asarray(path_m,float)
    if (path.ndim!=2 or path.shape[1]!=3 or not np.isfinite(path).all()
            or type(anchor) is not int or not 0<=anchor<len(path)-1):
        raise ValueError('finite path and fixed pre-step epoch required')
    delta=path[anchor+1:]-path[anchor]
    design=np.zeros_like(path)
    design[anchor+1:,0]=-delta[:,1]
    design[anchor+1:,1]=delta[:,0]
    return design


def projection(errors, direction):
    import numpy as np

    errors,direction=(np.asarray(v,float) for v in (errors,direction))
    if (errors.ndim!=1 or errors.shape!=direction.shape
            or not np.isfinite(errors).all() or not np.isfinite(direction).all()):
        raise ValueError('aligned finite complete score series required')
    norm=float(direction@direction)
    baseline=float(errors@errors)
    if min(norm,baseline)<=0:
        raise ValueError('nonzero score and prediction sensitivity required')
    angle=float(errors@direction/norm)
    mismatch=errors-angle*direction
    remaining=float(mismatch@mismatch)
    return dict(angle_rad=angle,original_score=baseline,remaining_score=remaining,
                removed_fraction=max(0.,1-remaining/baseline))


def _read_window(study,cut,rows,score):
    import numpy as np
    from .esa_changing_drift_transfer import _coordinates
    from .esa_native_rolling_transfer import LAWS, matched_window
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import restore
    from .studies.artifacts import digest, encoded

    training=json.loads(gzip.decompress(study.input(f'{cut}-training',raw=True)))
    times=study.input(f'{cut}-forecast_times')
    origin=study.input(f'{cut}-saved-input-binding')['time_origin_s']
    held=matched_window(rows,training,times,origin=origin)
    if len(held)!=120 or digest(encoded(held))!=score['held_receiver_sha256']:
        raise ValueError('unchanged archived 120 scoring rows required')
    observed=_coordinates(held)
    metric=physical_metric(_coordinates(training[-1:]))[0]
    results={}
    for law in LAWS:
        identity=f'{cut}-{law}'
        saved=study.input(identity+'-conditional')
        memo=study.artifact(identity,'factor-replay.json')
        operator=restore(study.artifact(identity,'rolling-factors.npz',raw=True),
            expected_sha256=memo['snapshot_sha256'],
            expected_configuration=saved['full_operator_configuration'],maximum_bytes=64*1024**2)
        path=np.asarray(saved['conditional_receiver_mean'])
        offset=path-path[ANCHOR]
        offset[:,1]=longitude_residual(offset[:,1])
        design=heading_mode(offset*metric,anchor=ANCHOR)/metric
        error=observed-path
        error[:,1]=longitude_residual(error[:,1])
        _,state=operator.apply_block(np.zeros((cut*3,2)),first_epoch=0)
        cols=np.column_stack((error.ravel(),design.ravel()))
        whitened,_=operator.apply_block(cols,first_epoch=cut,state=state)
        fit=projection(*whitened.T)
        if not np.isclose(fit['original_score'],score['scores'][law]['squared_standardized_error'],
                          rtol=1e-12,atol=1e-12):
            raise ValueError('original held-out score must replay')
        metre_delta=(error-design*fit['angle_rad'])*metric
        results[law]=dict(**fit,angle_deg=float(np.rad2deg(fit['angle_rad'])),
            rms_east_before_m=float(np.sqrt(np.mean((error[:,1]*metric[1])**2))),
            rms_east_after_m=float(np.sqrt(np.mean(metre_delta[:,1]**2))))
    return results


def run(root,action):
    from . import esa_innovation_transfer as evidence
    from . import esa_native_rolling_transfer as original
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest,encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root,'data/'+original.ID)) as study:
        if study.completion['manifest_sha256']!=evidence.SOURCE_SHA or study.completion['state']!='complete':
            raise ValueError('original no-refit covariance replay required')
        own=Path(__file__).relative_to(root).as_posix()
        freeze=encoded(dict(study=study.completion,anchor_index=ANCHOR,score_projections=4,
            earlier_score=evidence.EARLY_SCORE_SHA,later_score=evidence.LATE_SCORE_SHA,
            environment=runtime_environment(),native_calls=0,optimizer_starts=0,protected_reads=0,
            sources={name:digest((root/name).read_bytes()) for name in source_closure(
                root,(own,PLAN,'analysis/tests/test_esa_heading_step.py'))}))
        if action=='freeze':
            _write_equal(root/FREEZE,freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes()!=freeze:
            raise ValueError('unchanged fixed heading-step experiment required')
        early,late=((root/path).read_bytes() for path in (original.EARLIER_REPORT,original.REPORT))
        if digest(early)!=evidence.EARLY_SCORE_SHA or digest(late)!=evidence.LATE_SCORE_SHA:
            raise ValueError('original two score receipts changed')
        rows=json.loads(gzip.decompress(study.input('400-training',raw=True)))
        result={'earlier':_read_window(study,200,rows,json.loads(early))}
        with closing(ClosedStudy(root,original.LATER_SOURCE,store=study.store)) as source:
            if source.completion['manifest_sha256']!=original.LATER_SOURCE_SHA:
                raise ValueError('original recorded development data required')
            rows=json.loads(gzip.decompress(source.input('training',raw=True)))
        result['later']=_read_window(study,400,rows,json.loads(late))
    output=encoded(dict(freeze_sha256=digest(freeze),results=result,
        scientific_decision='abstain',protected_reads=0,native_calls=0,optimizer_starts=0))
    _write_equal(root/RESULT,output)
    return dict(sha256=digest(output),windows=len(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','replay'))
    print(json.dumps(run(Path.cwd(),parser.parse_args().action),sort_keys=True))
