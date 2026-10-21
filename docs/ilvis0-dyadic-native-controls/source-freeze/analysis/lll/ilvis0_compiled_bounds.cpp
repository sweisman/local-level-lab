/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Outward binary64 bounds for small, supplied affine-error certificates.
 * Does not certify the entire mechanization or any observation-error model.
 */
#include <algorithm>
#include <cfenv>
#include <cmath>
#include <cstddef>
#include <limits>
#ifdef __SSE__
#include <xmmintrin.h>
#endif

namespace {
struct Unsupported {int code;};
const double inf=std::numeric_limits<double>::infinity();
bool runtime_ok() {
    if(!std::numeric_limits<double>::is_iec559||sizeof(double)!=8||std::fegetround()!=FE_TONEAREST)return false;
#ifdef __SSE__
    if(_mm_getcsr()&((1u<<15)|(1u<<6)))return false; // FTZ / denormals-are-zero
#endif
    volatile double normal=std::numeric_limits<double>::min();
    volatile double half=normal*.5;
    return half>0.&&std::nextafter(0.,1.)==std::numeric_limits<double>::denorm_min();
}
double finite(double x){if(!std::isfinite(x))throw Unsupported{3};return x;}
double up(double x){return finite(std::nextafter(finite(x),inf));}
double down(double x){return finite(std::nextafter(finite(x),-inf));}
double add_up(double a,double b){if(a==0)return b;if(b==0)return a;return up(a+b);}
double mul_up(double a,double b){if(a==0||b==0)return 0;if(a==1)return b;if(b==1)return a;return up(a*b);}
double div_up(double a,double b){if(a==0)return 0;if(a==b)return 1;return up(a/b);}
double error_up(double a,double b){return a==b?0.:up(std::fabs(a-b));}
void check(const double *a,size_t n,bool positive=false){
    for(size_t i=0;i<n;i++)if(!std::isfinite(a[i])||(positive&&a[i]<0))throw Unsupported{2};
}
struct Interval{double lo,hi;};
double add_lo(double a,double b){if(a==0)return b;if(b==0)return a;if(a==-b)return 0;return down(a+b);}
double add_hi(double a,double b){if(a==0)return b;if(b==0)return a;if(a==-b)return 0;return up(a+b);}
Interval plus(Interval a,Interval b){return {add_lo(a.lo,b.lo),add_hi(a.hi,b.hi)};}
Interval point_product(double a,double b){
    if(a==0||b==0)return {0,0};
    if(a==1)return {b,b};if(b==1)return {a,a};
    if(a==-1)return {-b,-b};if(b==-1)return {-a,-a};
    double p=finite(a*b);return {down(p),up(p)};
}
Interval product(Interval a,Interval b){
    Interval out{inf,-inf};
    for(double x:{a.lo,a.hi})for(double y:{b.lo,b.hi}){
        Interval p=point_product(x,y);out.lo=std::min(out.lo,p.lo);out.hi=std::max(out.hi,p.hi);
    }
    return out;
}
double radius(double center,Interval exact){return std::max(error_up(center,exact.lo),error_up(center,exact.hi));}
double sqrt_normal_up(double x){
    // Callers normalize so 1<=x<=approximately 9. The FMA residual cannot
    // underflow here: its sign checks whether the rounded root is already up.
    double r=std::sqrt(x),residual=std::fma(r,r,-x);
    return residual<0?up(r):r;
}
double norm(const double *a,size_t n){
    double maximum=0;size_t nonzero=0;
    for(size_t i=0;i<n;i++){maximum=std::max(maximum,std::fabs(a[i]));nonzero+=a[i]!=0;}
    if(!maximum||nonzero==1)return maximum;
    double sum=0;
    for(size_t i=0;i<n;i++){double ratio=div_up(std::fabs(a[i]),maximum);sum=add_up(sum,mul_up(ratio,ratio));}
    return mul_up(maximum,sqrt_normal_up(sum));
}
double matrix_norm(const double *a){
    double maximum=0;for(int i=0;i<9;i++)maximum=std::max(maximum,std::fabs(a[i]));
    if(maximum==0)return 0;
    Interval scaled[9],gram[9];
    for(int i=0;i<9;i++){
        if(a[i]==0)scaled[i]={0,0};
        else if(std::fabs(a[i])==maximum){double s=a[i]>0?1.:-1.;scaled[i]={s,s};}
        else {double q=a[i]/maximum;scaled[i]={down(q),up(q)};}
    }
    double trace=0,rows=0;
    for(int i=0;i<3;i++)for(int j=0;j<3;j++){
        Interval g{0,0};for(int k=0;k<3;k++)g=plus(g,product(scaled[3*k+i],scaled[3*k+j]));
        gram[3*i+j]=g;if(i==j)trace=add_up(trace,std::max(0.,g.hi));
    }
    for(int i=0;i<3;i++){
        double row=0;for(int j=0;j<3;j++)row=add_up(row,std::max(std::fabs(gram[3*i+j].lo),std::fabs(gram[3*i+j].hi)));
        rows=std::max(rows,row);
    }
    return mul_up(maximum,sqrt_normal_up(std::min(trace,rows)));
}
double change_product(double x,double y,double dx,double dy){
    return add_up(add_up(mul_up(std::fabs(x),dy),mul_up(std::fabs(y),dx)),mul_up(dx,dy));
}
double remainder_product(double x,double y,double dx,double dy,double rx,double ry){
    return add_up(add_up(mul_up(std::fabs(x),ry),mul_up(std::fabs(y),rx)),mul_up(dx,dy));
}
}

