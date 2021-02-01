#!/usr/bin/env python

"""Tests for `op_env` package."""

import pytest
import subprocess

from op_env.cli import parse_argv


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_parse_args_run_commadn_with_arguments_():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert vars(args) == {'command': ['mycmd', '1', '2', '3'],
                          'e': 'DUMMY',
                          'subparser_name': 'run'}


def test_parse_args_run_simple():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd']
    args = parse_argv(argv)
    assert vars(args) == {'command': ['mycmd'], 'e': 'DUMMY', 'subparser_name': 'run'}


@pytest.mark.skip(reason="not yet written")
def test_cli_run():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'env']
    expected_envvar = 'DUMMY=dummyvalue'
    actual_output = subprocess.check_output(argv).decode('utf-8')
    assert expected_envvar in actual_output


def test_cli_help_run():
    expected_help = """usage: op-env run [-h] [-e ENVVAR] command [command ...]

positional arguments:
  command     Command to run with the environment set from
              1Password

optional arguments:
  -h, --help  show this help message and exit
  -e ENVVAR   environment variable name to set, based on item with
              same tag in 1Password
"""
    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', 'run', '--help']).decode('utf-8')
    assert actual_help == expected_help


def test_cli_help():
    expected_help = """usage: op-env [-h] {run} ...

positional arguments:
  {run}       Run the specified command with the given environment
              variables

optional arguments:
  -h, --help  show this help message and exit
"""
    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', '--help']).decode('utf-8')
    assert actual_help == expected_help
