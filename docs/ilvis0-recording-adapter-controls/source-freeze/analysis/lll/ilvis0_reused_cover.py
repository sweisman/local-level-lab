# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete-cover bookkeeping; partial fresh unions are never used.

Callers must verify inherited coverage, region proofs and coordinate-frame
provenance. Flags and matching identifiers alone do not prove those facts.
No model decision or calibrated uncertainty is supplied here.
"""
import math
import re


def _range(row):
    lo=row.get('lower');hi=row.get('upper')
    if (not isinstance(lo,list) or not isinstance(hi,list) or len(lo)!=3 or len(hi)!=3
            or any(type(v) not in (int,float) or not math.isfinite(v) for v in lo+hi)
            or any(a>b for a,b in zip(lo,hi,strict=True))):
        raise ValueError('three finite ordered coordinate intervals required')
    return lo,hi


def combine(inherited,regions,*,expected_regions):
    if (type(expected_regions) is not int or not 1<=expected_regions<=32
            or expected_regions&(expected_regions-1) or inherited.get('complete') is not True
            or not isinstance(inherited.get('case_id'),str) or not inherited['case_id']
            or not isinstance(inherited.get('frame_sha256'),str)
            or not re.fullmatch('[0-9a-f]{64}',inherited['frame_sha256'])):
        raise ValueError('complete inherited range and an explicit supported cover required')
    old_lo,old_hi=_range(inherited);regions=list(regions)
    if len(regions)>expected_regions:raise ValueError('too many cover members')
    seen=set();kept=[];excluded=0
    for row in regions:
        index=row.get('region_id')
        if (type(index) is not int or not 0<=index<expected_regions or index in seen
                or row.get('case_id')!=inherited['case_id'] or row.get('frame_sha256')!=inherited['frame_sha256']
                or type(row.get('passed')) is not bool):
            raise ValueError('unique matching case/frame/region identities required')
        seen.add(index)
        if row['passed']:
            if type(row.get('excluded')) is not bool:raise ValueError('explicit region exclusion state required')
            if row['excluded']:excluded+=1
            else:kept.append(_range(row))
    complete=len(seen)==expected_regions and all(row['passed'] for row in regions)
    result=dict(case_id=inherited['case_id'],frame_sha256=inherited['frame_sha256'],
        inherited_complete=True,fresh_complete=complete,combined_complete=True,
        completed_regions=sum(row['passed'] for row in regions),expected_regions=expected_regions,
        excluded_regions=excluded,lower=list(old_lo),upper=list(old_hi),fresh_lower=None,fresh_upper=None,
        mode='inherited-only',region_proofs_required=True,observational_coverage_qualified=False,
        scientific_decision='abstain')
    if not complete:return result
    if not kept:raise ValueError('no nonempty fresh region; separate infeasibility handling required')
    fresh_lo=[min(pair[0][axis] for pair in kept) for axis in range(3)]
    fresh_hi=[max(pair[1][axis] for pair in kept) for axis in range(3)]
    lo=[max(a,b) for a,b in zip(old_lo,fresh_lo,strict=True)]
    hi=[min(a,b) for a,b in zip(old_hi,fresh_hi,strict=True)]
    if any(a>b for a,b in zip(lo,hi,strict=True)):raise ValueError('complete inherited/fresh ranges disagree')
    result.update(lower=lo,upper=hi,fresh_lower=fresh_lo,fresh_upper=fresh_hi,mode='complete-intersection')
    return result
