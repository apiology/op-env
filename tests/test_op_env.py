#!/usr/bin/env python

"""Tests for `op_env` package."""

import os
import pytest
import subprocess
from unittest.mock import patch

from op_env.cli import parse_argv
from op_env.op import op_lookup


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


def test_op_lookup():
    with patch('op_env.op.subprocess') as mock_subprocess:
        op_lookup('TEST_VALUE')
        mock_Popen = mock_subprocess.Popen
        mock_ps = mock_Popen.return_value
        mock_Popen.assert_called_with(['op', 'list', 'items', '--tags', 'TEST_VALUE'],
                                      stdout=mock_subprocess.PIPE)
        mock_subprocess.check_output.\
            assert_called_with(['op', 'get', 'item', '-', '--fields', 'password'],
                               stdin=mock_ps.stdout)


def test_parse_args_run_command_with_long_env_variables():
    argv = ['op-env', 'run', '-e', 'DUMMY', '--environment', 'DUMMY2', 'mycmd']
    args = parse_argv(argv)
    assert vars(args) == {'command': ['mycmd'],
                          'environment': ['DUMMY', 'DUMMY2'],
                          'subparser_name': 'run'}


def test_parse_args_run_command_with_multiple_variables():
    argv = ['op-env', 'run', '-e', 'DUMMY', '-e', 'DUMMY2', 'mycmd']
    args = parse_argv(argv)
    assert vars(args) == {'command': ['mycmd'],
                          'environment': ['DUMMY', 'DUMMY2'],
                          'subparser_name': 'run'}


def test_parse_args_run_command_with_arguments():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert vars(args) == {'command': ['mycmd', '1', '2', '3'],
                          'environment': ['DUMMY'],
                          'subparser_name': 'run'}


def test_parse_args_run_simple():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd']
    args = parse_argv(argv)
    assert vars(args) == {'command': ['mycmd'], 'environment': ['DUMMY'], 'subparser_name': 'run'}


@pytest.mark.skip(reason="not yet written")
def test_cli_run():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'env']
    expected_envvar = 'DUMMY=dummyvalue'
    actual_output = subprocess.check_output(argv).decode('utf-8')
    assert expected_envvar in actual_output


def test_cli_help_run():
    expected_help = """usage: op-env run [-h] [--environment ENVVAR] command [command ...]

positional arguments:
  command               Command to run with the environment set from 1Password

optional arguments:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', 'run', '--help'], env=env).decode('utf-8')
    assert actual_help == expected_help


def test_cli_help():
    expected_help = """usage: op-env [-h] {run} ...

positional arguments:
  {run}       Run the specified command with the given environment variables

optional arguments:
  -h, --help  show this help message and exit
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', '--help'],
                                          env=env).decode('utf-8')
    assert actual_help == expected_help
