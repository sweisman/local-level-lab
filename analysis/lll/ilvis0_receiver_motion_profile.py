# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive receiver-only motion of preselected airborne tracks."""

import csv
import io
import json
import math
from pathlib import Path

import numpy as np

from . import ilvis0_segments as segments
from .ilvis0_distance_inventory_study import CONTEXTS, INVENTORY
from .ilvis0_motion_diagnosis import local_slope
from .models import WGS84_A, WGS84_E2
from .studies.artifacts import atomic, encoded, safe_path


ID = 'ilvis0-receiver-motion-profile-20261116'
PARENT = 'docs/ilvis0-receiver-raw-inventory/study-definition.json'
CANDIDATES = 'docs/ilvis0-receiver-raw-inventory/candidates.csv'
POLICY_PATH = 'docs/ilvis0-receiver-motion-profile/policy.json'
DEFINITION = 'docs/ilvis0-receiver-motion-profile/study-definition.json'
POLICY = dict(version='ilvis0-receiver-motion-profile-v1',
              velocity_window_s=30., course_rate_window_s=30.,
              maximum_receiver_gap_s=2.,
              reference_vertical_rate_mps=1.5,
              reference_course_rate_deg_s=.05,
              scientific_eligibility=False)


def _candidate_rows(blob):
    rows = list(csv.DictReader(io.StringIO(blob.decode('utf-8'))))
    if (len(rows) != 29 or len({r['segment_id'] for r in rows}) != 29 or
            len({r['task'] for r in rows}) != 29 or
            any(r['level_motion_screened'] != 'False' for r in rows)):
        raise ValueError('exact sealed 29-candidate input required')
    return rows


def write_definition(root):
    """Bind the 29 selected originals and a finite no-fit task budget."""
    from .studies.dependencies import source_closure

    root = Path(root).resolve()
    rows = _candidate_rows((root/CANDIDATES).read_bytes())
    parent = json.loads((root/PARENT).read_bytes())
    by_task = {r['identity']: r for r in parent['tasks']}
    if len(by_task) != 232 or len(parent['tasks']) != 232:
        raise ValueError('complete parent task list required')
    tasks = []
    for row in rows:
        original = by_task.get(row['task'])
        if original is None or original['source_sha256'] != row['source_sha256']:
            raise ValueError('candidate source differs from sealed parent')
        source = safe_path(root, original['source_path'])
        if not source.is_file() or source.stat().st_size != original['compressed_bytes']:
            raise ValueError('candidate original missing or changed size')
        tasks.append(dict(original, segment_id=row['segment_id'],
                          candidate_duration_s=float(row['duration_s'])))
    # The candidate ID is the exact interval binding. The parent scan must
    # reproduce it before any profile is saved.
    seeds = (str(Path(__file__).relative_to(root)),
             'analysis/lll/ilvis0_segments.py',
             'analysis/lll/ilvis0_receiver_support.py',
             'analysis/lll/ilvis0_motion_diagnosis.py',
             'analysis/tests/test_ilvis0_receiver_motion_profile.py',
             'docs/ilvis0-receiver-motion-profile/PLAN.md')
    definition = dict(id=ID, scope='29 preselected receiver/raw candidates; '
                      'receiver-only motion description; no Earth-model fits',
                      adapter=str(Path(__file__).relative_to(root)),
                      sources=source_closure(root,seeds),
                      inputs=dict(candidates=CANDIDATES,parent=PARENT,
                                  contexts=CONTEXTS,inventory=INVENTORY,
                                  policy=POLICY_PATH),
                      tasks=sorted(tasks,key=lambda r:r['identity']),
                      workers=1,threads=1,maximum_wall_s=7200,
                      stop_after_failure=False)
    for name,value in ((POLICY_PATH,POLICY),(DEFINITION,definition)):
        target=root/name;blob=encoded(value)
        if target.is_file():
            if target.read_bytes()!=blob:raise ValueError('frozen motion definition differs')
        else:atomic(target,blob)
    return definition


