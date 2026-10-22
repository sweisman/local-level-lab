# SPDX-License-Identifier: AGPL-3.0-or-later
"""Continue the existing generated recipe; never extend aircraft measurements."""
from copy import deepcopy
from fractions import Fraction as F
import math
import re

import numpy as np

from .ilvis0_legacy_recording import VERSION as PARENT_VERSION


def extend(source,*,packets,clock_offset_s,parent_sha256):
    """Create owned eight-minute-capable inputs with an explicit clock limit.

    The caller verifies the supplied parent artifact hash before using its data.
    Prefix agreement is checked bitwise. This prepares generated fixtures only;
    it supplies neither training observations nor an uncertainty certificate.
    """
    if (type(packets) is not int or not 48000<packets<=500000
            or type(clock_offset_s) not in (int,float) or not math.isfinite(clock_offset_s)
            or clock_offset_s<0. or not isinstance(parent_sha256,str)
            or not re.fullmatch('[0-9a-f]{64}',parent_sha256)
            or source.get('provenance',{}).get('version')!=PARENT_VERSION
            or source['provenance'].get('scope')!='generated software controls'):
        raise ValueError('recognized generated parent, explicit extension size/hash and nonnegative clock required')
    config=source['configuration']; limits=config['limits']; center=source['center']
    if (len(limits)!=27 or len(center)!=27 or limits[25]!=0.
            or any(type(v) not in (int,float) or not math.isfinite(v) or v<0. for v in limits)
            or any(v!=0. for v in center) or type(config['model']) is not int
            or config['model'] not in (0,1,2) or type(config['profile']) is not bool):
        raise ValueError('complete original fixed-clock, zero-center configuration required')
    t=np.arange(packets)*.005
    theta=.005*np.column_stack((2e-5+3e-4*np.sin(.03*t),-3e-5+2e-4*np.cos(.02*t),
                                1e-5+5e-4*np.sin(.01*t)))
    dv=.005*np.column_stack((.02*np.sin(.05*t),.02*np.cos(.04*t),-9.81+.01*np.sin(.03*t)))
    dt=np.full(packets,.005)
    for name,value in (('theta',theta),('dv',dv),('dt',dt)):
        parent=np.asarray(source[name],dtype='<f8')
        if (parent.shape!=value[:48000].shape or not np.all(np.isfinite(parent))
                or parent.tobytes()!=value[:48000].astype('<f8',copy=False).tobytes()):
            raise ValueError('original generated prefix does not match the declared recipe')
    new_config=deepcopy(config); new_config['limits'][25]=float(clock_offset_s)
    return dict(configuration=new_config,theta=theta.tolist(),dv=dv.tolist(),dt=dt.tolist(),center=list(center),
        provenance=dict(version='ilvis0-generated-duration-extension-v1',scope='generated software controls',
            parent_case_sha256=parent_sha256,parent_legacy_source_sha256=source['provenance']['source_sha256'],
            preserved_prefix_packets=48000,generated_suffix_packets=packets-48000,packets=packets,
            clock_offset_fixed=clock_offset_s==0.,parent_clock_limit_s=0.,declared_clock_limit_s=float(clock_offset_s),
            nonclock_configuration_preserved=True,original_prefix_bitwise_preserved=True,
            nominal_duration_s=packets*.005,sequential_endpoint_s=float(np.cumsum(dt)[-1]),
            exact_duration_s=str(F(.005)*packets),units=deepcopy(source['provenance']['units']),
            training_certificate_transferred=False,future_observations_used=False,
            independent_physics_validation=False,observational_coverage_qualified=False))
