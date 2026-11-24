# Look for a smooth position error that could close the saved ESA score gap

Keep the original and three screened satellite sets from the
[uncertain-anchor check](ESA_CARRIER_REWEIGHTED_BUDGET_RESULT.md).
Search for a smooth displacement of the saved GPS path that would
change the original position score by the full gap. Use positions at
the six anchors and knots spaced every 2.5 seconds. Connect them with a
natural cubic spline in each of the three score coordinates.

Keep each anchor coordinate within 1 m and acceleration error within
1.876 mm/s² RMS, as in the previous example. Limit additional range
errors to 1 mm RMS in directions covered by Nuuk Museum and
2 mm RMS in the remaining directions. Both RMS values use the number
of retained range rows. Reserve the verified geometric remainder
before setting both range limits. Use the same fixed satellite, clock
and atmosphere terms as the earlier linearization.

Use one capped constrained solve for each of the four satellite sets.
Keep each solve within 160 optimizer iterations. Independently check
the returned path's anchor values, integrated squared acceleration,
score change and range norms. If the path spans the gap, scale it to
the gap and repeat those checks. A feasible witness demonstrates a
possibility under the stated allowances. A search that stops below the
gap leaves the existence of such a path open.

Use one task, one numerical thread, 245 charged calculations and a
120-second wall cap. Use saved data from ESA development flight 187.
Use zero new model fits, original-file reads and reserved-flight reads.
