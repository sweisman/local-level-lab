# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guard a declared numerical allocation before executing a new job."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lll.compute_budget import environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=1,
                        help='maximum concurrent numerical workers in the target command')
    parser.add_argument('--threads', type=int, help='threads per worker; default shares available capacity')
    parser.add_argument('--reserved-threads', type=int, default=0,
                        help='capacity allocated to other active numerical jobs')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('target command required after --')
    try:
        settings = environment(workers=args.workers, threads=args.threads, reserved=args.reserved_threads)
    except ValueError as error:
        parser.error(str(error))
    os.execvpe(command[0], command, dict(os.environ, **settings))


if __name__ == '__main__':
    main()
