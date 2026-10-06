# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved geometry failures and small analytic tangents; never run flights or fits."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'analysis'), str(ROOT/'server')]
from lll import models
from lll.calib import RAD2DPH
from lll.inference import CandidateProblem, science_information
from lll.inference_policy import digest
from lll.policy import CANDIDATE_POLICY
from lll.research_design import implementation_hash, plain, protocol_geometry
from lll.runtime import numerical_environment


def analytic_problem(protocol, crab):
    """Ideal one-minute bins: sharp course changes, known mount axes, no qualification/noise.

    Spherical latitude integration is a fixture, not original campaign reconstruction.
    No synthesis, optimizer, bootstrap or CandidateProblem.solve is used.
    """
    t = np.arange(30., sum(leg[1] for leg in protocol['legs'])*60., 60.)
    ends = np.cumsum([leg[1]*60. for leg in protocol['legs']])
    groups = np.minimum(np.searchsorted(ends, t), len(ends)-1)
    psi = np.radians(np.array([leg[0] for leg in protocol['legs']])[groups])
    speed = protocol['speed']
    vn, ve = speed*np.cos(psi), speed*np.sin(psi)
    radius = 6371000.+11000.
    lat = np.radians(protocol['lat0'])+np.cumsum(vn)*60./radius
    turns = np.searchsorted(np.asarray(protocol['turn_schedule'])*60., t)
    fwd = np.column_stack([(-1.)**turns, np.zeros(len(t)), np.zeros(len(t))])
    bins = dict(t=t, dt=np.full(len(t), 60.), seg=groups+turns*len(ends),
        psi=psi, lat=lat, h=np.full(len(t), 11000.), v_n=vn, v_e=ve,
        lon_rate=ve/(radius*np.cos(lat)), up=np.tile([0., 0., 1.], (len(t), 1)),
        dup_dt=np.zeros((len(t), 3)), psi_dot=np.zeros(len(t)), gyro=np.zeros((len(t), 3)))
    settings = dict(crab_model=crab, crab_knot_seconds=300., crab_rate_sigma_dph=1.,
        bias_model='dynamic', bias_knot_seconds=900., bias_rw_sigma_dph_sqrth=3.,
        forward_uncertainty=True)
    return CandidateProblem(bins, fwd, lambda _: 0., np.full(3, 2/RAD2DPH), settings,
                            forward_sigma_rad=.02)


def tangent_audit(protocol):
    out = []
    for crab in ('dynamic', 'wind'):
        p = analytic_problem(protocol, crab)
        for anchor, k in models.EXPECTED_K.items():
            state = np.zeros(p.npar)
            state[:3] = k
            _, J = p.prediction(state, True)
            components = dict(residual_bias=list(range(3, p.base_p)),
                dynamic_bias=list(range(p.base_p, p.p)), crab=list(range(p.p, p.p+p.nc)),
                forward_axis=[p.npar-1])
            results = {}
            for remove in (None, *components):
                keep = [i for i in range(p.npar) if i not in components.get(remove, [])]
                report = science_information(J[:, keep], p.w)['report']
                results['full' if remove is None else 'without_'+remove] = report
            out.append(dict(crab_model=crab, anchor=anchor, reports=results))
    return out


