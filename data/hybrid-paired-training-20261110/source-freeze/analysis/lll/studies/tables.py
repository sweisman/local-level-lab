# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public abridged table generated from the comprehensive measured inventory."""
import html


def stretch_table(rows):
    if not rows or len({r['segment_id'] for r in rows})!=len(rows):
        raise ValueError('nonempty unique stretch inventory required')
    text=['| Recording / stretch | UTC interval | IMU type | Minutes | Speed min / median (km/h) | Course | Mean latitude | Track (km) | Current disposition |',
          '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for row in rows:
        label={'globe':'Globe preferred','flat':'Flat preferred','unresolved':'Unresolved'}.get(row['shape_preference'],'Unresolved')
        source=html.escape(row['filename']).replace('|','&#124;')
        text.append(f"| `{source}`<br>`{row['segment_id']}` | {row['start_utc']}<br>to {row['end_utc']} | "
            f"{row['imu_type']} | {float(row['duration_s'])/60:.2f} | "
            f"{float(row['minimum_ground_speed_kmh']):.1f} / {float(row['median_ground_speed_kmh']):.1f} | "
            f"{float(row['mean_course_deg']):.1f}° | {float(row['mean_latitude_deg']):.2f}° | "
            f"{float(row['gps_track_km']):.1f} | {label} |")
    return '\n'.join(text)+'\n'


def update_analytics_page(root):
    import csv
    from pathlib import Path
    directory=Path(root)/'docs/ilvis0-current-findings-20261015'
    with (directory/'stretch-analytics.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
    page=directory/'ANALYTICS.md';text=page.read_text();marker='<!-- stretch-table:start -->'
    if marker in text:text=text.split(marker)[0].rstrip()+'\n'
    text+='\n'+marker+'\n\n## All selected stretches\n\n'
    text+='This abridged table comes from the [comprehensive CSV](stretch-analytics.csv). '
    text+='Course is GPS travel direction, not aircraft heading; negative latitude is south.\n\n'
    text+=stretch_table(rows)+'\n<!-- stretch-table:end -->\n';page.write_text(text)
    return len(rows)