def profile_fixes(fixes, *, policy=POLICY):
    """Local receiver-coordinate slopes; unsupported epochs remain missing."""
    if policy != POLICY or len(fixes) < 61:
        raise ValueError('fixed policy and enough receiver fixes required')
    values=np.array([[r[k] for k in ('time_s','latitude_rad','longitude_rad','height_m')]
                     for r in fixes],float)
    if (not np.all(np.isfinite(values)) or np.any(np.diff(values[:,0])<=0)
            or np.any(np.diff(values[:,0])>policy['maximum_receiver_gap_s'])
            or np.any(abs(values[:,1])>=math.pi/2)):
        raise ValueError('ordered finite uninterrupted receiver fixes required')
    t,lat,lon,height=values.T
    north_rate=local_slope(t,lat,policy['velocity_window_s'])
    east_rate=local_slope(t,np.unwrap(lon),policy['velocity_window_s'])
    climb=local_slope(t,height,policy['velocity_window_s'])
    sine=np.sin(lat);base=1-WGS84_E2*sine*sine
    north=north_rate*(WGS84_A*(1-WGS84_E2)/base**1.5+height)
    east=east_rate*(WGS84_A/np.sqrt(base)+height)*np.cos(lat)
    supported=np.isfinite(north)&np.isfinite(east)&np.isfinite(climb)
    if np.count_nonzero(supported)<31:
        raise ValueError('insufficient continuous local velocity support')
    course=np.unwrap(np.arctan2(east[supported],north[supported]))
    turn=local_slope(t[supported],course,policy['course_rate_window_s'])
    final=np.isfinite(turn)
    if not np.any(final):
        raise ValueError('no supported course-change estimates')
    climb=climb[supported][final]
    speed=np.hypot(north[supported][final],east[supported][final])
    turn_deg=np.degrees(turn[final])
    return dict(receiver_fixes=len(fixes),supported_velocity_epochs=int(np.sum(supported)),
                supported_course_rate_epochs=int(np.sum(final)),
                duration_s=float(t[-1]-t[0]),
                height_span_m=float(np.ptp(height)),
                median_speed_kmh=float(np.median(speed)*3.6),
                minimum_speed_kmh=float(np.min(speed)*3.6),
                course_span_deg=float(np.degrees(np.ptp(course[final]))),
                p95_abs_climb_mps=float(np.percentile(abs(climb),95)),
                max_abs_climb_mps=float(np.max(abs(climb))),
                p95_abs_course_rate_deg_s=float(np.percentile(abs(turn_deg),95)),
                max_abs_course_rate_deg_s=float(np.max(abs(turn_deg))),
                reference_vertical_rate_mps=policy['reference_vertical_rate_mps'],
                reference_course_rate_deg_s=policy['reference_course_rate_deg_s'],
                receiver_coordinate_metric='WGS84, screening only',
                gyro_used=False,group1_motion_used=False,
                scientific_decision='abstain')


def evaluate(task,context):
    root=Path(context.root).resolve().parents[1]
    policy=json.loads(context.input_path('policy').read_bytes())
    rows=_candidate_rows(context.input_path('candidates').read_bytes())
    chosen=next((r for r in rows if r['task']==task['identity']),None)
    parent=json.loads(context.input_path('parent').read_bytes())
    parent_task=next((r for r in parent['tasks'] if r['identity']==task['identity']),None)
    contexts=json.loads(context.input_path('contexts').read_bytes())
    prior=next((r for r in contexts['results'] if r['task_id']==task['identity']),None)
    if (policy!=POLICY or chosen is None or parent_task is None or prior is None
            or task['segment_id']!=chosen['segment_id']
            or task['source_sha256']!=chosen['source_sha256']
            or task['source_sha256']!=parent_task['source_sha256']
            or task['source_path']!=parent_task['source_path']
            or prior['inspection']['source_sha256']!=task['source_sha256']):
        raise ValueError('sealed receiver candidate and source bindings required')
    source=safe_path(root,task['source_path'])
    if source.stat().st_size!=task['compressed_bytes']:
        raise ValueError('original source byte count changed')
    report=segments.scan(source,prior,policy=segments.RECEIVER_RAW_INVENTORY_POLICY)
    matches=[r for r in report['segments'] if r['segment_id']==task['segment_id']]
    if (report['source_sha256']!=task['source_sha256'] or len(matches)!=1
            or abs(matches[0]['duration_s']-task['candidate_duration_s'])>1e-6):
        raise ValueError('parent candidate did not reproduce')
    result=dict(identity=task['identity'],segment_id=task['segment_id'],
                source_sha256=task['source_sha256'],filename=task['filename'],
                passed=True,profile=profile_fixes(matches[0]['receiver_fixes']),
                scientific_decision='abstain',earth_model_fits=0,
                gyro_residuals_inspected=False)
    artifact=context.save('motion.json',result)
    return dict(passed=True,identity=task['identity'],segment_id=task['segment_id'],
                result_artifact=artifact,scientific_decision='abstain',
                earth_model_fits=0,gyro_residuals_inspected=False)
