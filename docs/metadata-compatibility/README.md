# Checking historical source versions

Completed analyses record the hashes of the source files they used. As shared
code improves, a current checkout can contain a newer version of those files.
That is separate from corruption of the recorded analysis.

The metadata verifier selects an exact **same-path, same-hash frozen source
version**. It checks the preserved bytes and the archive's checksums. It rejects
an absent or corrupt version and does not accept a different source file merely
because it has the desired hash. Ordinary measurement and result artifacts do
not receive this source-version fallback.

The small registry `repro/source-versions.json` preserves an earlier status
generator that predates this resolver. Other historical source versions remain
in their existing verified evidence packs. Historical test fixtures likewise
read the source snapshot declared by their study, rather than newer library
files from the checkout. No recorded fit, stopping rule or result hash changes.

[Reproducibility guide](../REPRODUCIBILITY.md) ·
[Current analysis status](../CURRENT_STATUS.md).
