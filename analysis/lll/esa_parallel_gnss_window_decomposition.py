# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only decomposition of matched PPP differences over fixed windows."""

import json
import math
from pathlib import Path

from .esa_full_parallel_gnss import _sha

VERSION='esa-parallel-gnss-window-decomposition-v1'
SOURCE='docs/prediction-observed-development/parallel-gnss-120s-result.json'
PLAN='docs/prediction-observed-development/PARALLEL_GNSS_WINDOW_DECOMPOSITION_PLAN.md'


def _rank(values, fraction):
    if not values:
        raise ValueError('nonempty fast-window sample required')
    return sorted(values)[math.ceil(fraction*len(values))-1]


def summarize(source):
    windows=[row for row in source['windows'] if row['fast_window']]
    if (len(windows)!=source['fast_summary']['fast_windows']
            or sum(row['matched_epochs'] for row in windows)
            !=source['fast_summary']['matched_epochs']
            or len({row['window_id'] for row in windows})!=len(windows)):
        raise ValueError('saved fast-window inventory differs')
    offset_squares=[0.]*3
    centered_squares=[0.]*3
    means=[[],[],[]]
    centered=[[],[],[]]
    for row in windows:
        count=row['matched_epochs']
        if count<=0:
            raise ValueError('positive matched count required')
        values=row['time_adjusted']
        for axis in range(3):
            mean=float(values['mean'][axis])
            spread=float(values['centered_rms'][axis])
            rms=float(values['rms'][axis])
            if (not all(math.isfinite(v) for v in (mean,spread,rms))
                    or spread<0 or rms<0
                    or not math.isclose(mean*mean+spread*spread,rms*rms,
                                        rel_tol=1e-8,abs_tol=1e-12)):
                raise ValueError('window mean-square identity differs')
            offset_squares[axis]+=count*mean*mean
            centered_squares[axis]+=count*spread*spread
            means[axis].append(abs(mean))
            centered[axis].append(spread)
    return dict(fast_windows=len(windows),matched_epochs=sum(w['matched_epochs']
                for w in windows),
        offset_fraction_of_relative_mean_square=[
            a/(a+b) if a+b else None
            for a,b in zip(offset_squares,centered_squares,strict=True)],
        p95_absolute_window_mean_m=[_rank(v,.95) for v in means],
        p95_within_window_centered_rms_m=[_rank(v,.95) for v in centered])


def build(root):
    root=Path(root).resolve()
    saved=json.loads((root/SOURCE).read_bytes())
    if (saved.get('version')!='esa-parallel-gnss-120s-v1'
            or saved.get('protected_group_reads')!=0
            or saved.get('uses_imu') is not False
            or saved.get('uses_model_fits') is not False):
        raise ValueError('sealed receiver-only window result required')
    return dict(version=VERSION,source_sha256=_sha(root/SOURCE),
        plan_sha256=_sha(root/PLAN),code_sha256=_sha(Path(__file__)),
        sources=[dict(filename=row['filename'],source_sha256=row['source_sha256'],
                      **summarize(row)) for row in saved['sources']],
        original_reads=0,imu_reads=0,earth_model_fits=0,
        protected_group_reads=0,absolute_accuracy_established=False,
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh saved-only decomposition required')
    result=build(args.root)
    atomic(output,encoded(result))
    print([(row['filename'],row['offset_fraction_of_relative_mean_square'])
           for row in result['sources']])


if __name__=='__main__': main()
