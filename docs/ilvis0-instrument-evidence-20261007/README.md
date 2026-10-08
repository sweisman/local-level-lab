# What we now know about the airborne IMU

The six prepared recordings come from professional POS AV 510 systems and identify
their IMU as type 6. There is now a direct published connection to the hardware
family: NOAA researchers describe a POS AV 510 fitted with IMU-6 as a tactical-grade
Litton-200 unit. This is strong support for the family identification, rather than
an identification made from a different manufacturer's type-number table.
[Damiani and Mader, ION GNSS+ 2014 abstract](https://www.ion.org/publications/abstract.cfm?articleID=12249)

The inference for our files is **consistent with the LN-200 family**, rather than a
proven exact part number. The manufacturer's LN-200 family description identifies
three fiber-optic gyros, three silicon accelerometers and digital angle/velocity
increments. Its hardware quality is appropriate to airborne inertial measurement.
The exact variant, individual calibration and processing of our recordings still
need confirmation. [Northrop Grumman family description](https://www.northropgrumman.com/wp-content/uploads/LN-200-FOG-Family-datasheet.pdf)

Applanix's 2009 FAQ describes specially selected LN200ROM variants for its 510
systems, and notes that the same product can use different IMUs. This supports a
possible variant; it does not tie LN200ROM to each of our six source hashes. Its
navigation explanation also says GPS-estimated sensor errors correct the increments
before navigation integration. That establishes a correction stage in the fused
solution, but does not specify which side of it supplies legacy Group 4.
[Applanix FAQ, printed pages 2 and 6](https://www.applanix.com/downloads/products/FAQs/faq_pos_av_rev_2a.pdf)

## The distinction that still matters

We need to know exactly what entered the recorded IMU stream. The same system can
produce both sensor measurements and a GPS-aided navigation answer. Excellent
navigation accuracy does not independently establish the accuracy or correction
history of the recorded sensor increments.

The newer V6 manual describes separate raw-sensor and navigation logging, an
unprocessed acquisition mode, and microsecond output time tags. These descriptions
support the architectural distinction. They do not establish the legacy V5 Group-4
tap point, sensor integration period, physical latency or correction settings.
[Applanix V6 manual, printed pages 1-11 to 1-13](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_USER_MANUAL.pdf)

| Question | Current conclusion |
|---|---|
| Is this consumer-grade hardware? | No. The logged professional system and published IMU-6 association support a tactical-grade LN-200-family inference. |
| Is the exact sensor variant identified? | No. The general LN200ROM association is insufficient to identify each installed unit. |
| Are the increment units supported? | Empirically, against fused Group 1; the original six-file checks and one gyro holdout failure remain preserved. |
| Are generic LN-200 scales safe to apply to these bytes? | No. The documented NovAtel output and our empirical Applanix scales differ. |
| Are Earth/transport rates retained in Group 4? | Still unresolved. The public correction description does not identify the legacy logging tap point. |
| Are bias/gain/noise, timing and mounting bounds independently established? | No. General specifications, inferred settings and successful software controls cannot supply per-installation bounds. |

NovAtel documents LN-200 increments as 2⁻¹⁹ radians and 2⁻¹⁴ metres/second per
count in its own RAWIMUSX output. Our empirical Applanix hypotheses are
0.4 arcsecond and 3.38 × 10⁻⁵ metres/second per count. The former is about 1.67%
larger than that documented angular quantum; the latter is about 44.62% smaller
than its velocity quantum. Different adapters can encode or rescale measurements
differently. This comparison neither disproves the hardware family nor establishes
which corrections Applanix applied. It prevents copying a family scale table into
the legacy decoder without validating the output format.
[NovAtel RAWIMUSX scale table](https://docs.novatel.com/OEM7/Content/SPAN_Logs/RAWIMUSX.htm)

## Exact configurations to ask about

The [configuration inventory](inventory.csv) associates the six existing source
hashes with their recorded version strings and embedded dates. It was built from
hash-verified completed evidence, without rescanning originals or inspecting gyro
residuals. The S/N below is the logged POS system identifier; it is not an
independently verified serial number for the installed IMU.

| Logged system S/N | Firmware | ICD | Embedded dates |
|---|---|---|---|
| 2720 | 04.50-Feb05/08 | 14.00 | 2009-04-14; 2014-09-16 |
| 3861 | 05.00-Dec16/09 | 17.00 | 2010-10-26; 2010-11-20 |
| 4126 | 05.20-Nov04/11 | 18.00 | 2015-09-24; 2017-09-20 |

The [technical question packet](QUESTIONS.md) names those configurations and asks
for the exact logging, scale, clock, correction and installation definitions. It is
a prepared request, not a message that has been sent. A firmware-matched legacy
ICD, acquisition description or calibration record could answer these questions;
another generic datasheet cannot.

This review supersedes the earlier blanket statement that no public hardware-family
association was available. The [earlier evidence matrix](../ilvis0-excitation-20261007/INSTRUMENT_EVIDENCE.md)
remains intact as historical evidence. No quantitative calibration or scientific
eligibility was promoted. All 232 originals remain, and empirical Earth fits/starts
remain zero. The project can proceed with explicitly labeled processing hypotheses,
but a measured Earth-model conclusion still needs the unresolved independent support.
