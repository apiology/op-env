#!/usr/bin/env python

"""Tests for `op_env` package."""

import pytest

# from op_env import op_env
import argparse
import subprocess
from unittest.mock import patch, call
from op_env.cli import process_args, parse_argv


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
                                          'your code into python_boilerplate.cli.process_args')])


def test_parse_argv_run_simple():
    argv = ['op_env', 'whatever']
    args = parse_argv(argv)
    assert vars(args) == {'_': ['whatever']}


def test_cli_help():
    expected_help = """usage: op_env [-h] [_ ...]

positional arguments:
  _

optional arguments:
  -h, --help  show this help message and exit
"""
    # older python versions show arguments like this:
    alt_expected_help = expected_help.replace('[_ ...]', '[_ [_ ...]]')
    actual_help = subprocess.check_output(['op_env', '--help']).decode('utf-8')
    assert actual_help in [expected_help, alt_expected_help]
