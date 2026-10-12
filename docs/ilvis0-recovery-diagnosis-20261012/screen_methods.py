# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small fixed software screen; no decoding, original reads, or observed fits."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

import numpy
import scipy
import platform

from lll import ilvis0_recovery_screen as screen

GUIDE = Path(__file__).resolve().parent
ROOT = GUIDE.parents[1]


def render(result):
    rows = result['results']
    counts = {v: sum(r['passed'] for r in rows if r['variant'] == v) for v in screen.VARIANTS}
    lines = []
    for name in screen.NAMES:
        values = [sum(r['passed'] for r in rows if r['variant'] == v and r['control'] == name)
                  for v in screen.VARIANTS]
        lines.append(f'| {name} | {values[0]}/3 | {values[1]}/3 |')
    failed = [r for r in rows if not r['passed']]
    detail = '\n'.join(f"- `{r['identity']}`: {r['evaluations']} evaluations; "
                       f"known answer {'passed' if r['known_answer_passed'] else 'failed'}; "
                       f"final checks {'passed' if r['converged'] else 'failed'}; "
                       f"{r['probe']['reason']}." for r in failed) or 'No software failures.'
    text = f'''# Bounded-method software screen

This compares two actual optimization strategies on **60 small software starts**:
TRF (the completed trial's method) and dogbox (a rectangular trust-region method).
It reads no archival observations and performs no native integrations. Both use
the same original parameter box, Jacobian scaling, 600-evaluation ceiling, fresh
gradient check and unchanged cost/residual stability checks.

| Known-answer control | TRF | Dogbox |
|---|---:|---:|
{chr(10).join(lines)}
| **Total** | **{counts['trf']}/30** | **{counts['dogbox']}/30** |

Each control has three predetermined starts. The last two controls have 27 coupled
parameters, a 100-million-to-one singular-value ratio, and a near-boundary start.
Known prediction and objective recovery are checked separately from numerical
termination. Unique parameters are checked only where the equations identify them.
Both strategies call the real SciPy optimizer; temporary dispatch leaves the
completed trial's source unchanged.

## Failed software checks

{detail}

## What this establishes

This is a screen, **not qualification for the airborne archive**. The controls
demonstrate behavior on specified equations, not the cause of a particular saved
flight's stall. Complete observed Jacobians and rejected-step traces were not saved
in the recovery trial. A new observed diagnostic needs a separate source freeze
and finite allowance. Neither a successful software test nor an unused completed
allowance permits replaying the 41 unfinished stretches.

Run `screen_methods.py --render-only` to regenerate this page from saved results.
Running it without that flag performs this small software screen again; it never
starts archival fits. Input/source/environment hashes are in the screen receipt.
'''
    (GUIDE/'METHOD_SCREEN.md').write_text(text)
    return counts


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--render-only', action='store_true')
    args = parser.parse_args()
    output = GUIDE/'method-screen.json'
    if args.render_only:
        result = json.loads(output.read_text())
    else:
        if output.exists():
            raise ValueError('software screen already saved; use --render-only')
        result = screen.run()
        result['environment'] = dict(python=platform.python_version(), numpy=numpy.__version__,
                                     scipy=scipy.__version__)
        output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    counts = render(result)
    sources = [Path(__file__), ROOT/'analysis/lll/ilvis0_recovery_screen.py',
               ROOT/'analysis/tests/test_ilvis0_recovery_screen.py']
    sources.extend(ROOT/'analysis/lll'/name for name in (
        'ilvis0_solver_controls.py', 'ilvis0_solver_screen.py', 'ilvis0_solver_recovery.py',
        'ilvis0_solver_refinement.py', 'ilvis0_solver_verified_stop.py'))
    receipt = dict(sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sources}, artifacts={n: hashlib.sha256((GUIDE/n).read_bytes()).hexdigest()
                            for n in ('METHOD_SCREEN.md', 'method-screen.json')},
                   observed_fit_starts=0, native_predictions=0)
    (GUIDE/'screen-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(passed=counts, starts=len(result['results']), observed_fit_starts=0)))


if __name__ == '__main__':
    main()