def audit(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    content = {k: v for k, v in manifest.items() if k != 'manifest_hash'}
    if digest(content) != manifest['manifest_hash']:
        raise ValueError('invalid historical manifest hash')
    archive = directory/'records.jsonl.gz'
    raw = gzip.decompress(archive.read_bytes())
    rows = [json.loads(line) for line in raw.splitlines()]
    if ([row['case'] for row in rows] != manifest['config']['cases'] or
            any(row['manifest_hash'] != manifest['manifest_hash'] for row in rows)):
        raise ValueError('historical task/provenance mismatch')
    cutoff = CANDIDATE_POLICY['retention_threshold']
    cases, flips = [], []
    for row in rows:
        result, case = row['result'], row['case']
        slip = result.get('slip') or {}
        before = slip.get('pre_exclusion_geometry') or {}
        planned = len({leg[0] for leg in result['design']['simulator']['legs']})
        groups = (result.get('heading_diversity') or {}).get('groups', [])
        design = result.get('design_identifiability') or {}
        anchor_ranks = {str(factor): min((sum(v >= cutoff*factor for v in a['normalized_singular_values'])
            for a in design.get('anchors', {}).values()), default=None) for factor in (.9, 1., 1.1)}
        cases.append(dict(case=case, intended_heading_count=planned,
            retained_heading_groups=len(groups), pre_watchdog_bins=before.get('n_bins'),
            post_watchdog_seconds=sum(g['seconds'] for g in groups),
            watchdog_excluded_segments=slip.get('exclude_segments', []),
            failure=result.get('failure'), flags=result.get('flags'),
            model_test_rank=result.get('model_test_rank'), design_rank=design.get('estimable_rank'),
            design_anchor_ranks_at_cutoff_factors=anchor_ranks))
        if len(set(anchor_ranks.values())) > 1:
            flips.append(case)
    protocol = manifest['config']['protocol']
    # Reviewable proposal only. Longer qualifying dwell and repeated opposing headings;
    # no assertion of adequacy follows from an idealized tangent calculation.
    proposals = []
    for name, bearings, turns in [
        ('repeated-four-directions-90min', [10., 100., 190., 280., 10., 100.], [5.,20.,35.,50.,65.,80.]),
        ('repeated-opposing-directions-90min', [10.,190.,100.,280.,10.,190.], [5.,20.,35.,50.,65.,80.])]:
        proposed = protocol_geometry(dict(lat0=35., lon0=-30., speed=270.,
            legs=[[b,15.] for b in bearings], turn_schedule=turns))
        proposals.append(dict(name=name, protocol=proposed, state='proposal_not_flight_tested',
            analytic_tangents=tangent_audit(proposed)))
    diagnostic = tangent_audit(protocol)
    stress = []
    for cell_id in ('lat+35-h6-good-t60-v270-turn3', 'lat+35-h6-good-t180-v270-turn3'):
        sim = next(row['result']['design']['simulator'] for row in rows if row['case']['cell_id'] == cell_id)
        geometry = protocol_geometry({k: sim[k] for k in ('lat0', 'lon0', 'speed', 'legs')} |
                                     {'turn_schedule': [turn[0] for turn in sim['index_turns']]})
        stress.append(dict(cell_id=cell_id, analytic_tangents=tangent_audit(geometry)))
    return plain(dict(partition='development', mode='saved records and analytic bin fixtures; no flights or fits',
        historical_manifest_hash=manifest['manifest_hash'], historical_implementation_hash=manifest['implementation_hash'],
        audit_implementation_hash=implementation_hash(), audit_environment=numerical_environment(),
        source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        completed_evaluations=len(rows), failure_flags=dict(Counter(flag for row in cases if row['failure'] for flag in row['flags'])),
        design_rank_flips_under_ten_percent_cutoff_shift=flips, cases=cases,
        analytic_control=diagnostic, analytic_stress=stress, protocol_proposals=proposals,
        findings=[
            'Mixed nuisance column units made numerical projection rank parameterization-dependent; fixed by unit-column scaling.',
            'Six-heading 60-minute fixtures allocate exactly ten minutes per leg; turn smoothing can fail the ten-minute stable-cruise screen.',
            'All six no-fit cases retain mount-slip/ambiguous-yaw/no-bins flags; watchdog selection removed every bin.',
            'Long dwell also permits unpenalized 15-minute dynamic bias to absorb slow science signals; longer flights alone need not help.',
            'Wind uses two course-modulated coefficients per time knot, versus one dynamic angle; its extra nuisance span can remove contrast information.',
            'The saved exact-control still-globe anchor second singular value is below the science cutoff; truncated contrast retention is not all pre-cutoff information.',
            'Anchor weighting and science coefficients exclude fitted gyro values, but retained bins and estimated forward/mount axes still condition the design report.'],
        limitations='Analytic fixtures use known axes and unqualified sharp course changes; they do not reconstruct historical Jacobians or establish real-flight power. Preserve historical results and gates.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, default=ROOT/'docs/geometry-development-20261006')
    parser.add_argument('--output', type=Path, default=ROOT/'docs/geometry-development-20261006/audit.json')
    args = parser.parse_args()
    report = audit(args.campaign)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(evaluations=report['completed_evaluations'],
        design_rank_flips=len(report['design_rank_flips_under_ten_percent_cutoff_shift']),
        output=str(args.output))))


if __name__ == '__main__':
    main()
