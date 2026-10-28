# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compensated coordinate accumulation; original increments/equations retained."""
from pathlib import Path

VERSION='compensated-coordinate-tangent-v1'


def derive(source,*,expected_sha256):
    from lll.ilvis0_timing_arithmetic import derive as boundary
    text=boundary(source,expected_sha256=expected_sha256,right_at_lower=True).decode()
    helper='''
static void add_coordinate(Dual &value,Dual &carry,const Dual &increment) {
    Dual adjusted=increment-carry;
    Dual updated=value+adjusted;
    carry=(updated-value)-adjusted;
    value=updated;
}
'''
    replacements={
        'static void step_gravity(int model,Dual *c,Dual *v,Dual *r,const Dual *theta,const Dual *dv,':
            helper+'static void step_gravity(int model,Dual *c,Dual *carry,Dual *v,Dual *r,const Dual *theta,const Dual *dv,',
        'rates(model,c,v,radius,rate); for(int i=0;i<3;i++) middle[i]=c[i]+rate[i]*dt/2;':
            'Dual corrected[3];for(int i=0;i<3;i++)corrected[i]=c[i]-carry[i];\n'
            '    rates(model,corrected,v,radius,rate); for(int i=0;i<3;i++) middle[i]=corrected[i]+rate[i]*dt/2;',
        'for(int i=0;i<3;i++) c[i]+=rate[i]*dt;':
            'for(int i=0;i<3;i++) add_coordinate(c[i],carry[i],rate[i]*dt);',
        'step_gravity(model,c,v,r,theta,dv,dt,gravity,radius,removal,0,0.);':
            'Dual carry[3];step_gravity(model,c,carry,v,r,theta,dv,dt,gravity,radius,removal,0,0.);',
        'Dual p[27],c[3],v[3],r[9],lever[3],offset[3],rot[9];':
            'Dual p[27],c[3],carry[3],v[3],r[9],lever[3],offset[3],rot[9];',
        'rates(model,c,p+6,radius,offset);for(int i=0;i<3;i++)c[i]+=offset[i];':
            'rates(model,c,p+6,radius,offset);for(int i=0;i<3;i++)add_coordinate(c[i],carry[i],offset[i]);',
        'Dual oc[3],ov[3],orr[9],fraction=':
            'Dual oc[3],ocarry[3],ov[3],orr[9],fraction=',
        'memcpy(oc,c,sizeof c);memcpy(ov,v,sizeof v);memcpy(orr,r,sizeof r);':
            'memcpy(oc,c,sizeof c);memcpy(ocarry,carry,sizeof carry);memcpy(ov,v,sizeof v);memcpy(orr,r,sizeof r);',
        'step_gravity(model,oc,ov,orr,partial_th,partial_dv,':
            'step_gravity(model,oc,ocarry,ov,orr,partial_th,partial_dv,',
        'mv(orr,lever,ln);rates(model,oc,ln,radius,offset);':
            'Dual position[3];for(int i=0;i<3;i++)position[i]=oc[i]-ocarry[i];\n'
            '            mv(orr,lever,ln);rates(model,position,ln,radius,offset);',
        'Dual value=oc[i]+offset[i];':
            'Dual value=(oc[i]-ocarry[i])+offset[i];',
        'difference[3*j+i]=static_cast<double>(value.v-static_cast<long double>(observations[3*j+i]));':
            'difference[3*j+i]=static_cast<double>((oc[i].v-static_cast<long double>(observations[3*j+i]))-ocarry[i].v+offset[i].v);',
        'step_gravity(model,c,v,r,th,vel,dt[k],':
            'step_gravity(model,c,carry,v,r,th,vel,dt[k],',
    }
    for old,new in replacements.items():
        if text.count(old)!=1:raise ValueError('unsupported compensated coordinate layout: '+old)
        text=text.replace(old,new)
    return text.encode()


def load(directory,*,reserve_build,gravity_anchor_height_m=None,expected_source_sha256=None):
    from lll.native_tangent import load as native
    from lll.studies.artifacts import digest
    original=Path(__file__).with_name('ilvis0_tangent.cpp').read_bytes();sha=digest(original)
    raw=derive(original,expected_sha256=sha if expected_source_sha256 is None else expected_source_sha256)
    kernel,meta=native(directory,raw,prefix='coordinate-precision',expected_sha256=digest(raw),
        reserve_build=reserve_build,gravity_anchor_height_m=gravity_anchor_height_m)
    return kernel,dict(meta,version=VERSION,original_source_sha256=sha,
        coordinate_accumulation='compensated-all-three',residual='subtract-observation-before-restoring-carry-and-lever',
        right_branch_at_normalized_lower_bound=True,gravity_anchor_height_m=gravity_anchor_height_m,
        physical_equations_changed=False,raw_increments_changed=False,production_qualified=False)
