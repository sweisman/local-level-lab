# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preregistered observable flight envelopes; never inferred from accepted outcomes."""
import numpy as np

from .inference_policy import digest

VERSION = 'observable-flight-domain-1'
METRICS = ('latitude_min_deg', 'latitude_max_deg', 'speed_min_mps', 'speed_max_mps',
           'usable_minutes', 'elapsed_minutes', 'heading_span_deg', 'max_gap_seconds',
           'max_bin_seconds', 'n_bins', 'n_epochs')
SOURCES = {'binned_input', 'synthetic_gnss', 'recorded_gnss',
           'replay_observed_fixes', 'replay_simulated_high_rate'}


def descriptor(value):
    """Validate/canonicalize an explicit envelope, optionally verifying its identity."""
    if not isinstance(value, dict) or set(value)-{'version','sources','bounds','epoch_start_minutes','domain_id'}:
        raise ValueError('invalid flight domain descriptor')
    if value.get('version') != VERSION or not isinstance(value.get('bounds'),dict) or set(value['bounds']) != set(METRICS):
        raise ValueError('flight domain requires every observable bound and current version')
    sources = value.get('sources')
    if not isinstance(sources, list) or len(sources)!=1 or not all(isinstance(s,str) and s in SOURCES for s in sources):
        raise ValueError('flight domain requires exactly one known acquisition source; calibrate lanes separately')
    def interval(pair):
        if (not isinstance(pair, (list,tuple)) or len(pair)!=2 or
                any(isinstance(v,bool) or not isinstance(v,(int,float)) or not np.isfinite(v) for v in pair) or pair[0]>pair[1]):
            raise ValueError('flight domain bounds must be finite ordered intervals')
        return [float(v) for v in pair]
    bounds = {k: interval(value['bounds'][k]) for k in METRICS}
    for k, (lo,hi) in bounds.items():
        if k.startswith('latitude_'):
            if lo < -90 or hi > 90: raise ValueError('invalid domain latitude')
        elif lo < 0: raise ValueError('domain observables must be nonnegative')
    if bounds['heading_span_deg'][1] > 360: raise ValueError('invalid heading span')
    epochs = value.get('epoch_start_minutes')
    if not isinstance(epochs,list) or not epochs: raise ValueError('flight domain requires an explicit epoch schedule')
    epochs = [interval(p) for p in epochs]
    if epochs[0] != [0.,0.] or any(p[0]<0 for p in epochs) or any(a[1]>=b[0] for a,b in zip(epochs,epochs[1:])):
        raise ValueError('epoch schedule must start at zero and have disjoint ordered intervals')
    if bounds['n_epochs'] != [float(len(epochs))]*2: raise ValueError('epoch count differs from domain schedule')
    content = dict(version=VERSION,sources=sorted(set(sources)),bounds=bounds,epoch_start_minutes=epochs)
    identity = VERSION+'-'+digest(content)
    if value.get('domain_id',identity)!=identity: raise ValueError('flight domain identity mismatch')
    return {**content,'domain_id':identity}


