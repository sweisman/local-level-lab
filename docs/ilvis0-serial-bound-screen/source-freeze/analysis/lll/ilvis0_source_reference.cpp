/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Source-only exposure of the unchanged native tangent primitives.
 * This does not execute geographic mechanization or fit observations.
 */
#include "ilvis0_tangent.cpp"

extern "C" int ilvis0_body_reference(size_t n,const double *theta,
    const double *dv,const double *dt,const double *initial_r,
    const double *limits,const double *point,double time,
    double *out,double *jacobian,size_t *packet,double *timing) {
    if(!n)return 1;
    Dual p[27],r[9],rotation[9],body[9],force[3];
    for(int j=0;j<27;j++){p[j]=point[j]*limits[j];p[j].d[j]=limits[j];}
    for(int i=0;i<9;i++){r[i]=initial_r[i];body[i]=(i%4==0);}
    exponential(p,rotation);mul(r,rotation,r);
    for(int i=0;i<3;i++)
        force[i]=(dv[i]-p[12+i]*dt[0])/(1+p[18+i])/dt[0];
    Dual query=time+p[25];double start=0.;bool found=false;
    if(!std::isfinite(query.v)||query.v<0)return 2;
    for(size_t k=0;k<n;k++) {
        double end=start+dt[k];bool partial=query.v<=end;
        Dual fraction=partial?(query-start)/dt[k]:Dual(1.);
        Dual angle[3],step_rotation[9];
        for(int i=0;i<3;i++)
            angle[i]=(theta[3*k+i]-p[9+i]*dt[k])/(1+p[15+i])*fraction;
        exponential(angle,step_rotation);mul(body,step_rotation,body);
        if(partial){*packet=k;timing[0]=query.v;timing[1]=start;timing[2]=end;found=true;break;}
        start=end;
    }
    if(!found)return 3;
    Dual departure[9],local[3],a[3],b[3];
    for(int i=0;i<9;i++)departure[i]=body[i]-(i%4==0);
    mv(r,force,a);mv(departure,force,local);mv(r,local,b);
    for(int s=0;s<2;s++)for(int axis=0;axis<3;axis++) {
        const Dual &v=s?b[axis]:a[axis];
        if(!std::isfinite(v.v))return 4;
        out[3*s+axis]=v.v;
        for(int j=0;j<27;j++)jacobian[(3*s+axis)*27+j]=v.d[j];
    }
    return 0;
}
