# Test timing differences between paired NASA gyroscopes

Use the two overlapping flight legs and four original recorder files from
the [paired accelerometer study](PAIRED_ACCELEROMETER_RESULT.md). Keep the
recorded IMU-to-aircraft rotation, angle conversions and all original source
checks. This comparison uses signed gyro increments. It requires no Earth-model
fit, fused attitude or ESA data.

Form 0.25- and 1-second windows on the left stream's existing overlap grid.
Compare nominal 200 Hz and elapsed-header timing separately. At each width
and clock, test a right-stream time shift from −300 to +300 ms in 5 ms steps.
A positive shift selects later recorded right-stream packets. Average the
signed angle increments over the summed duration of complete packets.
Never split a packet. Keep the same windows for every shift, with at least
80% support at both recorders. Require both windows in a match to stay
inside the same half of the original overlap for every shift. Keep at least
60 seconds of nominal windows in each half.

At each shift, fit the same three-dimensional rotation and constant offset
on the earlier half. Weight windows equally over the shared support. Require
the earlier centered right-stream singular ratio to reach 0.05, as in the
[earlier alignment check](../ilvis0-pair-alignment/RESULT.md). Pick the
smallest earlier vector RMS, breaking ties toward zero then the lower signed
shift. Compare the choice with a separately fitted zero-shift reference on
the later half. Also report the full earlier cost curve and the later error
on 10-second averages over fixed complete blocks. Record the spread of the
earlier choices across clocks and window widths. The two clocks, lengths and
related recorders do not supply independent replications.

A timing improvement would show that these two logged streams agree more
closely under that alignment. Different packet assignment, mount response,
calibration or internal filtering could also produce it. A fitted shift does
not calibrate either recorder's clock or absolute gyro error.

Freeze two single-thread workers, 180 seconds, two original decodes per task
and 484 earlier alignment attempts per task, plus four support checks and
four matched later checks.
Verify whole-packet arithmetic, support and split invariance, held-back
selection and recovery before launch. Retain every outcome and source hash.
