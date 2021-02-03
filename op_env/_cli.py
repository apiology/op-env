"""Console script for op_env."""
import argparse
import json
import sys
from typing import List, Dict
from typing_extensions import TypedDict
import subprocess
import os
from .op import op_smart_lookup


class Arguments(TypedDict):
    operation: str
    environment: List[str]
    command: List[str]


def add_environment_argument(arg_parser: argparse.ArgumentParser):
    arg_parser.add_argument('--environment', '-e',
                            metavar='ENVVAR',
                            action='append',
                            default=[],
                            help='environment variable name to set, '
                            'based on item with same tag in 1Password')


def parse_argv(argv: List[str]) -> Arguments:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='operation')
    subparsers.required = True
    run_parser = subparsers.add_parser('run',
                                       help='Run the specified command '
                                       'with the given environment variables')
    add_environment_argument(run_parser)
    run_parser.add_argument('command',
                            nargs='+',
                            help='Command to run with the environment set from 1Password')
    json_parser = subparsers.add_parser('json',
                                        help='Produce simple JSON on stdout '
                                        'mapping requested env variables to values')
    add_environment_argument(json_parser)
    return vars(parser.parse_args(argv[1:]))  # type: ignore


def do_smart_lookups(envvars: List[str]) -> Dict[str, str]:
    return {
        envvar: op_smart_lookup(envvar)
        for envvar in envvars
    }


def process_args(args: Arguments) -> int:
    if args['operation'] == 'run':
        copied_env = dict(os.environ)
        new_env = do_smart_lookups(args['environment'])
        copied_env.update(new_env)
        subprocess.check_call(args['command'], env=copied_env)
        return 0
    elif args['operation'] == 'json':
        new_env = do_smart_lookups(args['environment'])
        print(json.dumps(new_env))
        return 0
    else:
        raise ValueError(f"Unknown operation: {args['operation']}")


def main(argv: List[str] = sys.argv) -> int:
    """Console script for op_env."""
    args = parse_argv(argv)
    return process_args(args)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
