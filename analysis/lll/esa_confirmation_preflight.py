# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check frozen ESA confirmation bindings without opening flight observations."""

import argparse
import json
from pathlib import Path, PurePosixPath

from .esa_confirmation_evidence import check_public
from .esa_confirmation_queries import TRAINING, WITHHELD, cases
from .esa_confirmation_training_profile import TIMES, TIMES_SHA, _read
from .studies.artifacts import digest, encoded, safe_path


VERSION = 'esa-confirmation-preflight-v1'
REQUIRED_REFERENCES = ('forecast_method', 'aircraft_error_model', 'physical_adequacy', 'decision_rule')


def cohort_binding(layouts):
    return digest(encoded(layouts))


def public_layouts(root):
    """Use the verified public layouts only, including the exact shared held-out times."""
    check_public(root)
    selections = cases(root)
    times = _read(root, TIMES, TIMES_SHA)
    return {
        row['receiver']['group_id']: dict(
            case=identity, gps_week=row['gps_week'], slice_ticks=row['slice_ticks'],
            receiver_sha256=row['receiver']['sha256'], imu_range_sha256=row['imu_range_sha256'],
            training={key: value['times_sha256'] for key, value in times['records'][identity]['training'].items()},
            withheld=times['records'][identity]['withheld']['times_sha256'])
        for identity, row in selections.items()
    }


def documentation_path(root, name):
    if not isinstance(name, str):
        raise ValueError('repository documentation path required')
    path = PurePosixPath(name)
    if not path.parts or path.parts[0] != 'docs' or path.suffix not in ('.md', '.json'):
        raise ValueError('repository documentation path required')
    return safe_path(root, name)


def describe(layouts):
    return dict(version=VERSION, groups=sorted(layouts), cohort_sha256=cohort_binding(layouts),
                available_training_reports=list(TRAINING), withheld_reports=WITHHELD,
                required_references=list(REQUIRED_REFERENCES), observed_fits_authorized=False,
                protected_outcome_reads=0)


def audit_plan(root, layouts, plan):
    """Verify identities and bytes. Scientific qualification is outside this function."""
    if not isinstance(plan, dict) or plan.get('version') != VERSION:
        raise ValueError('unsupported confirmation preflight format')
    if plan.get('groups') != sorted(layouts) or plan.get('cohort_sha256') != cohort_binding(layouts):
        raise ValueError('confirmation cohort identities or layouts differ')
    training = plan.get('training_reports')
    if (not isinstance(training, list) or not training
            or any(type(n) is not int or n not in TRAINING for n in training)
            or training != sorted(set(training))
            or any(str(n) not in layout['training'] for n in training for layout in layouts.values())):
        raise ValueError('choose a nonempty set of verified training layouts')
    references = plan.get('references')
    if not isinstance(references, dict):
        raise ValueError('confirmation evidence references are required')
    validated = {}
    for kind in REQUIRED_REFERENCES:
        binding = references.get(kind)
        if not isinstance(binding, dict) or set(binding) != {'path', 'sha256'}:
            raise ValueError(f'confirmation reference required: {kind}')
        source = documentation_path(root, binding['path'])
        if not source.is_file() or digest(source.read_bytes()) != binding['sha256']:
            raise ValueError(f'confirmation reference differs: {kind}')
        validated[kind] = binding.copy()
    if set(references) != set(validated):
        raise ValueError('unexpected confirmation evidence reference')
    return describe(layouts) | dict(binding_status='verified', training_reports=training,
                                    validated_references=validated)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', help='check a proposed confirmation plan under repository docs/')
    args = parser.parse_args()
    root = Path.cwd()
    layouts = public_layouts(root)
    if args.plan is None:
        result = describe(layouts) | dict(binding_status='metadata_only')
    else:
        raw = documentation_path(root, args.plan).read_bytes()
        result = audit_plan(root, layouts, json.loads(raw)) | dict(plan_sha256=digest(raw))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
