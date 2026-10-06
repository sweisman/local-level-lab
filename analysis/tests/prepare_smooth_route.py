# SPDX-License-Identifier: AGPL-3.0-or-later
"""Write an explicit smoother latent route and geometry diagnostics, never a flight campaign."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'analysis'), str(ROOT/'analysis'/'tests')]

import numpy as np
from audit_roll_proxy import knot_bank_jumps
from lll.models import G0
from lll.research_design import implementation_hash
from lll.trajectory import TrackReplay, smooth_track_spec


def metrics(replay, t):
    values = replay.sample(t)
    support = replay.support(t)
    bank = np.arctan(values['speed']*values['psi_dot']/G0)
    roll = np.diff(bank)/np.diff(t)
    good_roll = support[:-1] & support[1:]
    jumps = knot_bank_jumps(replay)
    def bounds(values):
        finite = np.asarray(values)[np.isfinite(values)]
        return None if not len(finite) else [float(finite.min()), float(finite.max())]
    return dict(supported_samples=int(support.sum()),
                ground_speed_mps=bounds(values['speed']),
                vertical_speed_mps=bounds(values['vz']),
                bank_deg=bounds(np.degrees(bank)),
                scalar_roll_rate_dps=bounds(np.degrees(roll[good_roll])),
                max_absolute_one_sided_bank_jump_deg=max((abs(e['jump_deg']) for e in jumps), default=0.),
                bank_jumps_over_one_degree=sum(abs(e['jump_deg']) > 1 for e in jumps))


def prepare(source, output):
    spec = json.loads(source.read_text())
    smooth = smooth_track_spec(spec)
    original, alternative = TrackReplay(spec), TrackReplay(smooth)
    t = np.arange(0., original.duration, .05)
    np.testing.assert_array_equal(original.support(t), alternative.support(t))
    for _, _, curves in alternative.blocks:
        knots = curves[0].x
        expected = original.sample(knots)
        actual = alternative.sample(knots)
        for name in ('lat', 'lon', 'h'):
            np.testing.assert_allclose(actual[name], expected[name], rtol=1e-12, atol=1e-12)
    review = dict(scope='20 Hz latent-path geometry only; no synthesized flight, science fit or search',
                  original_trajectory_hash=spec['trajectory_hash'],
                  alternative_trajectory_hash=smooth['trajectory_hash'],
                  current_implementation_hash=implementation_hash(),
                  position_knots_preserved=True, gap_support_preserved=True,
                  original=metrics(original,t), alternative=metrics(alternative,t),
                  authorized_attempts=0,
                  assumptions='Natural endpoint curvature and between-fix motion are unmeasured. C2 continuity avoids bank steps but does not guarantee physical motion, accuracy or science eligibility.')
    with output.open('x') as out:
        out.write(json.dumps(smooth, indent=2, allow_nan=False)+'\n')
    with output.with_name('smooth-route-review.json').open('x') as out:
        out.write(json.dumps(review, indent=2, allow_nan=False)+'\n')
    return review


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), allow_nan=False))
