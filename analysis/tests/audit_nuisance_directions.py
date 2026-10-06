# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local nuisance attribution from saved pilot arrays; never simulate or refit."""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))

import numpy as np
from lll import models
from lll.attitude import unit
from lll.calib import RAD2DPH
from lll.design_envelope import nuisance_states
from lll.inference import CandidateProblem, science_information
from lll.research_design import implementation_hash
from lll.runtime import numerical_environment, numerical_environment_hash


def groups_for(problem):
    groups = dict(bias_level=list(range(3, problem.base_p)),
                  bias_drift=list(range(problem.base_p, problem.p)))
    if problem.wind_tas is None:
        groups['wind_crab'] = list(range(problem.p, problem.p + problem.nc))
    else:
        columns = np.arange(problem.p, problem.p + problem.nc).reshape(-1, 3)
        groups['wind_vector'] = columns[:, :2].ravel().tolist()
        groups['airspeed'] = columns[:, 2].tolist()
    if problem.nm: groups['mount_yaw'] = list(range(problem.mount_slice.start, problem.mount_slice.stop))
    if problem.forward: groups['forward_angle'] = [problem.npar - 1]
    return {k: v for k, v in groups.items() if v}


def decompose(J, weights, groups):
    """Exact all-orders allocation of lost squared contrast retention at one tangent.

    Joint nuisance spans overlap. Averaging marginal losses over every ordering avoids
    assigning the shared loss to whichever family happens to be projected first.
    This is algebraic attribution, not a causal estimate or a new acceptance policy.
    """
    names = list(groups)
    if sorted(itertools.chain.from_iterable(groups.values())) != list(range(3, J.shape[1])):
        raise ValueError('nuisance groups must partition all nuisance columns')
    reports = {}
    for mask in range(1 << len(names)):
        columns = [0, 1, 2] + [i for g, name in enumerate(names) if mask & (1 << g) for i in groups[name]]
        report = science_information(J[:, columns], weights)['report']
        reports[mask] = report
    full = reports[(1 << len(names)) - 1]
    allocations = {}
    for pair in full['model_contrast_information']:
        contributions = {}
        for i, name in enumerate(names):
            value = 0.
            for mask, report in reports.items():
                if mask & (1 << i): continue
                count = mask.bit_count()
                weight = math.factorial(count) * math.factorial(len(names) - count - 1) / math.factorial(len(names))
                before = report['model_contrast_information'][pair]['pre_cutoff_retained_fraction'] ** 2
                after = reports[mask | (1 << i)]['model_contrast_information'][pair]['pre_cutoff_retained_fraction'] ** 2
                if after > before + 1e-8: raise ValueError('projection loss is not monotone')
                value += weight * (before - after)
            contributions[name] = value
        total = 1. - full['model_contrast_information'][pair]['pre_cutoff_retained_fraction'] ** 2
        if not np.isclose(sum(contributions.values()), total, atol=1e-8):
            raise ValueError('attribution does not sum to full projection loss')
        allocations[pair] = dict(total_squared_retention_lost=total, all_order_attribution=contributions)
    return dict(full=full, without_nuisance=reports[0], attribution=allocations,
        leave_one_group_out={name:reports[((1 << len(names)) - 1) ^ (1 << i)] for i, name in enumerate(names)},
        group_alone={name:reports[1 << i] for i, name in enumerate(names)},
        projection_checks=len(reports))


def reconstruct(root, row):
    folder = root / 'diagnostics' / row['task_id']
    analysis = json.loads((folder / 'analysis.json').read_text())
    if analysis['temperature']['term_used']:
        raise ValueError('this pilot diagnostic requires an inactive temperature term')
    with np.load(folder / 'fit-input.npz', allow_pickle=False) as data: bins = dict(data)
    with np.load(folder / 'fit-rows.npz', allow_pickle=False) as data: saved = dict(data)
    tangent0 = np.cross(unit(bins['up_reference']), analysis['forward_axis']['axis_b'])
    tangent = np.einsum('nji,j->ni', bins['mount_matrices'][bins['epoch']], tangent0)
    problem = CandidateProblem(bins, bins['forward'], lambda _:np.zeros(3), np.ones(3),
        row['inference_policy']['settings'], forward_sigma_rad=analysis['forward_axis']['angle_sigma_rad'],
        forward_tangent=tangent)
    _, reconstructed = problem.prediction(saved['parameters'], True)
    if not np.allclose(reconstructed, saved['jacobian'], rtol=1e-10, atol=1e-14):
        raise ValueError('reconstructed Jacobian differs from saved fit')
    return problem, folder


