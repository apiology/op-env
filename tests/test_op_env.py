#!/usr/bin/env python

"""Tests for `op_env` package."""

import pytest
import subprocess

# from op_env import op_env


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


def test_cli_help():
    expected_help = b"""usage: op-env [-h] [_ ...]

positional arguments:
  _

optional arguments:
  -h, --help  show this help message and exit
"""
    actual_help = subprocess.check_output(['op-env', '--help'])
    assert expected_help == actual_help
