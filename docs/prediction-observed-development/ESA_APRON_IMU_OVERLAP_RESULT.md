# GPS ranges and inertial motion during the Nuuk stop

The aircraft and Nuuk Museum tracked 12 common GPS satellites in each of 120 one-second intervals. Their range residuals showed weak correlation, −0.09. Subtracting the museum residuals increased the aircraft RMS from 10.77 mm to 13.93 mm. This longer comparison gives little evidence that one shared error dominated the two receivers on the ground.

| Interval | Aircraft RMS | Museum RMS | Difference RMS | Correlation |
| --- | ---: | ---: | ---: | ---: |
| Full two minutes | 10.77 mm | 7.93 mm | 13.93 mm | −0.09 |
| First minute | 12.49 mm | 8.68 mm | 15.89 mm | −0.10 |
| Second minute | 8.71 mm | 7.10 mm | 11.66 mm | −0.08 |

The aircraft's inertial instrument recorded 36,000 samples over the same window. The standard deviation of its one-second mean gyro rates was about 698, 73 and 106 degrees per hour on the three instrument axes. A fixed parking location does not establish that the instrument stayed angularly still. The recorded variation can contain motion, vibration and sensor effects. The range calculation assumes a fixed aircraft position and leaves those effects in the result.

The two-minute ground comparison used the same satellite products and phase checks as the earlier 18-second comparison. It leaves the independent in-flight error limits open. The first run stopped at a bookkeeping error before reading measurements. The corrected run preserved that stop and completed all 361 planned checks, with zero model fits and zero reads from the reserved flights. [Study plan](ESA_APRON_IMU_OVERLAP_PLAN.md) · [Accounting correction](ESA_APRON_IMU_OVERLAP_ACCOUNTING_PLAN.md) · [Verified result and paired ranges](esa-apron-imu-ranges-result.json) · [Earlier ground comparison](ESA_APRON_NKAR_RESULT.md)
