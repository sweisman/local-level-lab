# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay two high-scoring relaxed points with their shared terms linked."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
from pathlib import Path


RESULT = 'docs/prediction-observed-development/esa-attitude-survivor-physical-replay.json'
SOURCE_SHA = '20daae58ec852916eefb5d5617bc08ed7e2d1286e98ad8de4d74157d991ad61d'
RANGES = ('sphere_still-5-1','flat_still-2-2')


def report(root):
    import numpy as np
    from .esa_attitude_cover_score import GAMMA
    from .esa_attitude_refinement_score import ID as REFINEMENT
    from .esa_attitude_survivor_score import ID
    from .esa_calibration_witness import check_point
    from .esa_linked_training_support import projection_inputs
    from .ilvis0_coupled_map import restore_static_reference
    from .studies.closed import ClosedStudy

    records = []
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root,'data/'+ID)))
        refined = stack.enter_context(closing(ClosedStudy(root,'data/'+REFINEMENT,store=study.store)))
        if (study.completion['manifest_sha256']!=SOURCE_SHA
                or refined.completion['manifest_sha256']!=study.input('cover')['manifest_sha256']):
            raise ValueError('exact sealed survivor and physical reference required')
        for identity in RANGES:
            model = study.tasks[identity]['payload']['model']
            saved = study.artifact(identity,'survivor-support.json')
            prior = study.input(identity+'-feasibility')['trials'][-1]
            anchors = study.input(identity+'-anchors')
            if prior['checked_point'] is not None and prior['checked_point']['loss_passed']:
                anchors.append(dict(point=prior['point'],score_lower=None))
            anchor = max(anchors,key=lambda r:r['score_lower'] if r['score_lower'] is not None else -float('inf'),
                         default=None)
            trial, matched = next((t,c) for t in saved['trials'] for c in t['checks']
                if c.get('loss_passed') and c['score_lower']==saved['lower'])
            point = tuple(map(F,trial['point']))
            if anchor is not None:
                fraction = F(matched['fraction'])
                point = tuple(a+fraction*(v-a) for a,v in zip(map(F,anchor['point']),point,strict=True))
            residual, raw, _, _, _, earlier, target, _ = projection_inputs(lambda k:study.input(k,raw=True),model)
            original = check_point(earlier,raw,residual,target,point[:51],unshared=GAMMA)
            if any(original[k]!=v for k,v in matched.items() if k not in ('fraction','static_passed')):
                raise ValueError('archived relaxed point did not reproduce exactly')
            force, sample = (refined.input(model+suffix) for suffix in ('-force','-first-sample'))
            reference = restore_static_reference(force['configuration'],sample['dv'],sample['dt'],
                lower=force['lower'],upper=force['upper'],center=force['center'],
                expected_report=refined.input(model+'-reference'))
            center = tuple(map(F,force['center']))
            physical = np.clip([float(v+c) for v,c in zip(point[:27],center,strict=True)],
                               force['lower'],force['upper'])
            linked = reference.normalized_values_at(physical)
            if np.any(abs(linked)>1.) or not np.isfinite(linked).all():
                raise ValueError('shared values left their unchanged normalized box')
            displacement = [F(v)-c for v,c in zip(physical,center,strict=True)]
            replay = check_point(earlier,raw,residual,target,[*displacement,*linked],unshared=GAMMA)
            records.append(dict(identity=identity,physical_point=physical.tolist(),
                                relaxed=original,linked=replay))
    return dict(manifest_sha256=SOURCE_SHA,rows=records,fit_starts=0,new_bound_calls=0,
                scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    raw = encoded(report(root))
    _write_equal(root/RESULT,raw)
    print(digest(raw))
