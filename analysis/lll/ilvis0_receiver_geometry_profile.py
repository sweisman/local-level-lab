# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional pairwise Earth-rate geometry on preselected receiver tracks."""

import json
import math
from pathlib import Path

import numpy as np

from . import ilvis0_observation as observation
from . import ilvis0_segments as segments
from . import models
from .ilvis0_motion_diagnosis import local_slope
from .ilvis0_receiver_candidate_study import (
    PARENT,CANDIDATES,CONTEXTS,INVENTORY,bound_source,tasks)
from .studies.artifacts import atomic,encoded


ID='ilvis0-receiver-geometry-profile-20261116'
POLICY_PATH='docs/ilvis0-receiver-geometry-profile/policy.json'
DEFINITION='docs/ilvis0-receiver-geometry-profile/study-definition.json'
POLICY=dict(version='ilvis0-receiver-geometry-profile-v1',
            coordinate_slope_span_s=30.,maximum_receiver_gap_s=2.,
            model_fits_enabled=False,scientific_eligible=False)


def write_definition(root):
    from .studies.dependencies import source_closure

    root=Path(root).resolve()
    seeds=(str(Path(__file__).relative_to(root)),
           'analysis/lll/ilvis0_receiver_candidate_study.py',
           'analysis/lll/ilvis0_observation.py',
           'analysis/lll/ilvis0_segments.py',
           'analysis/tests/test_ilvis0_receiver_geometry_profile.py',
           'docs/ilvis0-receiver-geometry-profile/PLAN.md')
    definition=dict(id=ID,scope='29 receiver/raw tracks; conditional model '
                    'contrast geometry only; no observed Earth-model fits',
                    adapter=str(Path(__file__).relative_to(root)),
                    sources=source_closure(root,seeds),
                    inputs=dict(candidates=CANDIDATES,parent=PARENT,
                                contexts=CONTEXTS,inventory=INVENTORY,
                                policy=POLICY_PATH),tasks=tasks(root),
                    workers=1,threads=1,maximum_wall_s=7200,
                    stop_after_failure=False)
    for name,value in ((POLICY_PATH,POLICY),(DEFINITION,definition)):
        path=root/name;raw=encoded(value)
        if path.is_file():
            if path.read_bytes()!=raw:raise ValueError('frozen geometry definition changed')
        else:atomic(path,raw)
    return definition


def geometry_from_fixes(fixes,*,policy=POLICY):
    """Profile conditional physical contrasts using timed positions only."""
    if policy!=POLICY or len(fixes)<61:
        raise ValueError('fixed policy and sufficient receiver fixes required')
    values=np.array([[r[k] for k in ('time_s','latitude_rad','longitude_rad')]
                     for r in fixes],float)
    if (not np.all(np.isfinite(values)) or
            np.any(np.diff(values[:,0])<=0) or
            np.any(np.diff(values[:,0])>policy['maximum_receiver_gap_s']) or
            np.any(abs(values[:,1])>=math.pi/2)):
        raise ValueError('ordered finite uninterrupted receiver positions required')
    t,phi,lon=values.T
    phi_dot=local_slope(t,phi,policy['coordinate_slope_span_s'])
    lam_dot=local_slope(t,np.unwrap(lon),policy['coordinate_slope_span_s'])
    keep=np.isfinite(phi_dot)&np.isfinite(lam_dot)
    if int(np.sum(keep))<10:
        raise ValueError('fewer than ten supported coordinate-rate epochs')
    t,phi,phi_dot,lam_dot=t[keep],phi[keep],phi_dot[keep],lam_dot[keep]
    heading=np.arctan2(np.cos(phi)*lam_dot,phi_dot)
    rotation=models.earth_rate_sphere(phi)
    globe=np.column_stack((np.cos(phi)*lam_dot,-phi_dot,-np.sin(phi)*lam_dot))
    disc=np.column_stack((np.zeros(len(phi)),np.zeros(len(phi)),-lam_dot))
    envelope=observation.contrast_envelope(
        t,heading,rotation,globe,disc,np.ones(len(t),int))
    return dict(receiver_fixes=len(fixes),supported_epochs=len(t),
                latitude_range_deg=np.rad2deg([min(phi),max(phi)]).tolist(),
                conditional_geometry=envelope,gyro_observations_used=False,
                group1_attitude_used=False,aircraft_motion_independently_known=False,
                receiver_coordinate_metric='reported geodetic coordinates; conditional',
                scientific_decision='abstain')


def evaluate(task,context):
    policy=json.loads(context.input_path('policy').read_bytes())
    if policy!=POLICY:raise ValueError('fixed geometry policy required')
    source,timing=bound_source(task,context)
    report=segments.scan(source,timing,policy=segments.RECEIVER_RAW_INVENTORY_POLICY)
    matches=[row for row in report['segments'] if row['segment_id']==task['segment_id']]
    if (report['source_sha256']!=task['source_sha256'] or len(matches)!=1 or
            abs(matches[0]['duration_s']-task['candidate_duration_s'])>1e-6):
        raise ValueError('sealed receiver/raw interval did not reproduce')
    result=dict(identity=task['identity'],segment_id=task['segment_id'],
                source_sha256=task['source_sha256'],filename=task['filename'],
                passed=True,profile=geometry_from_fixes(matches[0]['receiver_fixes']),
                scientific_decision='abstain',earth_model_fits=0,
                gyro_residuals_inspected=False)
    artifact=context.save('geometry.json',result)
    return dict(identity=task['identity'],segment_id=task['segment_id'],
                passed=True,result_artifact=artifact,
                scientific_decision='abstain',earth_model_fits=0,
                gyro_residuals_inspected=False)
