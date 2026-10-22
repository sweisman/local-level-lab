# Piecewise endpoint-average error

Let a continuous residual r have derivative h on a complete partition of
[0,1]. Assume h is twice continuously differentiable inside each segment,
with one-sided values and slopes at the interior nodes. Let

\[
K(s)=\frac{s(1-s)}2.
\]

Integration by parts on each segment gives

\[
\int_0^1 h(s)\,ds-\frac{h(0)+h(1)}2
=-\sum_i\int_{a_i}^{a_{i+1}}K(s)h''(s)\,ds
-\sum_c K(c)[h']_c+\sum_c K'(c)[h]_c.
\]

If M bounds |h''| on each segment and B bounds the absolute jumps, an
axis-wise error radius is

\[
E=\sum_i M_i\int_{a_i}^{a_{i+1}}K(s)\,ds
+\sum_c K(c)B_{h',c}+\sum_c |K'(c)|B_{h,c}.
\]

The integral weights use the exact primitive s²/4−s³/6. The component combines
this radius with explicit intervals for r(0), h(0) and h(1), using rational
arithmetic before outward conversion to binary endpoints.

For the residual-source diagnostic, h is the derivative of the error left
after the retained source expression. A native packet-clock boundary can
change h or h′. Their jumps therefore require bounds; a packet-boundary flag
alone does not supply them. All actual boundaries must be included.

The component proves arithmetic under supplied assumptions. It does not verify
that a native partition is complete, that the native residual is continuous,
or that its derivative/jump bounds are valid. It cannot qualify V01 by itself.
