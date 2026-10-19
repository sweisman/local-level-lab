"""Render verified saved timing results; no original reads or native evaluations."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    done=json.loads((HERE/'completion.json').read_text())
    if done['manifest_sha256']!=sha(HERE/'manifest.json') or done['summary_sha256']!=sha(HERE/'summary.json'):
        raise ValueError('publication completion mismatch')
    receipt=json.loads((HERE/'evidence-receipt.json').read_text())
    for name,digest in receipt['artifacts'].items():
        if sha(HERE/name)!=digest:raise ValueError('changed publication artifact: '+name)
    s=json.loads((HERE/'summary.json').read_text());m=json.loads((HERE/'manifest.json').read_text())
    if s['native_evaluations']!=29 or s['optimizer_starts']!=0 or len(s['timing_derivative_checks'])!=5:
        raise ValueError('complete frozen diagnostic required')
    lines=['# Timing derivative and path results','',
        f"Completed **29 fixed evaluations in {s['elapsed_s']/60:.2f} minutes**, with zero optimizer starts. All primary and repeat centers reproduced exactly. No fit, repeat or scientific labels changed.",'',
        '## Independent timing derivatives','',
        'The analytic timing column is compared with symmetric one-microsecond residual differences. Errors below are relative vector-norm discrepancies, not statistical uncertainty. Distance to the nearest nominal integration boundary is reported separately.','',
        '| Processing / endpoint | Relative derivative error | Nearest clock boundary (µs) | Perturbation crosses boundary? |',
        '|---|---:|---:|---|']
    for r in s['timing_derivative_checks']:
        fields=r['identity'].split('::');case=fields[1].removeprefix('bias1_');label=('IMU8 control' if fields[0].startswith('b365') else case)+' / '+r['endpoint']
        lines.append(f"| {label} | {r['relative_residual_derivative_error']:.6g} | {r['nearest_nominal_clock_boundary_s']*1e6:.3f} | {'yes' if r['crosses_nominal_boundary'] else 'no'} |")
    lines+=['','## Full-vector path','',
        'Every nuisance coordinate moves together along the straight line between saved endpoints. These are fixed-point costs, not reoptimized timing-profile costs. The timing column gives its parameter value relative to the recorded receiver times.','',
        '| Fraction from primary to repeat | Timing (ms) | Unsubtracted cost | Profiled-removal cost |',
        '|---:|---:|---:|---:|']
    targets=[r for r in s['results'] if not r['is_control']]
    def point(row,k):
        method='center' if k==0 else 'repeat_center' if k==8 else 'path_'+str(k)
        return next(p for p in row['probes'] if p['method']==method)
    for k in range(9):
        a,b=[point(r,k) for r in targets]
        index=next(t['time_index'] for t in m['plan']['tasks'] if t['identity']==targets[0]['identity'])
        lines.append(f"| {k/8:.3f} | {a['point'][index]*.15*1000:.6f} | {a['cost']:.9f} | {b['cost']:.9f} |")
    errors=[r['relative_residual_derivative_error']*100 for r in s['timing_derivative_checks']]
    lines+=['','## Interpretation','',
        f"The five derivative comparisons differ by **{min(errors):.4f}–{max(errors):.4f}%** in vector norm. No perturbation crosses a nominal integration boundary. This finds no gross timing-derivative fault. It does not certify the accuracy of a nearly cancelled objective gradient or prove either endpoint is globally optimal.",'',
        'Both processing cases give almost identical sampled costs. The path rises from the primary toward the repeat, reaches a sampled high point just before the repeat, then falls slightly. This is consistent with distinct locally stationary solutions connected through coupled timing/calibration directions. The path was not reoptimized at intermediate times, so it is not a minimized timing profile.','',
        'No failed repeat passes from these points. The horizontal-only fits retain their large unscored height errors; the original full-position **53 globe / zero flat / zero unresolved** results are unchanged. The next task is known-answer qualification of a deterministic multi-start method before any new observed fits.','',
        '[Recovery qualification plan](NEXT_PLAN.md) · [All saved point metrics](README.md) · [Frozen scope](PLAN.md) · [Preceding diagnosis](../ilvis0-horizontal-repeat-probes-20261019/INTERPRETATION.md).']
    (HERE/'DIAGNOSIS.md').write_text('\n'.join(lines)+'\n')
    print('Verified and rendered 29 saved points /five derivative checks; no native calls.')


if __name__=='__main__':build()
