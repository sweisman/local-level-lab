# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict metadata handling for compatible deterministic remainder reports.

Artifact integrity and identical maps are necessary, not proof of provider
qualification. Callers must establish mathematical validity, input provenance
and a common error specification before using a merged report. This module
performs no integration, fitting, support solve or scientific decision.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re

VERSION='ilvis0-compatible-bound-report-reuse-v1'
COMMON_FIELDS=('version','time_s','center','physical_parameter_count','enclosure_parameter_count',
    'normalized_center','lower','upper','bound_lower','bound_upper','source_id','reference_binding',
    'shared_binding','acceleration_binding','transform_binding','previous_coefficients',
    'acceleration_coefficients','transform_coefficients','previous_caps','acceleration_caps',
    'retained_acceleration_remainder','transform_reference','conditioning','source_initial_padding')
HEX=re.compile(r'[0-9a-f]{64}')
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,199}')


def _pairs(items):
    out={}
    for key,value in items:
        if key in out:raise ValueError('duplicate JSON field')
        out[key]=value
    return out


def _finite_tree(value):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('nonfinite report value')
    if isinstance(value,dict):
        for item in value.values():_finite_tree(item)
    elif isinstance(value,list):
        for item in value:_finite_tree(item)


def _number(value,*,nonnegative=False):
    try:valid=type(value) in (int,float) and math.isfinite(value) and (not nonnegative or value>=0)
    except (OverflowError,TypeError):valid=False
    if not valid:raise ValueError('finite numeric report value required')


def _vector(value,length,*,nonnegative=False):
    if not isinstance(value,list) or len(value)!=length:raise ValueError('complete report vector required')
    for item in value:_number(item,nonnegative=nonnegative)


def _decode(blob):
    try:out=json.loads(blob,object_pairs_hook=_pairs)
    except (UnicodeDecodeError,json.JSONDecodeError,RecursionError) as error:
        raise ValueError('supported JSON report required') from error
    if not isinstance(out,dict) or any(key not in out for key in COMMON_FIELDS+('unshared_remainder',)):
        raise ValueError('complete bound report required')
    _finite_tree(out)
    if (type(out['physical_parameter_count']) is not int or out['physical_parameter_count']!=27
            or type(out['enclosure_parameter_count']) is not int or out['enclosure_parameter_count']!=51):
        raise ValueError('all 27 physical and 51 expression columns required')
    for key in ('version','source_id','reference_binding','shared_binding','acceleration_binding','transform_binding'):
        if not isinstance(out[key],str) or not out[key]:raise ValueError('complete report binding required')
    _number(out['time_s']);_number(out['retained_acceleration_remainder'],nonnegative=True)
    _vector(out['center'],3);_vector(out['unshared_remainder'],3,nonnegative=True)
    for key in ('normalized_center','lower','upper','bound_lower','bound_upper'):_vector(out[key],27)
    for lo,hi,z,outer_lo,outer_hi in zip(*(out[k] for k in
            ('lower','upper','normalized_center','bound_lower','bound_upper')),strict=True):
        if lo>hi or outer_lo>min(lo,z) or outer_hi<max(hi,z):
            raise ValueError('ordered domain and reference hull required')
    for key,columns in (('previous_coefficients',6),('acceleration_coefficients',9),('transform_coefficients',9)):
        matrix=out[key]
        if not isinstance(matrix,list) or len(matrix)!=3:raise ValueError('three complete coefficient rows required')
        for row in matrix:_vector(row,columns)
    _vector(out['previous_caps'],6,nonnegative=True);_vector(out['acceleration_caps'],9,nonnegative=True)
    if (out.get('scientific_decision')!='abstain' or out.get('observational_coverage_qualified') is not False
            or out.get('floating_point_enclosure_verified') is not False):
        raise ValueError('research report with explicit unresolved coverage required')
    return out


@dataclass(frozen=True)
class Provider:
    name:str
    environment_sha256:str
    sha256:str
    document:bytes

    def __post_init__(self):
        if (not isinstance(self.name,str) or not NAME.fullmatch(self.name)
                or not isinstance(self.environment_sha256,str) or not HEX.fullmatch(self.environment_sha256)
                or not isinstance(self.sha256,str) or not HEX.fullmatch(self.sha256)
                or not isinstance(self.document,bytes) or not 0<len(self.document)<=1048576
                or hashlib.sha256(self.document).hexdigest()!=self.sha256):
            raise ValueError('bounded owned report bytes and matching identity hashes required')
        _decode(self.document)

    @classmethod
    def from_file(cls,name,path,*,sha256,environment_sha256):
        return cls(name,environment_sha256,sha256,Path(path).read_bytes())


def merge_reports(providers):
    providers=tuple(providers)
    if (not 1<=len(providers)<=16 or not all(isinstance(p,Provider) for p in providers)
            or len({p.name for p in providers})!=len(providers)):
        raise ValueError('bounded distinct report providers required')
    providers=tuple(sorted(providers,key=lambda p:p.name))
    if len({p.environment_sha256 for p in providers})!=1:raise ValueError('provider environment mismatch')
    reports=[_decode(p.document) for p in providers];base=reports[0]
    for report in reports[1:]:
        different=[key for key in COMMON_FIELDS if report[key]!=base[key]]
        if different:raise ValueError('provider map/domain/assumption mismatch: '+', '.join(different))
    result=deepcopy(base);chosen=[];remainders=[]
    for axis in range(3):
        index=min(range(len(reports)),key=lambda j:(reports[j]['unshared_remainder'][axis],providers[j].name))
        remainders.append(reports[index]['unshared_remainder'][axis]);chosen.append(providers[index].name)
    result['unshared_remainder']=remainders
    for key in ('position_unshared_remainder','force_unshared_remainder','lever_unshared_remainder',
                'acceleration_clock_remainder','force_center_difference'):
        result.pop(key,None)
    result['native_candidate_version']=VERSION
    result['certificate_reuse']=dict(version=VERSION,environment_sha256=providers[0].environment_sha256,
        providers=[dict(name=p.name,sha256=p.sha256) for p in providers],coordinate_providers=chosen,
        provider_qualification_required=True,decomposition_available=False)
    result.update(scientific_decision='abstain',observational_coverage_qualified=False,
        floating_point_enclosure_verified=False)
    return result
