# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lossless engineering-value adapter for frozen generated recording controls.

The caller verifies the original artifact hash. This is not an aircraft-data
decoder, a training certificate or a unit/calibration conversion.
"""
from collections import Counter
from fractions import Fraction as F
import math
import re

MODELS=('sphere_rotating','sphere_still','flat_still')
VERSION='ilvis0-generated-recording-adapter-v1'


def _number(value):
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('finite literal generated measurement required')
    return float(value)


def _vector(value,length):
    if not isinstance(value,(list,tuple)) or len(value)!=length:
        raise ValueError('complete generated vector required')
    return [_number(v) for v in value]


def convert(source,*,profile,source_sha256,expected_packets=48000):
    required=('model','profile','packets','durations','starts','base_time','raw_theta','raw_dv',
        'limits','center','seed_coordinates','seed_velocity','seed_rotation','radius')
    if (not isinstance(source,dict) or any(k not in source for k in required)
            or type(profile) is not bool or type(source['profile']) is not bool
            or source['model'] not in MODELS or type(expected_packets) is not int
            or not 1<=expected_packets<=500000 or type(source['packets']) is not int
            or source['packets']!=expected_packets or not isinstance(source_sha256,str)
            or not re.fullmatch('[0-9a-f]{64}',source_sha256)):
        raise ValueError('complete recognized generated recording and declared processing required')
    n=expected_packets;dt=_vector(source['durations'],n);starts=_vector(source['starts'],n)
    if any(v<=0 for v in dt):raise ValueError('strictly positive original periods required')
    elapsed=0.
    for start,period in zip(starts,dt,strict=True):
        if start!=elapsed:raise ValueError('original sequential packet clock is inconsistent')
        elapsed+=period
    if _number(source['base_time'])!=elapsed:raise ValueError('original endpoint clock changed')
    theta=[_vector(row,3) for row in _vector_rows(source['raw_theta'],n)]
    dv=[_vector(row,3) for row in _vector_rows(source['raw_dv'],n)]
    limits=_vector(source['limits'],27);center=_vector(source['center'],27)
    if any(v<0 for v in limits) or any(abs(v)>1 for v in center):
        raise ValueError('original nonnegative limits and normalized center required')
    rotation=[_vector(row,3) for row in _vector_rows(source['seed_rotation'],3)]
    radius=_number(source['radius'])
    if radius<=0:raise ValueError('positive original coordinate radius required')
    configuration=dict(initial_c=_vector(source['seed_coordinates'],3),initial_v=_vector(source['seed_velocity'],3),
        initial_r=rotation,limits=limits,model=MODELS.index(source['model']),profile=profile,gravity=9.81,radius=radius)
    duration=sum((F(value)*count for value,count in Counter(dt).items()),F(0))
    return dict(configuration=configuration,theta=theta,dv=dv,dt=dt,center=center,
        provenance=dict(version=VERSION,scope='generated software controls',source_sha256=source_sha256,
            legacy_model=source['model'],original_profile=source['profile'],declared_profile=profile,
            processing_override=profile!=source['profile'],clock_offset_fixed=limits[25]==0.,
            original_endpoint_s=elapsed,exact_duration_s=str(duration),packets=n,
            units=dict(theta='radian increments',dv='metre/second increments',dt='seconds'),
            original_measurements_and_limits_preserved=True,training_certificate_transferred=False))


def _vector_rows(value,length):
    if not isinstance(value,(list,tuple)) or len(value)!=length:raise ValueError('complete original row count required')
    return value
