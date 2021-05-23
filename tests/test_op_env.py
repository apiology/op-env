#!/usr/bin/env python

"""Tests for `op_env` package."""

# from op_env import op_env
import argparse
import os
import subprocess
from unittest.mock import call, patch

import pytest

from op_env.cli import parse_argv, process_args


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


def test_process_args():
    with patch('builtins.print') as mock_print:
        ns = argparse.Namespace()
        setattr(ns, '_', '<fake>')
        out = process_args(ns)

        assert out == 0
        mock_print.assert_has_calls([call('Arguments: <fake>'),
                                     call('Replace this message by putting '
                                          'your code into op_env.cli.process_args')])


# @pytest.mark.skip(reason="working on main help test first")
def test_parse_argv_run_simple():
    argv = ['op_env', 'op1', '123']
    args = parse_argv(argv)
    assert vars(args) == {'operation': 'op1', 'arg1': 123}


def test_cli_op1_help():
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)
    expected_help = """usage: op_env op1 [-h] arg1

Do some kind of operation

positional arguments:
  arg1        arg1 help

optional arguments:
  -h, --help  show this help message and exit
"""
    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op_env', 'op1', '--help'],
                                          env=env).decode('utf-8')
    assert actual_help == expected_help


def test_cli_help():
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)
    expected_help = """usage: op_env [-h] {op1} ...

positional arguments:
  {op1}
    op1       Do some kind of operation

optional arguments:
  -h, --help  show this help message and exit
"""
    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op_env', '--help'],
                                          env=env).decode('utf-8')
    assert actual_help == expected_help
