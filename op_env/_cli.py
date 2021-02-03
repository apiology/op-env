"""Console script for op_env."""
import argparse
import sys
from typing import List, Dict
import subprocess
import os
from .op import op_smart_lookup


def parse_argv(argv: List[str]) -> Dict[str, str]:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='Run the specified command '
                                       'with the given environment variables',
                                       dest='operation')
    subparsers.required = True
    run_parser = subparsers.add_parser('run')
    run_parser.add_argument('--environment', '-e',
                            metavar='ENVVAR',
                            action='append',
                            default=[],
                            help='environment variable name to set, '
                            'based on item with same tag in 1Password')
    run_parser.add_argument('command',
                            nargs='+',
                            help='Command to run with the environment set from 1Password')
    return vars(parser.parse_args(argv[1:]))


def process_args(args: Dict[str, str]) -> int:
    if args['operation'] == 'run':
        copied_env = dict(os.environ)
        new_env: Dict[str, str] = {
            envvar: op_smart_lookup(envvar)
            for envvar in args['environment']
        }
        copied_env.update(new_env)
        subprocess.check_call(args['command'], env=copied_env)
        return 0
    else:
        raise ValueError(f"Unknown operation: {args['operation']}")


def main(argv: List[str] = sys.argv) -> int:
    """Console script for op_env."""
    args = parse_argv(argv)
    return process_args(args)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
