"""Console script for op_env."""
import argparse
import json
import os
import pipes
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Union

from typing_extensions import TypedDict
import yaml

from .op import op_smart_lookup


class Arguments(TypedDict):
    operation: str
    environment: List[str]
    command: List[str]


class AppendListFromYAMLAction(argparse.Action):
    def __call__(self,
                 parser: argparse.ArgumentParser,
                 namespace: argparse.Namespace,
                 values: Union[str, Sequence[Any], None],
                 option_string: Optional[str] = None):
        assert isinstance(values, str)  # should be validated already by argparse
        filename = values
        with open(filename, 'r') as stream:
            variables_from_yaml = yaml.safe_load(stream)
            if variables_from_yaml is None:
                # treat an empty file as an empty list
                variables_from_yaml = []
            if not isinstance(variables_from_yaml, list):
                raise argparse.ArgumentTypeError('YAML file must be a list; '
                                                 f'found {variables_from_yaml}')
            if not all([isinstance(item, str) for item in variables_from_yaml]):
                raise argparse.ArgumentTypeError('YAML file must contain a list of strings; '
                                                 f'found {variables_from_yaml}')
        envvars = getattr(namespace, self.dest)
        envvars.extend(variables_from_yaml)


def add_environment_arguments(arg_parser: argparse.ArgumentParser):
    arg_parser.add_argument('--environment', '-e',
                            metavar='ENVVAR',
                            action='append',
                            default=[],
                            help='environment variable name to set, '
                            'based on item with same tag in 1Password')
    arg_parser.add_argument('--yaml-environment', '-y',
                            metavar='YAMLENV',
                            action=AppendListFromYAMLAction,
                            dest='environment',
                            default=[],
                            help='YAML config specifying a list of environment variable '
                            'names to set')


def parse_argv(argv: List[str]) -> Arguments:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='operation')
    subparsers.required = True
    run_desc = 'Run the specified command with the given environment variables'
    run_parser = subparsers.add_parser('run',
                                       description=run_desc,
                                       help=run_desc)
    add_environment_arguments(run_parser)
    run_parser.add_argument('command',
                            nargs='+',
                            help='Command to run with the environment set from 1Password')
    json_desc = 'Produce simple JSON on stdout mapping requested env variables to values'
    json_parser = subparsers.add_parser('json',
                                        description=json_desc,
                                        help=json_desc)
    add_environment_arguments(json_parser)
    sh_desc = ("Produce commands on stdout that can be 'eval'ed to set "
               "variables in current shell")
    sh_parser = subparsers.add_parser('sh',
                                      help=sh_desc,
                                      description=sh_desc)
    add_environment_arguments(sh_parser)
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
    elif args['operation'] == 'sh':
        new_env = do_smart_lookups(args['environment'])
        for envvar, envvalue in new_env.items():
            print(f'{envvar}={pipes.quote(envvalue)}; export {envvar}')
        return 0
    else:
        raise ValueError(f"Unknown operation: {args['operation']}")


def main(argv: List[str] = sys.argv) -> int:
    """Console script for op_env."""
    args = parse_argv(argv)
    return process_args(args)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
