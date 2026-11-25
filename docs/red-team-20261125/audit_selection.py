# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review audit of what the selection ledger left out, and why. Reads one CSV; runs no fits."""
import collections
import csv
import json
import re
import sys

rows = list(csv.DictReader(open(sys.argv[1], newline='')))
print('files', len(rows), 'states', dict(collections.Counter(r['state'] for r in rows)))
print('selected stretches', sum(int(r['selected_stretches'] or 0) for r in rows))
total = collections.Counter(); files_with = collections.Counter()
by_year = collections.defaultdict(collections.Counter)
for r in rows:
    counts = json.loads(r['rejection_counts']) if r['rejection_counts'] else {}
    m = re.search(r'(\d{2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})', r['filename'], re.I)
    year = '20'+m.group(3) if m else 'undated-name'
    by_year[year]['files'] += 1; by_year[year]['stretches'] += int(r['selected_stretches'] or 0)
    for k, v in counts.items():
        total[k] += v; files_with[k] += v > 0; by_year[year][k] += v
print('rejection counts summed over files (units as recorded; one sample can fail several rules):')
for k, v in total.most_common():
    print(f'  {k:45s} {v:10d} in {files_with[k]} files')
print('by year in filename:')
for year in sorted(by_year):
    c = by_year[year]
    print(f"  {year}: files {c['files']:3d} stretches {c['stretches']:3d} below_speed {c['below_ground_speed']:8d} course_rate {c['excessive_course_rate']:7d} alignment {c['incomplete_alignment']:8d}")
print('reasons:', dict(collections.Counter(r['reason'] for r in rows if r['reason'])))
print('name families:', dict(collections.Counter(re.sub(r'[0-9]+', '#', r['filename'])[:40] for r in rows).most_common(12)))
