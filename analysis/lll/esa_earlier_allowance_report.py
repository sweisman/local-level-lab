# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate the existing complete ESA cover at smaller earlier error allowances."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
from pathlib import Path


RESULT = 'docs/prediction-observed-development/esa-earlier-allowance-sensitivity.json'
SURVIVOR_SHA = '20daae58ec852916eefb5d5617bc08ed7e2d1286e98ad8de4d74157d991ad61d'
GAMMAS = (0.,.02,.05,.1)


def slope(direction):
    from .ilvis0_exact_scale import sqrt_upper

    return F(0) if direction is None else F(sqrt_upper(sum(F(v)**2 for v in direction)))


def report(root):
    from .esa_attitude_cover_score import GAMMA
    from .esa_attitude_refinement_score import ID as REFINEMENT
    from .esa_attitude_survivor_score import ID as SURVIVOR
    from .ilvis0_saved_prediction_audit import endpoint
    from .studies.closed import ClosedStudy

    models = []
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root,'data/'+SURVIVOR)))
        refined = stack.enter_context(closing(ClosedStudy(root,'data/'+REFINEMENT,store=study.store)))
        cover = study.input('cover')
        if (study.completion['manifest_sha256']!=SURVIVOR_SHA
                or refined.completion['manifest_sha256']!=cover['manifest_sha256']
                or max(GAMMAS)!=GAMMA):
            raise ValueError('exact saved cover and original error allowance required')
        for group in cover['rows']:
            model = group['model']
            regions = []
            for row in group['rows']:
                parent,child = row['parent_index'],row['cell_index']
                identity = f'{model}-{parent}-{child}'
                caps = [(F(row['upper']),F(0))]
                exclusion = None
                if row['upper']>group['nominal_separation']/2:
                    earlier = study.input(identity+'-feasibility')['trials'][-1]
                    exclusion = F(earlier['exact_upper']),slope(earlier['direction'])
                    cell = refined.artifact(f'{model}-{parent}',f'cell-{child}.json')
                    ancestor = refined.input(f'{model}-range-{parent}')
                    caps.extend([(F(cell['proposed_exact']),slope(cell['proposal_direction'])),
                                 (F(cell['reused_exact']),slope(ancestor['proposal_direction']))])
                    if identity in study.rows and study.rows[identity]['passed']:
                        survivor = study.artifact(identity,'survivor-support.json')
                        caps.append((F(survivor['upper']),F(0)))
                        caps.extend((F(t['exact_upper']),slope(t['direction'])) for t in survivor['trials'])
                regions.append((identity,caps,exclusion))

            rows = []
            for gamma in GAMMAS:
                shift = F(gamma)-F(GAMMA)
                kept, removed = [], []
                for identity,caps,exclusion in regions:
                    if exclusion is not None and exclusion[0]+shift*exclusion[1]<0:
                        removed.append(identity)
                    else:
                        kept.append((min(base+shift*rate for base,rate in caps),identity))
                upper, identity = max(kept)
                rows.append(dict(earlier_unshared=gamma,upper=endpoint(upper,True),
                                 largest_range=identity,excluded_ranges=removed))
            models.append(dict(model=model,nominal_separation=group['nominal_separation'],rows=rows))
    return dict(rows=models,manifest_sha256=SURVIVOR_SHA,new_bound_calls=0,new_fits=0,
                scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded

    root = Path.cwd()
    raw = encoded(report(root))
    _write_equal(root/RESULT,raw)
    print(digest(raw))
