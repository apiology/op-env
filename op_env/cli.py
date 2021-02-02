"""Console script for op_env."""
import argparse
import sys


def parse_argv(argv):
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
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    """Console script for op_env."""
    args = parse_argv(argv)

    print("Arguments: " + str(args))
    print("Replace this message by putting your code into "
          "op_env.cli.main")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
