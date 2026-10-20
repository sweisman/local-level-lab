/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Test-only entry point to the unchanged C kernel's static local step.
 */
#include "../lll/ilvis0_native.c"

void lll_local_bound_value(const double *r,const double *v,const double *theta,const double *dv,
    double dt,const double *earth,const double *transport,double phi,double removal,double gravity,
    double *rn,double *vn) {
    local(r,v,theta,dv,dt,earth,transport,phi,removal,gravity,rn,vn);
}