def observables(bins, source='binned_input'):
    """Geometry of retained bins only. Neither gyro outcomes nor simulator truth is read."""
    try:
        t,dt,lat,vn,ve,epoch = [np.asarray(bins[k],float) for k in ('t','dt','lat','v_n','v_e','epoch')]
        n = len(t)
        if (n<1 or source not in SOURCES or any(v.shape!=(n,) or not np.isfinite(v).all() for v in (t,dt,lat,vn,ve,epoch))
                or np.any(np.diff(t)<=0) or np.any(dt<=0) or np.any(epoch<0) or np.any(epoch!=np.floor(epoch))
                or np.any(np.diff(epoch)<0) or np.any(abs(lat)>np.pi/2)):
            return None
        starts,ends = t-dt/2,t+dt/2
        # Bins represent integration intervals; overlapping bins cannot increase exposure.
        if np.any(starts[1:] < ends[:-1]-1e-6): return None
        speeds = np.hypot(vn,ve)
        course = np.sort(np.mod(np.degrees(np.arctan2(ve,vn)),360.))
        span = 360.-np.max(np.diff(np.r_[course,course[0]+360.]))
        epoch_starts = [float((starts[np.flatnonzero(epoch==e)[0]]-starts[0])/60) for e in np.unique(epoch)]
        return dict(version=VERSION,source=source,latitude_min_deg=float(np.degrees(lat.min())),
                    latitude_max_deg=float(np.degrees(lat.max())),speed_min_mps=float(speeds.min()),speed_max_mps=float(speeds.max()),
                    usable_minutes=float(dt.sum()/60),elapsed_minutes=float((ends[-1]-starts[0])/60),
                    heading_span_deg=float(span),max_gap_seconds=float(max(0.,np.max(starts[1:]-ends[:-1]) if n>1 else 0.)),
                    max_bin_seconds=float(dt.max()),n_bins=n,n_epochs=len(epoch_starts),epoch_start_minutes=epoch_starts)
    except (TypeError,KeyError,ValueError,IndexError):
        return None


def acquisition_source(manifest):
    replay=manifest.get('trajectory_replay')
    if replay: return 'replay_'+replay.get('mode','unknown')
    return 'synthetic_gnss' if 'synthetic' in manifest.get('quality',{}).get('flags',[]) else 'recorded_gnss'


def membership(domain, measured):
    domain = descriptor(domain)
    reasons = []
    if not isinstance(measured,dict) or measured.get('version') != VERSION:
        reasons.append('flight observables unavailable')
    else:
        if measured.get('source') not in domain['sources']: reasons.append('acquisition source outside calibrated domain')
        for key,(lo,hi) in domain['bounds'].items():
            v=measured.get(key)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not np.isfinite(v) or not lo<=v<=hi:
                reasons.append(key+' outside calibrated domain')
        times=measured.get('epoch_start_minutes')
        schedule=domain['epoch_start_minutes']
        if (not isinstance(times,list) or len(times)!=len(schedule) or any(
                isinstance(v,bool) or not isinstance(v,(int,float)) or not np.isfinite(v) or not lo<=v<=hi
                for v,(lo,hi) in zip(times or [],schedule))):
            reasons.append('IMU epoch timing outside calibrated domain')
    return dict(version=VERSION,requested_domain_id=domain['domain_id'],
                domain_id=domain['domain_id'] if not reasons else None,inside=not reasons,exclusions=reasons)


def resolve_domain(explicit, *policies):
    domains = [descriptor(p['flight_domain']) for p in policies if p and p.get('flight_domain') is not None]
    if explicit is not None: domains.append(descriptor(explicit))
    if domains and any(d!=domains[0] for d in domains): raise ValueError('flight domain differs between configuration and decision policies')
    return domains[0] if domains else None


def decision_exclusions(fit, policy):
    """Old offline policies remain readable, but cannot make flight decisions."""
    if not policy or policy.get('flight_domain') is None: return ['empirical flight policy has no observable domain']
    expected=membership(policy['flight_domain'],fit.get('domain_observables'))
    if fit.get('flight_domain') != descriptor(policy['flight_domain']) or fit.get('domain_membership') != expected or fit.get('domain_id') != expected['domain_id']:
        return ['flight domain binding missing or inconsistent']
    return expected['exclusions']


def check_policy_domain(policy):
    domain=descriptor(policy.get('flight_domain'))
    if policy.get('domain_id') != domain['domain_id']: raise ValueError('decision policy flight domain mismatch')
    return domain


def check_record_domain(row, domain):
    expected=membership(domain,row.get('domain_observables'))
    if row.get('domain_membership') != expected or row.get('domain_id') != expected['domain_id'] or row.get('flight_domain') != descriptor(domain):
        raise ValueError('campaign record flight domain mismatch')
