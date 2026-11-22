# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select and check turns in an archived ESA holdout using receiver motion only."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_MANEUVER_PAIRS_PLAN.md'
SELECTION = FOLDER+'esa-maneuver-pairs-selection.json'
RESULT = FOLDER+'esa-maneuver-pairs-result.json'
STUDY = 'data/esa-linear-uncertainty-development-v3-20261115'
MANIFEST = '0d89b2d2af9b8546cef9bf33c6e222e2a19214137f87805a1b6241f10dc55092'
TASK = 'single-pass-receiver-conditional'
SCORING_SHA = '5cce2704433e7dece8eec336882692e15194d6c882d8e2bd7efa67265a172c2b'
CUT, LATER, BLOCK = 800, 400, 30
TURN_SPAN, STRAIGHT_SPAN = 5., 2.


def select_pairs(course_spans):
    """Use contiguous before/after controls with the same time spacing."""
    if any(not math.isfinite(x) or x<0 for x in course_spans):
        raise ValueError('finite nonnegative course spans required')
    indices = range(1,len(course_spans)-1)
    turns = [i for i,v in enumerate(course_spans) if v>=TURN_SPAN]
    occupied = {j for i in turns for j in (i-1,i,i+1)}
    matches = []
    for turn in turns:
        if (turn not in indices
                or max(course_spans[turn-1],course_spans[turn+1])>STRAIGHT_SPAN
                or any(abs(turn-other)<=2 for other in turns if other!=turn)):
            continue
        candidates = [i for i in indices if not occupied.intersection(range(i-1,i+2))
                      and max(course_spans[i-1:i+2])<=STRAIGHT_SPAN]
        if candidates:
            control = min(candidates,key=lambda i:(abs(i-turn),i))
            matches.append(dict(turn=turn,straight=control))
            occupied.update(range(control-1,control+2))
    return dict(turn_centres=turns,matches=matches,
                unmatched_turns=sorted(set(turns)-{m['turn'] for m in matches}),
                straight_centres=[i for i in indices if max(course_spans[i-1:i+2])<=STRAIGHT_SPAN])


def _motion(rows):
    import numpy as np

    v = np.asarray([[r['north_mps'],r['east_mps']] for r in rows])
    t = np.asarray([r['time_s'] for r in rows])
    if (not np.isfinite(v).all() or not np.isfinite(t).all() or np.any(np.diff(t)<=0)
            or np.any(np.linalg.norm(v,axis=1)==0)):
        raise ValueError('complete ordered original ground velocity required')
    course = np.unwrap(np.arctan2(v[:,1],v[:,0]))
    blocks=[]
    for i in range(LATER//BLOCK):
        start=CUT+i*BLOCK
        stop=start+BLOCK
        profile=course[start-1:stop]
        blocks.append(dict(block=i,first_epoch=start,last_epoch=stop-1,
            course_span_deg=float(np.rad2deg(np.ptp(profile))),
            net_course_change_deg=float(np.rad2deg(profile[-1]-profile[0])),
            ground_speed_mean_mps=float(np.mean(np.linalg.norm(v[start:stop],axis=1))),
            up_velocity_mean_mps=float(np.mean([r['up_mps'] for r in rows[start:stop]]))))
    return blocks,course[CUT:]


def run(root,action):
    import numpy as np
    from .esa_changing_drift_transfer import _coordinates
    from .esa_native_rolling_transfer import LATER_SOURCE, LATER_SOURCE_SHA, matched_window
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, STUDY)) as study, closing(
            ClosedStudy(root,LATER_SOURCE,store=study.store)) as receiver:
        if (study.completion['manifest_sha256']!=MANIFEST or study.completion['state']!='complete'
                or study.rows[TASK]['passed'] is not True
                or receiver.completion['manifest_sha256']!=LATER_SOURCE_SHA
                or receiver.manifest['inputs']['scoring']['sha256']!=SCORING_SHA):
            raise ValueError('exact verified same-flight 800/400 study and original scoring source required')
        binding=study.input('saved-input-binding')
        if binding['source_id']!='esa-99f1530c3eda4318' or binding['protected_reads']!=0:
            raise ValueError('only the opened development interval may be used')
        rows=json.loads(gzip.decompress(receiver.input('scoring',raw=True)))
        training=json.loads(gzip.decompress(study.input('training',raw=True)))
        if len(rows)!=CUT+LATER or len(training)!=CUT or rows[:CUT]!=training:
            raise ValueError('exact saved training and held data boundary required')
        blocks,heading=_motion(rows)
        selected=select_pairs([b['course_span_deg'] for b in blocks])
        source=Path(__file__).relative_to(root).as_posix()
        plan=encoded(dict(study=study.completion,scoring_sha256=SCORING_SHA,
            sources={name:digest((root/name).read_bytes()) for name in source_closure(
                root,(source,PLAN,'analysis/tests/test_esa_maneuver_pairs.py'))},
            environment=runtime_environment(),block_size=BLOCK,turn_span=TURN_SPAN,
            straight_span=STRAIGHT_SPAN,blocks=blocks,selected=selected,
            unused_tail_epochs=LATER%BLOCK,forecast_path_read=False,
            protected_reads=0,fit_starts=0,native_calls=0))
        if action=='select':
            _write_equal(root/SELECTION,plan)
            return dict(selection_sha256=digest(plan),**selected)
        if (root/SELECTION).read_bytes()!=plan:
            raise ValueError('motion selections must precede reading the forecast')
        forecast=study.artifact(TASK,'conditional-forecast.json')
        saved=study.input('weighted-forecast')
        times=saved['times_s']
        held=matched_window(rows,training,times,origin=binding['time_origin_s'])
        reference=np.asarray(forecast['conditional_receiver_mean'])
        if (forecast['training_epochs']!=CUT or forecast['prediction_epochs']!=LATER
                or len(held)!=LATER or reference.shape!=(LATER,3)
                or forecast['later_receiver_values_used'] is not False):
            raise ValueError('unchanged earlier-only full conditioned path required')
        coords=_coordinates(held)
        delta=coords-reference
        delta[:,1]=longitude_residual(delta[:,1])
        delta*=physical_metric(_coordinates(training[-1:]))[0]
        projection=delta[:,1]*np.cos(heading)-delta[:,0]*np.sin(heading)
        errors=[]
        for i in range(len(blocks)):
            region=slice(i*BLOCK,(i+1)*BLOCK)
            errors.append(dict(block=i,
                cross_track_rms_m=float(np.sqrt(np.mean(projection[region]**2))),
                cross_track_mean_m=float(projection[region].mean()),
                height_rms_m=float(np.sqrt(np.mean(delta[region,2]**2)))))
        changes=[]
        for pair in selected['matches']:
            row=dict(pair)
            for name,center in pair.items():
                row[name+'_cross_track_rms_before_m']=errors[center-1]['cross_track_rms_m']
                row[name+'_cross_track_rms_after_m']=errors[center+1]['cross_track_rms_m']
            changes.append(row)
        output=encoded(dict(selection_sha256=digest(plan),blocks=errors,matched_changes=changes,
            horizontal_rms_m=float(np.sqrt(np.mean(np.sum(delta[:,:2]**2,axis=1)))),
            height_rms_m=float(np.sqrt(np.mean(delta[:,2]**2))),
            protected_reads=0,fit_starts=0,native_calls=0,scientific_decision='abstain'))
    _write_equal(root/RESULT,output)
    return dict(sha256=digest(output),usable_pairs=len(changes),**selected)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('select','compare'))
    print(json.dumps(run(Path.cwd(),parser.parse_args().action),sort_keys=True))
