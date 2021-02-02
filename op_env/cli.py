"""Console script for op_env."""
import argparse
import sys
from typing import List, Dict
import subprocess
from .op import op_lookup


def parse_argv(argv: List[str]) -> Dict[str, str]:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='Run the specified command '
                                       'with the given environment variables',
                                       dest='subparser_name')
    run_parser = subparsers.add_parser('run')
    run_parser.add_argument('--environment', '-e',
                            metavar='ENVVAR',
                            action='append',
                            help='environment variable name to set, '
                            'based on item with same tag in 1Password')
    run_parser.add_argument('command',
                            nargs='+',
                            help='Command to run with the environment set from 1Password')
    return vars(parser.parse_args(argv[1:]))


def process_args(args: Dict[str, str]) -> int:
    if args['subparser_name'] == 'run':
        env: Dict[str, str] = {
            envvar: op_lookup(envvar)
            for envvar in args['environment']
        }
        print(f'Running with env {env}')
        subprocess.check_call(args['command'], env=env)
        return 0
    else:
        raise ValueError(f"Unknown subparser_name: {args['subparser_name']}")


def main(argv: List[str] = sys.argv) -> int:
    """Console script for op_env."""
    args = parse_argv(argv)
    return process_args(args)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
