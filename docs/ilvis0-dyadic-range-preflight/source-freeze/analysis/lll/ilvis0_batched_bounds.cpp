/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Batch the existing component/global intersection without changing arithmetic.
 * The included primitive and all runtime/input guards remain unchanged.
 */
#include "ilvis0_compiled_bounds.cpp"

namespace {
void finish_bounds(size_t n,double *out) {
    for(size_t i=0;i<n;i++) {
        out[i]=std::min(out[i],out[2*n]);
        out[n+i]=std::min(out[n+i],out[2*n+1]);
    }
    out[2*n]=std::min(out[2*n],norm(out,n));
    out[2*n+1]=std::min(out[2*n+1],norm(out+n,n));
}
}

extern "C" int ilvis0_batched_finalize(size_t n,const double *d,const double *r,
    double gd,double gr,double *out) {
    try {
        if(!runtime_ok())return 1;if(n!=1&&n!=3)return 2;
        check(d,n,true);check(r,n,true);double globals[2]={gd,gr};check(globals,2,true);
        for(size_t i=0;i<n;i++){out[i]=d[i];out[n+i]=r[i];}
        out[2*n]=gd;out[2*n+1]=gr;finish_bounds(n,out);return 0;
    } catch(Unsupported e){return e.code;}
}

extern "C" int ilvis0_batched_vector(int op,size_t n,const double *a,const double *ad,const double *ar,const double *ag,
    const double *b,const double *bd,const double *br,const double *bg,const double *center,double *out) {
    int code=ilvis0_bounds_vector(op,n,a,ad,ar,ag,b,bd,br,bg,center,out);
    if(code)return code;
    try {finish_bounds(n,out);return 0;}catch(Unsupported e){return e.code;}
}
