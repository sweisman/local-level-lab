# Two Galileo-only carrier paths preserve the fixed shape preference

On ESA flight 187, the original GPS carrier path scored **−7.13**. The
Galileo-only paths scored **−7.08** and **−7.19**. Negative values favor the
zero-field globe over the zero-field disc, with zero marking a tie.

| Galileo path | Later horizontal RMS from GPS | Later height RMS from GPS | Fixed shape score |
| --- | ---: | ---: | ---: |
| Septentrio | 30.7 cm | 2.1 cm | −7.080 |
| NovAtel | 32.0 cm | 3.0 cm | −7.187 |

The two Galileo paths agree with each other to **1.94 cm RMS** in three
dimensions over the later 120 reports. Both completed every one of the 519
one-second steps and used at least eight common Galileo satellites. The
absolute differences above are between receiver solutions. The study has
no separate reference for the aircraft's true position.

Both paths start at the original earlier position. The saved GPS path
supplies the common elevation mask. Each later displacement comes from
Galileo E1/E5b carrier changes, the final ESOC ephemerides and a separately
solved receiver clock change. At the 18 shared samples used to check Galileo
clock timing, the SP3 and RINEX clock files differed by at most 0.465 ps.
The same antenna, position coordinates and neutral-atmosphere model remain
shared sources of error. No inertial fit, forecast change or protected
flight was used.

| ESOC product for GPS week 2269, day 187 | Compressed bytes | SHA-256 |
| --- | ---: | --- |
| `ESA0MGNFIN_20231870000_01D_05M_ORB.SP3.gz` | 977,601 | `b432894dada564aa6a677b4b488e744efb10a05a08fb182840123ca487308d30` |
| `ESA0MGNFIN_20231870000_01D_30S_CLK.CLK.gz` | 9,470,903 | `eb736ad0c86877d0d62153034ab6b44eced10e89a7bd95ece693150ad84f66f2` |

The run took 16 seconds on one numerical thread and all 11 focused tests
passed. The evidence includes both raw excerpts, the final products and the
satellite decisions at each step.
[Official ESA product index](https://navigation-office.esa.int/products/gnss-products/2269/)

[Frozen plan](ESA_GALILEO_PHASE_PATH_PLAN.md) ·
[Numerical results](esa-galileo-phase-path-result.json) ·
[Execution receipts](esa-galileo-phase-path-evidence/README.md) ·
[Reproduction bundle](esa-galileo-phase-path-evidence/bundle.zip)
