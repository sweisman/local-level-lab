# Why the faster ESA calculation failed its start-choice gate

The sealed [pair table](../esa-observed-model-dispatch-v2/pair-results.csv)
contains eight globe model/processing groups, each with two primary starts.
The two calculations agree on the chosen start in five groups and disagree in
three. All 16 matched globe forecasts passed the separate position-comparison
check. The failed exact-start rule remains failed.

| Group | Wide start-cost gap | Selected start-cost gap | Cost scale |
|---|---:|---:|---:|
| Specified field, no removal, short receiver law | 1.37×10⁻⁸ | 1.01×10⁻⁷ | 681 |
| Zero field, no removal, short receiver law | 3.29×10⁻⁴ | 2.30×10⁻⁴ | 4.29×10⁹ |
| Zero field, profiled removal, persistent receiver law | 4.64×10⁻⁷ | 1.68×10⁻⁸ | 1.68×10⁷ |

Each gap is the absolute difference between the two saved training costs in
that method. In every disagreement, it is tiny relative to the cost itself.
The largest same-start difference between methods is 1.09×10⁻⁷, 5.20×10⁻⁴
and 8.40×10⁻⁷ respectively. Thus the saved evidence is consistent with an
unstable choice between near-tied starts, not a large difference in fitted
objective. This audit uses only saved costs and does not prove that the two
starts make equivalent forecasts. The separate [saved forecast diagnostic](README.md)
found cross-primary differences no larger than 0.00007914 m on this one
development recording; that is not a prospective equivalence qualification.

A new method could treat near-tied starts as equivalent only if a **fixed,
prospective** cost tolerance and a separate bound on their withheld forecast
difference both pass independent generated controls. It must then be tested
on a separately selected development input. This audit cannot change the
original 5/8 qualification result or authorize protected ESA confirmation.