def state_matrix(problem, state_id):
    parts = state_id.split('/')
    p = copy.copy(problem)
    if parts[0] != 'nominal':
        match = re.fullmatch(r'epoch-(\d+)-(-?1)', parts[0])
        if match is None: raise ValueError('unsupported mapping perturbation')
        epoch, sign = map(int, match.groups())
        p.fwd = np.broadcast_to(p.fwd, (len(p.bins['t']), 3)).copy()
        sel = p.bins['epoch'] == epoch
        u, f = unit(p.bins['up'][sel]), p.fwd[sel]
        angle = sign * np.radians(1.)
        p.fwd[sel] = f * np.cos(angle) + np.cross(u, f) * np.sin(angle) + u * (u * f).sum(axis=1)[:, None] * (1 - np.cos(angle))
        p.tangent = np.cross(p.bins['up'], p.fwd)
    nuisance_id = '/'.join(parts[1:-4])
    values = dict(nuisance_states(p))[nuisance_id]
    z = np.zeros(p.npar)
    z[:3] = models.EXPECTED_K[parts[-3]]
    z[p.p:p.p + p.nc] = values
    if parts[-1] != 'none': raise ValueError('unexpected mount state')
    if p.forward: z[-1] = float(parts[-4].removeprefix('forward-'))
    noise = float(parts[-2].removeprefix('noise-'))
    _, J = p.prediction(z, True)
    J, weights = p.observation_information(z, J, np.full(len(p.y), (RAD2DPH / noise) ** 2))
    return J, weights


def review(root):
    started = time.monotonic()
    root = root.resolve()
    campaign = json.loads((root / 'campaign.json').read_text())
    if implementation_hash() != campaign['implementation_hash']:
        raise ValueError('source differs from completed pilot')
    if campaign['execution']['completed'] != 3 or campaign['execution']['analysis_failures']:
        raise ValueError('requires completed three-case prefix without failures')
    cases, sources = [], [root / 'campaign.json']
    for row in campaign['records'][:2]:
        problem, folder = reconstruct(root, row)
        sources += [folder / n for n in ('analysis.json', 'fit-input.npz', 'fit-rows.npz')]
        groups = groups_for(problem)
        nominal_id = 'wind-0-0/tas-250.0' if problem.wind_tas is not None else 'wind-constant-0-0'
        nominal = [f'nominal/{nominal_id}/forward-0/{anchor}/noise-6/none' for anchor in models.EXPECTED_K]
        recorded = row['design_identifiability']['untruncated_contrasts']
        limiting = sorted({c['limiting_state'] for c in recorded.values()})
        zero_forward = [re.sub(r'/forward-[^/]+/', '/forward-0/', s) for s in limiting]
        checks = []
        for state in dict.fromkeys(nominal + limiting + zero_forward):
            J, w = state_matrix(problem, state)
            d = decompose(J, w, groups)
            for pair, original in recorded.items():
                if original['limiting_state'] == state and not np.isclose(
                    d['full']['model_contrast_information'][pair]['pre_cutoff_retained_fraction'],
                    original['retained_fraction'], rtol=1e-7, atol=1e-9):
                    raise ValueError('local check does not reproduce recorded limiting retention')
            checks.append(dict(state_id=state, nominal=state in nominal,
                               recorded_limiting=state in limiting, **d))
        cases.append(dict(task_index=row['task_index'], task_id=row['task_id'],
            crab_model=row['fit_options']['crab_model'], nuisance_groups=groups,
            gyro_rows=len(problem.y), speed_rows=len(problem.auxiliary(np.zeros(problem.npar))), checks=checks))
    # With no flagged mount boundaries, the third candidate's saved tangent is identical.
    one = root / 'diagnostics' / campaign['records'][1]['task_id'] / 'fit-rows.npz'
    two = root / 'diagnostics' / campaign['records'][2]['task_id'] / 'fit-rows.npz'
    with np.load(one, allow_pickle=False) as a, np.load(two, allow_pickle=False) as b:
        identical = all(np.array_equal(a[k], b[k]) for k in ('jacobian','parameters','bin_index'))
    if not identical: raise ValueError('third candidate differs; do not omit it from attribution')
    sources.append(two)
    return dict(scope='saved-bin local tangent attribution; no flights, fits, bootstrap or envelope search',
        implementation_hash=campaign['implementation_hash'], numerical_environment=numerical_environment(),
        numerical_environment_hash=numerical_environment_hash(),
        helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        cases=cases, third_candidate_saved_tangent_identical=identical,
        projection_checks=sum(c['projection_checks'] for case in cases for c in case['checks']),
        elapsed_s=time.monotonic() - started, authorized_additional_attempts=0,
        limitations=['Subset ablations and all-orders loss attribution are diagnostic, not proposed nuisance omissions.',
            'Nominal and recorded worst-retention states only, not the complete envelope or a new design guarantee.',
            'Recorded minimum information can occur at a different state than recorded minimum retention.',
            'Fixed design noise and saved geometry/forward axes; weights and science anchors do not use fitted gyro realization.',
            'No fitting priors used in projection; physical speed rows retained for every subset.',
            'Shrinking forward uncertainty changes envelope state range, not the local nuisance-column span.',
            'No acceptance, calibration, validation or production policy changed.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.directory)
    with args.output.open('x') as out: out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','input_sha256','numerical_environment','limitations')}))
