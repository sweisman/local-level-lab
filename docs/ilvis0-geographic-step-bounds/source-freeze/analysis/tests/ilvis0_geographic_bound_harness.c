/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Test-only full-step/antenna entry point; original kernel remains unchanged.
 */
#include "../lll/ilvis0_native.c"

void lll_geographic_bound_value(int model,const double *input,double *output) {
    double *c=output,*v=output+3,*r=output+6;
    const double *theta=input+15,*dv=input+18,*lever=input+21;
    double period=input[24],gravity=input[25],radius=input[26],removal=input[27];
    memcpy(c,input,3*sizeof(double));memcpy(v,input+3,3*sizeof(double));memcpy(r,input+6,9*sizeof(double));
    step(model,c,v,r,theta,dv,period,gravity,radius,removal);
    double local_lever[3],offset[3];mv(r,lever,local_lever);rates(model,c,local_lever,radius,offset);
    for(int i=0;i<3;i++)output[15+i]=c[i]+offset[i];
}
