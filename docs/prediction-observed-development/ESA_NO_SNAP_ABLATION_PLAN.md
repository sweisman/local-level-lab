# Remove the changing-jerk term from the saved ESA forecast test

The correction audit identifies the highest-order inertial term as the main
source of kilometre-scale corrections. Test its role by setting its process
variance to zero. Keep the original acceleration and jerk drivers, initial
error settings, receiver offset and random walk, both receiver weighting cases
and the same 4.2-standardized-unit range. Treat that threshold as descriptive
for this changed law.

Use the same 24 starts, 400 earlier reports and 120 forecast reports on ESA
development recording 187. Reuse all 20 passing forecast paths and keep the
four failed starts. Build and seal both sets of ranges from earlier data
before opening the later reports. Keep the same training-selected starts,
coordinate chart, scoring horizons and descriptive accuracy screen.

Compare correction size, later range containment and model separation to the
unchanged full-law replay. A smaller range alone cannot qualify the modified
law. The results must show any loss of containment or point accuracy alongside
any gain in separation. No inference about actual jerk error or a scientific
decision follows from removing one term in this development control.

Freeze the existing forecast and range seals, the comparison receipt, source,
environment and the altered process variance. Use two operators over 520
reports and at most 48 cases, one numerical thread, zero new fits and zero
reserved-group reads.
