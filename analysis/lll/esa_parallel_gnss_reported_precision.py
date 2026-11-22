# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive PPP disagreement divided by summed reported variance."""

import json
import math
from pathlib import Path

from .esa_full_parallel_gnss import AIR1, BASE, INVENTORY, _sha
from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
from .esa_parallel_gnss import MATCH_TOLERANCE_S, match_times
from .esa_parallel_gnss_time import corrected_neu
from .esa_parallel_gnss_120s import FULL, window_id
from .esa_ppp_acquisition import TARGETS, verify_complete
from .esa_receiver_sequence_wrap import records_with_sequence_wrap

VERSION='esa-parallel-gnss-reported-precision-v1'
WINDOWS='docs/prediction-observed-development/parallel-gnss-120s-result.json'
PLAN='docs/prediction-observed-development/PARALLEL_GNSS_REPORTED_PRECISION_PLAN.md'


def ratios(reference, other, adjusted):
    a=reference['position_variance_m2']
    b=other['position_variance_m2']
    if len(a)!=3 or len(b)!=3 or len(adjusted)!=3:
        raise ValueError('complete three-axis reported variance required')
    denominators=[]
    for x,y,difference in zip(a,b,adjusted,strict=True):
        if (not all(math.isfinite(float(v)) for v in (x,y,difference))
                or x<=0 or y<=0):
            raise ValueError('positive finite original reported variances required')
        denominators.append(math.sqrt(x+y))
    return ([difference/scale for difference,scale in zip(adjusted,denominators)],
            denominators)


def _nearest_rank(values, fraction):
    if not values:
        raise ValueError('nonempty descriptive sample required')
    return sorted(values)[math.ceil(fraction*len(values))-1]


def summarize(reference, matched, saved):
    if not isinstance(saved,list) or not saved:
        raise ValueError('complete saved 120-second windows required')
    expected={row['window_id']:row['matched_epochs']
              for row in saved if row['fast_window']}
    if len(expected)!=sum(row['fast_window'] for row in saved):
        raise ValueError('unique saved fast windows required')
    bins={key:[] for key in expected}
    previous=-1
    for index, other in matched:
        if type(index) is not int or index<=previous or index>=len(reference):
            raise ValueError('unique ordered reference match required')
        previous=index
        row=reference[index]
        if abs(other['time_s']-row['time_s'])>MATCH_TOLERANCE_S:
            raise ValueError('matched times exceed frozen tolerance')
        key=window_id(row['time_s'])
        if key in bins:
            _, adjusted=corrected_neu(row,other)
            scaled,denominator=ratios(row,other,adjusted)
            bins[key].append((adjusted,scaled,denominator))
    if any(len(bins[key])!=count for key,count in expected.items()):
        raise ValueError('saved fast-window pair counts differ')
    all_pairs=[pair for rows in bins.values() for pair in rows]
    if not all_pairs:
        raise ValueError('no fast-window PPP pairs')
    absolute=[[abs(pair[1][axis]) for pair in all_pairs] for axis in range(3)]
    windows=[]
    for key,rows in sorted(bins.items()):
        windows.append(dict(window_id=key,matched_epochs=len(rows),
            mean_difference_m=[math.fsum(row[0][axis] for row in rows)/len(rows)
                               for axis in range(3)],
            mean_summed_reported_std_m=[math.fsum(row[2][axis] for row in rows)/len(rows)
                                       for axis in range(3)]))
    return dict(fast_windows=len(windows),matched_epochs=len(all_pairs),
        median_absolute_ratio=[_nearest_rank(a,.5) for a in absolute],
        p95_absolute_ratio=[_nearest_rank(a,.95) for a in absolute],
        maximum_absolute_ratio=[max(a) for a in absolute],
        fraction_absolute_ratio_over_three=[sum(v>3 for v in a)/len(a)
                                            for a in absolute],
        windows=windows)


def build(root):
    from .airquantumgrav_receiver import records
    root=Path(root).resolve()
    inventory=json.loads((root/INVENTORY).read_bytes())
    saved=json.loads((root/WINDOWS).read_bytes())
    full=json.loads((root/FULL).read_bytes())
    if (inventory.get('source_file')!=AIR1 or inventory.get('epochs')!=64080
            or saved.get('version')!='esa-parallel-gnss-120s-v1'
            or saved.get('reference_sha256')!=inventory.get('sha256')
            or saved.get('full_result_sha256')!=_sha(root/FULL)
            or saved.get('protected_group_reads')!=0):
        raise ValueError('unchanged opened receiver and fixed-window audit required')
    air1=root/BASE/AIR1
    if _sha(air1)!=inventory['sha256']:
        raise ValueError('air1 source hash differs')
    with air1.open() as stream:
        reference=list(records(stream))
    sources=[]
    for name,size in TARGETS.items():
        path=root/BASE/name
        receipt=json.loads((root/BASE/(name+'.receipt.json')).read_bytes())
        source_sha=verify_complete(path,size,receipt)
        original=next(row for row in saved['sources'] if row['filename']==name)
        full_source=next(row for row in full['sources'] if row['filename']==name)
        if source_sha!=original['source_sha256']:
            raise ValueError('other PPP source hash differs')
        sequence_audit={}
        with path.open() as stream:
            parsed=records_with_sequence_wrap(stream,
                expected_rollovers=EXPECTED_ROLLOVERS[name],audit=sequence_audit)
            matched=match_times(reference,parsed)
            for _ in parsed:
                pass
        if (len(matched)!=original['matched_epochs']
                or sequence_audit!=full_source['sequence_audit']):
            raise ValueError('full matched-pair count or sequence audit differs')
        result=summarize(reference,matched,original['windows'])
        if (result['fast_windows']!=original['fast_summary']['fast_windows']
                or result['matched_epochs']!=original['fast_summary']['matched_epochs']):
            raise ValueError('fast-window count differs from saved audit')
        sources.append(dict(filename=name,source_sha256=source_sha,
                            sequence_audit=sequence_audit,**result))
    return dict(version=VERSION,plan_sha256=_sha(root/PLAN),
        code_sha256=_sha(Path(__file__)),window_result_sha256=_sha(root/WINDOWS),
        reference_sha256=inventory['sha256'],sources=sources,
        variance_reference='sum of each export\'s original reported axis variance',
        receiver_independence_assumed=False,absolute_accuracy_established=False,
        imu_reads=0,receiver_original_reads=3,protected_group_reads=0,
        earth_model_fits=0,scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh reported-precision audit required')
    result=build(args.root)
    atomic(output,encoded(result))
    print([(row['filename'],row['matched_epochs'],row['p95_absolute_ratio'])
           for row in result['sources']])


if __name__=='__main__':main()
