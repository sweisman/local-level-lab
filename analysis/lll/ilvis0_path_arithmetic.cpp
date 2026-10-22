/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Outward third-order interval arithmetic. Not native execution-error bounds.
 */
#include "ilvis0_compiled_bounds.cpp"
#include <array>

namespace path_arithmetic {
using I=Interval;
struct Jet {std::array<I,4> d;};
I neg(I a){return {-a.hi,-a.lo};}
I sub(I a,I b){return plus(a,neg(b));}
I scale(I a,double b){return product(a,{b,b});}
I reciprocal(I a){
    if(a.lo<=0&&a.hi>=0)throw Unsupported{2};
    auto lower=[](double x){return x==1||x==-1?x:down(1/x);};
    auto upper=[](double x){return x==1||x==-1?x:up(1/x);};
    return {lower(a.hi),upper(a.lo)};
}
I divide(I a,I b){return product(a,reciprocal(b));}
I square(I a){
    I x=point_product(a.lo,a.lo),y=point_product(a.hi,a.hi);
    return {(a.lo<=0&&a.hi>=0)?0:std::max(0.,std::min(x.lo,y.lo)),std::max(x.hi,y.hi)};
}
Jet add(Jet a,Jet b){Jet r;for(int n=0;n<4;n++)r.d[n]=plus(a.d[n],b.d[n]);return r;}
Jet mul(Jet a,Jet b){
    const int choose[4][4]={{1,0,0,0},{1,1,0,0},{1,2,1,0},{1,3,3,1}};
    Jet r;for(int n=0;n<4;n++){
        r.d[n]={0,0};for(int k=0;k<=n;k++)r.d[n]=plus(r.d[n],scale(product(a.d[k],b.d[n-k]),choose[n][k]));
    }return r;
}
Jet inverse(Jet a){
    const int choose[4][4]={{1,0,0,0},{1,1,0,0},{1,2,1,0},{1,3,3,1}};
    Jet r;r.d[0]=reciprocal(a.d[0]);
    for(int n=1;n<4;n++){
        I sum{0,0};for(int k=1;k<=n;k++)sum=plus(sum,scale(product(a.d[k],r.d[n-k]),choose[n][k]));
        r.d[n]=neg(product(sum,r.d[0]));
    }return r;
}
double root_endpoint(double x,bool upper){
    // Normalize the exact binary input so square comparisons cannot underflow.
    // The sqrt call supplies only a guess; outward product checks certify it.
    int e=std::ilogb(x);if(e%2)e--;
    double m=std::scalbn(x,-e),r=std::sqrt(m);
    for(int k=0;k<8;k++){
        I sq=point_product(r,r);
        if(upper?sq.lo>=m:sq.hi<=m)return std::scalbn(r,e/2);
        r=upper?up(r):down(r);
    }
    throw Unsupported{3};
}
Jet root(Jet a){
    if(a.d[0].lo<=0)throw Unsupported{2};
    Jet r;r.d[0]={root_endpoint(a.d[0].lo,false),root_endpoint(a.d[0].hi,true)};
    I den=scale(r.d[0],2);
    r.d[1]=divide(a.d[1],den);
    r.d[2]=divide(sub(a.d[2],scale(square(r.d[1]),2)),den);
    r.d[3]=divide(sub(a.d[3],scale(product(r.d[1],r.d[2]),6)),den);
    return r;
}
I trig_value(I x,bool cosine){
    double m=std::max(std::fabs(x.lo),std::fabs(x.hi));if(m>8)throw Unsupported{2};
    std::array<I,42> fact;fact[0]={1,1};for(int n=1;n<42;n++)fact[n]=scale(fact[n-1],n);
    I result{0,0};for(int n=40;n>=0;n--){
        I coefficient{0,0};if(n%2==(cosine?0:1))coefficient=scale(reciprocal(fact[n]),(n/2)%2?-1:1);
        result=plus(product(result,x),coefficient);
    }
    I power{1,1};for(int n=0;n<41;n++)power=scale(power,m);
    double error=divide(power,fact[41]).hi;
    I padded=plus(result,{-error,error});return {std::max(-1.,padded.lo),std::min(1.,padded.hi)};
}
Jet trig(Jet a,bool cosine){
    I s=trig_value(a.d[0],false),c=trig_value(a.d[0],true),x1=a.d[1],x2=a.d[2],x3=a.d[3];
    I x11=square(x1),x111=product(x11,x1),x12=product(x1,x2);Jet r;
    if(!cosine){
        r.d[0]=s;r.d[1]=product(c,x1);r.d[2]=sub(product(c,x2),product(s,x11));
        r.d[3]=sub(sub(product(c,x3),scale(product(s,x12),3)),product(c,x111));
    }else{
        r.d[0]=c;r.d[1]=neg(product(s,x1));r.d[2]=neg(plus(product(s,x2),product(c,x11)));
        r.d[3]=plus(neg(plus(product(s,x3),scale(product(c,x12),3))),product(s,x111));
    }return r;
}
Jet read(const double *a){
    check(a,8);Jet r;for(int i=0;i<4;i++){
        if(a[2*i]>a[2*i+1])throw Unsupported{2};r.d[i]={a[2*i],a[2*i+1]};
    }return r;
}
}

extern "C" int ilvis0_path_arithmetic(int op,const double *a,const double *b,double *out){
    try{
        if(!runtime_ok())return 1;if(op<0||op>6)return 2;
        using namespace path_arithmetic;Jet x=read(a),r;
        if(op==0)r=add(x,read(b));else if(op==1)r=mul(x,read(b));
        else if(op==2)r=inverse(x);else if(op==3){r=mul(x,x);r.d[0]=square(x.d[0]);}
        else if(op==4)r=root(x);else r=trig(x,op==6);
        for(int i=0;i<4;i++){
            if(!std::isfinite(r.d[i].lo)||!std::isfinite(r.d[i].hi))return 3;
            out[2*i]=r.d[i].lo;out[2*i+1]=r.d[i].hi;
            if(out[2*i]>out[2*i+1])return 3;
        }return 0;
    }catch(Unsupported e){return e.code;}
}
