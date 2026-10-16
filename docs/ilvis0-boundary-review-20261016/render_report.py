"""Publication-only renderer; preserves the completed arithmetic builder."""
import shutil
from build_report import HERE, OUTPUT, load, sha, write, seal


def render(review):
    for name in ('manifest.json','review.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    text='# Timing-boundary recovery review\n\n'
    text+='**One additional complete comparison favors globe; five of the six reviewed stretches remain unresolved.** '
    text+='The recovered comparison also favors the specified background field under both processing cases. '
    text+='Its cause and a solar-versus-sidereal distinction are not determined.\n\n'
    text+='The numerical check now verifies both sides of a timing boundary with all nuisance directions included. '
    text+='Original measurements, physical bounds, receiver weights and clock remain unchanged. Earlier stopping labels are preserved.\n\n'
    text+='| Stretch | Shape result | Passing primary fits | Passing required repeat pairs |\n|---|---|---:|---:|\n'
    for row in review['comparisons']:
        sid=row['segment_id'];d=review['dispositions'][sid]
        text+=f"| `{sid}` | {d['shape_preference']} | {sum(f['converged'] for c in row['cases'] for f in c['fits'])}/6 | {d['passed_repeat_pairs']}/{d['required_repeat_pairs']} |\n"
    text+='\n## Recovered comparison\n\n'
    text+='| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost |\n|---|---:|---:|---:|\n'
    for row in review['comparisons']:
        if review['dispositions'][row['segment_id']]['shape_preference']!='globe':continue
        for c in row['cases']:
            costs={f['model']:f['residual_sum_squares'] for f in c['fits']}
            text+=f"| {c['case_id']} | {costs['sphere_rotating']:.6f} | {costs['sphere_still']:.6f} | {costs['flat_still']:.6f} |\n"
    text+='\nThe required repeat agrees in relative cost to about 8.4 × 10⁻¹² and in track RMS '
    text+='to at most 1.1 micrometres per axis. These are numerical repeatability measures, not instrument accuracy.\n\n'
    text+='## Remaining checks\n\n'
    text+='| Endpoint | Outcome |\n|---|---|\n'
    for r in review['attempts']:
        if not r['passed']:text+=f"| `{r['source_identity']}` | {r['display_reason']} |\n"
    text+='\nThe interrupted identity remains unresolved. Its journal is retained unchanged; '
    text+='the continuation ran only previously unstarted identities. The reporting error occurred '
    text+='before any native evaluation and supplies no numerical result.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [All stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · '
    text+='[Next steps](../NEXT_STEPS.md). This review reads saved outputs only and performs no new fits or predictions.\n'
    (HERE/'README.md').write_text(text)
    names=['manifest.json','review.json','completion.json','README.md']
    names.extend(p.name for p in HERE.glob('evidence-*') if p.is_file() and p.name != "evidence-receipt.json")
    write(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in names},
        observed_starts=0,native_predictions=0,original_files_read=0))


if __name__ == "__main__":
    seal(HERE, artifact="review.json", key="review_sha256")
    render(load(HERE / "review.json"))
