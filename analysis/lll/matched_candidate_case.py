# SPDX-License-Identifier: AGPL-3.0-or-later
"""Give three candidate fits one immutable generated measurement set."""

import copy
import re


MODELS=('sphere_rotating','sphere_still','flat_still')
REQUIRED=('fit.json','forecast.json','forecast-error-diagnostic.json',
          'bounded-physical.json','bounded-receiver.json',
          'receiver-forecast-error-diagnostic.json')


def _binding(material):
    import numpy as np
    from .studies.artifacts import digest,encoded
    arrays={}
    for name in ('theta','dv','dt','times'):
        array=np.asarray(material[name],dtype='<f8')
        arrays[name]=digest(array.tobytes())
    return dict(raw_array_sha256=arrays,
                earlier_receiver_sha256=digest(encoded(material['training_rows'])),
                same_measurements_for_all_candidates=True,
                later_receiver_positions_used=False)


def run(material,candidates,*,fit_candidate,save,open_later):
    import numpy as np
    if (tuple(candidates)!=MODELS or not isinstance(material,dict)
            or not callable(fit_candidate) or not callable(save)
            or not callable(open_later)):
        raise ValueError('exact three candidates and explicit lifecycle callbacks required')
    frozen=dict(material)
    for name in ('theta','dv','dt','times'):
        frozen[name]=np.array(material[name],dtype=float,copy=True)
        frozen[name].setflags(write=False)
    frozen['training_rows']=copy.deepcopy(material['training_rows'])
    n=len(frozen['dt']);t=frozen['times'];m=len(frozen['training_rows'])
    if (n<1 or frozen['theta'].shape!=(n,3) or frozen['dv'].shape!=(n,3)
            or t.ndim!=1 or not 2<=m<len(t)
            or any(not np.all(np.isfinite(frozen[k])) for k in ('theta','dv','dt','times'))
            or np.any(frozen['dt']<=0) or np.any(np.diff(t)<=0)):
        raise ValueError('complete finite generated measurements required')
    initial=_binding(frozen)
    save('input-binding.json',initial)
    results={}
    for model in MODELS:
        if _binding(frozen)!=initial:
            raise ValueError('candidate measurements changed before fitting')
        written=set()
        def candidate_save(name,value):
            if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',name)
                    or name in written):
                raise ValueError('unique safe candidate artifact required')
            if name in REQUIRED[2:]:
                target=('receiver_measurement' if name.startswith('receiver-')
                        or name=='bounded-receiver.json' else 'physical_position')
                if (not isinstance(value,dict)
                        or value.get('prediction_target')!=target
                        or value.get('later_observations_used') is not False):
                    raise ValueError('matched target and earlier-only artifact required')
                if (name.startswith('bounded-')
                        and value.get('nominal_joint_coverage_lower_bound',0)<.95):
                    raise ValueError('whole-path nominal allowance required')
            save('candidates/'+model+'/'+name,value)
            written.add(name)
        result=fit_candidate(model,frozen,candidate_save)
        if not set(REQUIRED)<=written:
            raise ValueError('complete candidate artifacts required before later truth')
        if _binding(frozen)!=initial:
            raise ValueError('candidate measurements changed during fitting')
        results[model]=result
    if _binding(frozen)!=initial:
        raise ValueError('candidate measurements changed before later truth')
    return dict(binding=initial,candidates=results,truth=open_later())
