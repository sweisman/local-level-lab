# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed six-case runtime acceptance, separate from scientific qualification."""
from fractions import Fraction as F
import math
from statistics import median


def assess(rows):
    rows=list(rows);identities=[(r.get('model'),r.get('profile')) for r in rows]
    complete=(len(rows)==6 and all(type(m) is int and type(p) is bool for m,p in identities)
        and set(identities)=={(m,p) for m in range(3) for p in (False,True)})
    ratios=[];all_matched=all(r.get('passed') is True and r.get('exact_report_match') is True for r in rows)
    for row in rows:
        if row.get('passed') is not True:continue
        values=[row.get(k) for k in ('candidate_s','predecessor_s')]
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values):
            raise ValueError('finite positive measured durations required')
        ratios.append(F(values[0])/F(values[1]))
    middle=median(ratios) if ratios else None
    maximum=max(ratios) if ratios else None
    useful=(len(ratios)==6 and middle<=F(95,100) and maximum<=F(110,100))
    return dict(qualified=complete and all_matched and useful,cases=len(rows),complete_matrix=complete,
        every_report_matched=all_matched,median_ratio=float(middle) if middle is not None else None,
        maximum_ratio=float(maximum) if maximum is not None else None,
        median_limit=.95,maximum_limit=1.10,observational_coverage_qualified=False,scientific_decision='abstain')
