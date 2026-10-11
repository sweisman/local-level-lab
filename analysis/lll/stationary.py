# SPDX-License-Identifier: AGPL-3.0-or-later
"""Latitude-blind signed reversal diagnostic; no calibrated detection or flight fit."""
import numpy as np

RAD2DPH=np.degrees(1.)*3600.
POSITIONS='ABBAABBA'
PROTOCOL='stationary-reversal-v1'


def summarize(sess):
    result=dict(protocol=PROTOCOL,scientific_decision='abstain',latitude_used=False,
        signed_rate_dph=None,blocks=[],flags=[],uncertainty_status='not calibrated')
    if sess.manifest.get('stationary',{}).get('protocol')!=PROTOCOL:
        result['flags'].append('unsupported_stationary_protocol'); return result
    axis=sess.manifest.get('stationary',{}).get('axis')
    if axis not in ('x','y'):
        result['flags'].append('unknown_horizontal_axis'); return result
    expected=[f'ground.{p}.{i+1}' for i,p in enumerate(POSITIONS)]
    phases=[sess.phase(n) for n in expected]
    if any(p is None for p in phases):
        result['flags'].append('incomplete_reversal_sequence'); return result
    if any(b['start_ns']<a['end_ns'] for a,b in zip(phases,phases[1:])):
        result['flags'].append('overlapping_blocks'); return result
    for p,pos in zip(phases,POSITIONS):
        minutes=sess.manifest.get('stationary',{}).get('block_minutes')
        if minutes is not None and p.get('still_s',0)<minutes*60:
            result['flags'].append('incomplete_still_block'); break
        start,end=p['start_ns']+30_000_000_000,p['end_ns']-30_000_000_000
        g=sess.slice('gyro',start,end); a=sess.slice('accel',start,end)
        if (g is None or a is None or len(g['t_ns'])<10 or len(a['t_ns'])<10
            or end-start<30_000_000_000):
            result['flags'].append('insufficient_settled_data'); break
        dt=np.diff(g['t_ns']); accel_dt=np.diff(a['t_ns'])
        values=np.column_stack([a[k] for k in ('x','y','z')])
        rates=np.column_stack([g[k] for k in ('x','y','z')])
        if (not np.isfinite(values).all() or not np.isfinite(rates).all()
            or np.any(dt<=0) or np.any(dt>2_000_000_000)
            or np.any(accel_dt<=0) or np.any(accel_dt>2_000_000_000)
            or any(s['t_ns'][0]-start>2_000_000_000 or end-s['t_ns'][-1]>2_000_000_000 for s in (g,a))):
            result['flags'].append('invalid_or_gapped_block'); break
        gravity=values.mean(axis=0); norm=np.linalg.norm(gravity)
        if (norm<8.5 or norm>11. or gravity[2]/norm<np.cos(np.deg2rad(5.))
            or np.linalg.norm(values.std(axis=0))>.06):
            result['flags'].append('block_not_level_and_still'); break
        result['blocks'].append(dict(name=p['name'],position=pos,samples=len(rates),
            midpoint_s=float(g['t_ns'].astype(float).mean()/1e9),
            mean_rate_dph=float(np.mean(g[axis])*RAD2DPH)))
    if result['flags']: return result
    t=np.array([b['midpoint_s'] for b in result['blocks']]); t=(t-t.mean())/3600.
    sign=np.array([1. if p=='A' else -1. for p in POSITIONS])
    design=np.column_stack([np.ones(len(t)),t,sign])
    y=np.array([b['mean_rate_dph'] for b in result['blocks']])
    beta,_,rank,_=np.linalg.lstsq(design,y,rcond=None)
    if rank!=3:
        result['flags'].append('offset_and_reversal_not_separable'); return result
    result.update(axis=axis,signed_rate_dph=float(beta[2]),constant_offset_dph=float(beta[0]),
        linear_offset_change_dph_per_hour=float(beta[1]),
        block_residual_rms_dph=float(np.sqrt(np.mean((y-design@beta)**2))),
        method='equal block weights; constant offset, linear offset change, signed A/B rate',
        limitations='Nonlinear drift, thermal effects, alignment and correlated noise remain uncalibrated.')
    return result
