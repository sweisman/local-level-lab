# The vertical force records agree more closely at longer averaging times

Applying the same 1.1-second average to both records raises all three
correlations above 0.93 at the existing candidate offset. The RMS
difference between their centered force changes falls by 92% in each
excerpt, to the nearest whole percent. The short averaging times were
more sensitive to differences between the two signals.

| Excerpt byte offset | 0.1 s | 0.3 s | 0.7 s | 1.1 s |
| ---: | ---: | ---: | ---: | ---: |
| 466,124,214 | 0.467 | 0.844 | 0.950 | 0.969 |
| 931,200,441 | 0.843 | 0.721 | 0.864 | 0.937 |
| 1,396,276,591 | 0.563 | 0.870 | 0.960 | 0.969 |

The [response diagnostic](ESA_GIRAFE_PLATFORM_VERTICAL_RESPONSE_PLAN.md)
uses the same time supports, offset and excerpts as the original three
vertical holdouts. It reproduces every short-width correlation. The
longer averaging supports give evidence of shared low-frequency motion.
The original 1-of-3 timing qualification stays in the record. A check
against the separately recorded iMAR acceleration can test whether the
candidate clock transfers to another instrument on the same flight.

The [verified receipt](esa-girafe-platform-vertical-response-result.json)
has SHA-256 `6ace84fe9ba24ef55508683fae0123b8bfd8d652de707928987be4c04fc00657`.
Manifest SHA-256 is
`7970b7dbcdb1071f93bf2747a95aa0f396beb92b67ea43e07e86f9a5e8c7b513`.
The local job used 16 charged operations and completed in 1.4 seconds on
one thread. It performed zero network calls and zero model fits.
The [portable evidence bundle](esa-girafe-platform-vertical-response-evidence/bundle.zip)
contains the frozen source, inputs, charge ledger and every comparison.
