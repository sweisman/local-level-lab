# A public one-second ground control from Qaqortoq

The Qaqortoq receiver matched **all 121 seconds** of the two-minute ESA
development window. Each of the **120 one-second intervals** had at least five
usable GPS satellites in common with both intervening aircraft half-second
pairs. The ground observations have explicit `C1C`, `L1C`, `C2W` and `L2W`
signal labels. [BKG high-rate archive](https://igs.bkg.bund.de/root_ftp/IGS/highrate/2023/187/) ·
[IGS station record](https://network.igs.org/QAQ100GRL)

The station is approximately **456–458 km** from the aircraft during this
window. The matched signals can test some satellite errors shared between the
two receivers. Atmospheric delays, antenna behavior and other local errors can
differ over that distance. The nearby 1 Hz Nuuk Museum recording remains the
better local reference and still requires EarthScope sign-in.
[Nuuk data access](ESA_GROUND_REFERENCE_AVAILABILITY.md)

The acquisition verified the original archive and exact `11:45` quarter-hour
member. The decoded record contains 900 consecutive GPS seconds. The observed
timestamps establish cadence because the header omits its interval and final
time. Eleven parser and pairing tests passed. The intake ran zero fits and
opened no reserved aircraft recordings. The [signed range comparison](ESA_QAQ_GROUND_SCORE_RESULT.md)
uses these matches and the frozen aircraft score.

| Evidence | SHA-256 |
| --- | --- |
| BKG daily source archive | `3a930b2fea4bceb5e3876f15a72eb2f8b7539353b21d4470457053b6a7c11486` |
| Compact quarter-hour member | `08a104f4ed40ab71952039103ee5d990bced83e1ee960c328af761e0bfb087ff` |
| Expanded quarter-hour | `eb8b38ce05ed7f599c30b5df321f34cac1754cb8e75e8d6fbcec638a8cc982f2` |
| Intake receipt | `0cd8b21d3015f105d750d29290016f3eac353e85d2ab65c6cab4cfaeeb82c6e8` |

The retained local files are the original compact member and the matched
excerpt. To reproduce the intake, use the daily archive and GSI `crx2rnx`
4.2.0 with the saved aircraft parent study.
[Acquisition and exact matches](esa-qaq-ground-intake.json) ·
[Original daily archive](https://igs.bkg.bund.de/root_ftp/IGS/highrate/2023/187/QAQ100GRL_R_20231870000_01D_01S_MO.crx.tar.gz) ·
[GSI converter](https://terras.gsi.go.jp/ja/crx2rnx.html)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_qaq_ground_intake \
  /path/to/QAQ100GRL_R_20231870000_01D_01S_MO.crx.tar.gz /path/to/crx2rnx
```
