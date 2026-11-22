# Compare the frozen shape score on two Galileo-only paths

Use the archived Septentrio and NovAtel observations from development flight
187. Use their matched E1 and E5b carrier signals, GPS time tags, and the 520
integer-second positions of the original 400/120 comparison. Align both paths
to the same earlier position used by the GPS carrier replay. Keep the frozen
shape forecasts, position metric and score operator unchanged.

Use final ESOC multi-constellation orbit and clock files for GPS week 2269,
day 187. Verify the GPS time convention by comparing identical Galileo SP3
and clock-file samples at the 300-second knots around the working window to
within one picosecond. Use eight-knot 300-second orbit interpolation and
linear interpolation between 30-second clock samples. Use E1 code for signal
travel time and add the periodic relativistic clock correction derived from
the interpolated orbit, using a one-second centered velocity stencil.
[ESA final products](https://navigation-office.esa.int/products/gnss-products/2269/) ·
[Galileo frequencies](https://www.gsc-europa.eu/sites/default/files/sites/all/files/Galileo_OS_SIS_ICD_v2.1.pdf) ·
[Clock convention](https://gssc.esa.int/navipedia/index.php/Clock_Modelling)

Require normal observations on common satellites and both bands, no
loss-of-lock flags, and an E1–E5b range-change difference at most 0.075 m
within each receiver. Use the NovAtel E1 Doppler if present at both endpoints
and require the change to agree within 0.7 cycles. Require usable Doppler
and precise products on every used satellite. After a common clock
adjustment, discard receiver-to-receiver range differences above 0.075 m.
Use a common 5-degree elevation mask based on the saved GPS carrier path
and require at least five common satellites. The saved positions serve to
select satellites and provide the one common start, with no later position
updates from GPS. Solve one receiver clock change per step and update the
neutral atmospheric delay at the solved endpoint. Preserve the first
failed step and its omissions if either path cannot be completed.

Freeze a 519-step study on one numerical thread with a 120-second
cooperative limit and two receiver solutions per step, each with one
atmospheric update. Report horizontal and vertical disagreement, fixed
shape scores, and every skipped satellite. These carriers are from a
different constellation, with the same antenna and conventional receiver
coordinates. No inertial fit, protected flight or statistical inference
enters the comparison.
