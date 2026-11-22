# Eight additional windows for checking aircraft-motion predictions

The [receiver-only selection rule](ESA_DIRECTION_HOLDOUT_SELECTION.md)
found 27 candidate blocks, 20 on the first flight leg and seven on the
second. It selected these eight before any direction measurements were
scored. Indices are zero-based in the original 2 Hz receiver export.

| Flight leg | First query | Last query | Receiver course |
| --- | ---: | ---: | --- |
| First | 15657 | 16455 | Intermediate |
| First | 19857 | 20655 | Intermediate |
| First | 26577 | 27375 | Intermediate |
| First | 30777 | 31575 | Steady |
| Second | 51976 | 52774 | Turn |
| Second | 53656 | 54454 | Intermediate |
| Second | 55336 | 56134 | Intermediate |
| Second | 57016 | 57814 | Intermediate |

The [selection receipt](esa-direction-holdout-selection.json) records all
27 candidates and the 13 audited exclusions. Its SHA-256 is
`63e98166299b0e79bde2413022c81918a80dea5df68aff687d64afb535744204`.
The completed task used one charged check and read only the four saved
metadata inputs. Both legs come from one recording. The seven reserved
flight groups remain unopened.
