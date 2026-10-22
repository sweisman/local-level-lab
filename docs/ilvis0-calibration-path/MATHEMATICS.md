# Calibrated increments along a parameter path

For a fixed recorded increment r and positive packet duration t, let
b(s)=b₀+s db and g(s)=g₀+s dg. Write a₀=r−t b₀, c₀=1+g₀ and D=c₀+s dg.
The native calibration expression is

\[
q(s)=\frac{a_0-st\,db}{D}.
\]

After cancellation, its first derivative has numerator
N=−t db c₀−dg a₀, independent of s. Therefore

\[
q'=N/D^2,\qquad q''=-2dg\,N/D^3,\qquad
q'''=6(dg)^2N/D^4.
\]

The implementation evaluates exact rational interval enclosures for supplied
direction boxes and a subinterval of [0,1]. It requires the complete denominator
range to stay positive. It cancels the common product before bounding it.

On one stable packet branch the partial fraction is affine, u(s)=u₀+u₁s.
For the partial increment, the derivative of order n is

\[
(uq)^{(n)}=u q^{(n)}+n u_1q^{(n-1)},\qquad n=1,2,3.
\]

The partial duration has derivatives tu, tu₁, 0, 0. A range for u extending
outside [0,1] is rejected, rather than clipped or silently moved to another
packet. Exact endpoints are retained and binary outputs are rounded outward.

These formulas bound packet calibration/partial timing only. Rotation,
velocity, position, frame transforms, derivative jumps and whole-program
roundoff still require a qualified native implementation.
