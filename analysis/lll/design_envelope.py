# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite, preregistered nuisance-state design checks; never fitted residual weights."""
import copy
import itertools
import numpy as np

from . import models
from .calib import RAD2DPH
from .policy import CANDIDATE_POLICY

ENVELOPE_ASSUMPTIONS = dict(version='nuisance-envelope-1', anchors=list(models.EXPECTED_K),
    sigma_bin_dph=[3., 6.], prior_multiplier=3., planning_forward_sigma_deg=5.,
    epoch_yaw_deg=1., nuisance_state='dynamic intercept/drift grid or wind coefficient corners and individual drifts',
    weighting='fixed isotropic design noise; no fitted gyro coefficients or residual weights',
    limitations='Finite development grid, not a bound over every admissible nuisance trajectory')


def nuisance_states(problem):
    if problem.nc == 0: return [('no-crab', np.zeros(0))]
    amplitude = 3*np.radians(problem.settings.get('crab_sigma_deg', 5.))
    rate = 3*np.radians(problem.settings['crab_rate_sigma_dph'])/3600.
    center = np.mean(problem.knots) if problem.knots is not None else np.mean(problem.bins['t'])
    times = problem.knots if problem.knots is not None else np.full(problem.nc, center)
    states = []
    if problem.settings['crab_model'] == 'wind':
        for a, b in itertools.product((-1, 0, 1), repeat=2):
            states.append((f'wind-constant-{a}-{b}', np.tile([a*amplitude, b*amplitude], len(times))))
        for axis, sign in itertools.product((0, 1), (-1, 1)):
            values = np.zeros((len(times), 2)); values[:, axis] = sign*rate*(times-center)
            states.append((f'wind-drift-{axis}-{sign}', values.ravel()))
    else:
        for a, b in itertools.product((-1, 0, 1), repeat=2):
            states.append((f'crab-{a}-{b}', a*amplitude+b*rate*(times-center)))
    return states


def envelope_size(problem):
    epochs = len(np.unique(problem.bins.get('epoch', [0])))
    return len(models.EXPECTED_K)*len(nuisance_states(problem))*3*(1+2*epochs)


def envelope_information(problem):
    from .inference import science_information
    epochs = np.asarray(problem.bins.get('epoch', np.zeros(len(problem.bins['t']), int)))
    variations = [('nominal', None, 0.)]+[(f'epoch-{e}-{sign}', e, sign*np.radians(1.))
            for e in np.unique(epochs) for sign in (-1, 1)]
    sigma = problem.forward_sigma if problem.forward_sigma is not None else np.radians(5.)
    weights = np.full(len(problem.y), (RAD2DPH/6.)**2)
    states, anchors, worst, pre = [], {}, {}, {}
    for mapping_id, epoch, angle in variations:
        p = copy.copy(problem)
        if epoch is not None and p.fwd is not None:
            p.fwd = np.broadcast_to(p.fwd, (len(epochs), 3)).copy()
            sel = epochs == epoch
            u = np.asarray(p.bins['up'])[sel]; u = u/np.linalg.norm(u, axis=1)[:, None]
            f = p.fwd[sel]
            p.fwd[sel] = f*np.cos(angle)+np.cross(u, f)*np.sin(angle)+u*(u*f).sum(axis=1)[:, None]*(1-np.cos(angle))
            p.tangent = np.cross(p.bins['up'], p.fwd)
        for nuisance_id, values in nuisance_states(p):
            for forward in (-3*sigma, 0., 3*sigma):
                for anchor, coefficients in models.EXPECTED_K.items():
                    z = np.zeros(p.npar); z[:3] = coefficients
                    z[p.p:p.p+p.nc] = values
                    if p.forward: z[-1] = forward
                    _, jac = p.prediction(z, True)
                    report = science_information(jac, weights)['report']
                    state_id = f'{mapping_id}/{nuisance_id}/forward-{forward:.9g}/{anchor}'
                    states.append(dict(state_id=state_id, anchor=anchor, rank=report['estimable_rank'],
                        minimum_retention=min(c['retained_fraction'] for c in report['model_contrast_information'].values())))
                    # Anchors retain the most limiting complete state for rank diagnostics.
                    if anchor not in anchors or states[-1]['minimum_retention'] < anchors[anchor]['minimum_retention']:
                        anchors[anchor] = dict(report=report, minimum_retention=states[-1]['minimum_retention'], state_id=state_id)
                    for name, value in report['model_contrast_information'].items():
                        for destination, field, info in ((worst, 'retained_fraction', 'information'),
                                                        (pre, 'pre_cutoff_retained_fraction', 'pre_cutoff_information')):
                            old = destination.get(name)
                            retention, information = value[field], value[info]
                            if old is None:
                                destination[name] = dict(retained_fraction=retention, information=information,
                                    estimable=retention >= CANDIDATE_POLICY['retention_threshold'], limiting_state=state_id)
                            else:
                                old['information'] = min(old['information'], information)
                                if retention < old['retained_fraction']:
                                    old.update(retained_fraction=retention, limiting_state=state_id)
                                old['estimable'] &= retention >= CANDIDATE_POLICY['retention_threshold']
    return dict(assumptions=copy.deepcopy(ENVELOPE_ASSUMPTIONS), uses_gyro_realization=False,
        conditioning='retained bins and supplied forward/mount axes; preprocessing may use gyro',
        rank_threshold=CANDIDATE_POLICY['retention_threshold'],
        estimable_rank=min(v['rank'] for v in states), anchors={a: v['report'] for a,v in anchors.items()},
        model_contrast_information=worst, untruncated_contrasts=pre, states=states,
        envelope_configuration=dict(crab_sigma_deg=problem.settings.get('crab_sigma_deg',5.),
            crab_rate_sigma_dph=problem.settings['crab_rate_sigma_dph'],
            crab_knot_seconds=problem.settings['crab_knot_seconds'], forward_sigma_rad=sigma,
            evaluated_noise_dph=6., information_at_3dph_multiplier=4.),
        svd_evaluations=len(states))