extern "C" int ilvis0_bounds_runtime_ok(){return runtime_ok();}
extern "C" int ilvis0_bounds_positive(int op,double a,double b,double *out){
    try{if(!runtime_ok())return 1;double values[2]={a,b};check(values,2,true);
        if(op!=0&&op!=1)return 2;*out=op?mul_up(a,b):add_up(a,b);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_bounds_norm(size_t n,const double *a,double *out){
    try{if(!runtime_ok())return 1;if(n<1||n>9)return 2;check(a,n);*out=norm(a,n);return 0;}catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_bounds_matrix_norm(const double *a,double *out){
    try{if(!runtime_ok())return 1;check(a,9);*out=matrix_norm(a);return 0;}catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_bounds_vector(int op,size_t n,const double *a,const double *ad,const double *ar,const double *ag,
    const double *b,const double *bd,const double *br,const double *bg,const double *center,double *out){
    try{
        if(!runtime_ok())return 1;if(op<0||op>5||(n!=1&&n!=3)||(op>=2&&n!=3))return 2;
        size_t an=op>=4?9:(op==2?1:n),bn=op==1?1:n;
        check(a,an);check(ad,an,true);check(ar,an,true);check(ag,3,true);
        check(b,bn);check(bd,bn,true);check(br,bn,true);check(bg,3,true);check(center,n);
        double errors[3]={0,0,0},gd=0,gr=0;
        for(size_t i=0;i<n;i++){
            double d=0,r=0;Interval exact{0,0};
            if(op==0){d=add_up(ad[i],bd[i]);r=add_up(ar[i],br[i]);exact=plus({a[i],a[i]},{b[i],b[i]});}
            else if(op==1){d=mul_up(std::fabs(b[0]),ad[i]);r=mul_up(std::fabs(b[0]),ar[i]);exact=point_product(a[i],b[0]);}
            else if(op==2){d=change_product(a[0],b[i],ad[0],bd[i]);r=remainder_product(a[0],b[i],ad[0],bd[i],ar[0],br[i]);exact=point_product(a[0],b[i]);}
            else if(op==3){
                size_t j=(i+1)%3,k=(i+2)%3;
                d=add_up(change_product(a[j],b[k],ad[j],bd[k]),change_product(a[k],b[j],ad[k],bd[j]));
                r=add_up(remainder_product(a[j],b[k],ad[j],bd[k],ar[j],br[k]),remainder_product(a[k],b[j],ad[k],bd[j],ar[k],br[j]));
                Interval other=point_product(a[k],b[j]);exact=plus(point_product(a[j],b[k]),{-other.hi,-other.lo});
            }else for(size_t k=0;k<3;k++){
                size_t j=3*i+k;d=add_up(d,change_product(a[j],b[k],ad[j],bd[k]));
                r=add_up(r,remainder_product(a[j],b[k],ad[j],bd[k],ar[j],br[k]));exact=plus(exact,point_product(a[j],b[k]));
            }
            errors[i]=radius(center[i],exact);out[i]=add_up(d,errors[i]);out[n+i]=add_up(r,errors[i]);
        }
        if(op==0){gd=add_up(ag[0],bg[0]);gr=add_up(ag[1],bg[1]);}
        else if(op==1){gd=mul_up(std::fabs(b[0]),ag[0]);gr=mul_up(std::fabs(b[0]),ag[1]);}
        else if(op==2||op==3){
            double na=norm(a,an),nb=norm(b,bn);
            gd=add_up(add_up(mul_up(na,bg[0]),mul_up(nb,ag[0])),mul_up(ag[0],bg[0]));
            gr=add_up(add_up(mul_up(na,bg[1]),mul_up(nb,ag[1])),mul_up(ag[0],bg[0]));
        }else{
            double nb=norm(b,3);gd=add_up(mul_up(ag[2],bg[0]),mul_up(nb,ag[0]));
            if(op==5)gd=add_up(gd,mul_up(ag[0],bg[0]));
            gr=add_up(add_up(mul_up(ag[2],bg[1]),mul_up(nb,ag[1])),mul_up(ag[0],bg[0]));
        }
        double error=norm(errors,n);out[2*n]=add_up(gd,error);out[2*n+1]=add_up(gr,error);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_bounds_matrix(int op,const double *a,const double *ag,const double *b,const double *bg,
    const double *center,double *out){
    try{
        if(!runtime_ok())return 1;if(op<0||op>2)return 2;
        check(a,9);check(b,9);check(ag,3,true);check(bg,3,true);check(center,9);double errors[9];
        for(int i=0;i<3;i++)for(int j=0;j<3;j++){
            Interval exact{0,0};int index=3*i+j;
            if(op==0)exact=plus({a[index],a[index]},{b[index],b[index]});
            else for(int k=0;k<3;k++)exact=plus(exact,point_product(a[3*i+k],b[3*k+j]));
            errors[index]=radius(center[index],exact);
        }
        double d=add_up(ag[0],bg[0]),r=add_up(ag[1],bg[1]);
        if(op==1||op==2){
            d=add_up(add_up(mul_up(ag[2],bg[0]),mul_up(bg[2],ag[0])),mul_up(ag[0],bg[0]));
            r=add_up(add_up(mul_up(ag[2],bg[1]),mul_up(bg[2],ag[1])),mul_up(ag[0],bg[0]));
        }
        if(op==2)d=std::min(add_up(mul_up(ag[2],bg[0]),ag[0]),add_up(mul_up(bg[2],ag[0]),bg[0]));
        double error=norm(errors,9);out[0]=add_up(d,error);out[1]=add_up(r,error);
        if(op==2)out[0]=std::min(out[0],add_up(1.,std::max(1.,matrix_norm(center))));
        return 0;
    }catch(Unsupported e){return e.code;}
}
