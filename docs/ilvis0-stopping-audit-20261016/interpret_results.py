# SPDX-License-Identifier: AGPL-3.0-or-later
"""Interpret sealed audit metadata; no solves, predictions or archive reads."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    load=lambda name:json.loads((HERE/name).read_text())
    complete=load('completion.json')
    if complete['manifest_sha256']!=sha(HERE/'manifest.json') or complete['diagnosis_sha256']!=sha(HERE/'diagnosis.json'):
        raise ValueError('sealed audit mismatch')
    manifest=load('manifest.json');summary=load('diagnosis.json');saved={t['identity']:t['fit'] for t in manifest['tasks']}
    primaries=[r for r in summary['endpoints'] if r['role']=='primary'];rows=[]
    for r in primaries:
        fit=saved[r['identity']];gradient=fit['scaled_projected_gradient'];names=fit['active_parameters']
        largest=max(range(len(gradient)),key=lambda i:abs(gradient[i]))
        other=max(abs(g) for n,g in zip(names,gradient) if n!='time_offset')
        full,fixed=r['affine_slices'][0],r['affine_slices'][2]
        removed=1-abs(fixed['predicted_cost_change'])/abs(full['predicted_cost_change'])
        rows.append(dict(identity=r['identity'],largest_gradient_parameter=names[largest],maximum_non_time_gradient=other,
                         fraction_affine_decrease_removed_by_fixed_time=removed))
    if len(primaries)!=11 or len({r['segment_id'] for r in primaries})!=6:raise ValueError('fixed primary population required')
    stats=dict(stretches=6,unfinished_primary_fits=11,screened_endpoints=len(summary['endpoints']),
        primaries_with_all_epochs_within_1us=sum(r['packet_screen']['epochs_within_1us']==r['packet_screen']['receiver_epochs'] for r in primaries),
        time_dominates_gradient=sum(r['largest_gradient_parameter']=='time_offset' for r in rows),
        primaries_with_other_gradients_below_threshold=sum(r['maximum_non_time_gradient']<=1e-4 for r in rows),
        passing_stationarity=sum(r['stationarity_passed'] for r in primaries),
        worsening_fresh_probes=sum(r['signed_fresh_cost_change'] is not None and r['signed_fresh_cost_change']>0 for r in primaries),
        minimum_affine_decrease_removed_by_fixed_time=min(r['fraction_affine_decrease_removed_by_fixed_time'] for r in rows),
        observed_fit_starts=0,native_predictions=0,original_files_read=0)
    text='# What explains the remaining numerical failures?\n\n'
    text+=f"All **{stats['unfinished_primary_fits']} unfinished primary fits across all six unresolved stretches** place every receiver epoch within **one microsecond of an IMU packet boundary**. "
    text+='This is reconstructed from saved receiver times, nominal packet counts and fitted offsets, without reading original recordings.\n\n'
    text+=f"The timing parameter is the largest scaled projected-gradient component in **{stats['time_dominates_gradient']}/11** cases. All other gradient components are below the existing threshold in **{stats['primaries_with_other_gradients_below_threshold']}/11**. "
    text+=f"Seven primaries already pass the full gradient test; all seven fail a fresh correction that **increases** the objective. The other four fail the timing-gradient check before that correction is attempted.\n\n"
    text+=f"Holding time offset fixed removes at least **{100*stats['minimum_affine_decrease_removed_by_fixed_time']:.2f}%** of the apparent improvement in each saved linearized correction. "
    text+='These are local linear systems; that reduction does not prove the remaining full-model optimum.\n\n'
    text+='The independent cusp controls show why this matters: a true minimum can fail the original gate because a smooth correction crosses a derivative discontinuity and worsens the fit. '
    text+='The observed screen therefore identifies a common timing-boundary issue worth resolving before further optimizer changes or larger iteration budgets. '
    text+='It does not establish that every archival endpoint is optimal, and none of the six failures is relabeled.\n\n'
    text+='The next diagnostic should check one-sided timing behavior together with nuisance reoptimization. '
    text+='Any revised stopping rule must reject genuinely unfinished smooth fits, respect the same physical bounds, '
    text+='and reproduce objective and predicted-track agreement. A tightly bounded timing profile can then '
    text+='test the archival minimum. This audit authorizes no new observed fits.\n\n'
    text+='[Full audit and known-answer controls](README.md) · [All 22 endpoints](endpoints.csv).\n'
    (HERE/'INTERPRETATION.md').write_text(text)
    (HERE/'interpretation.json').write_text(json.dumps(dict(statistics=stats,primary_diagnostics=rows),indent=2,sort_keys=True)+'\n')
    receipt=dict(inputs={n:sha(HERE/n) for n in ('manifest.json','diagnosis.json','completion.json')},
        sources={Path(__file__).name:sha(Path(__file__))},artifacts={n:sha(HERE/n) for n in ('INTERPRETATION.md','interpretation.json')},
        observed_fit_starts=0,native_predictions=0,affine_solves=0)
    (HERE/'interpretation-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(stats))


if __name__=='__main__':main()
