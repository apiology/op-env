#!/usr/bin/env python

"""Tests for `op_env` package."""

import os
import pytest
import subprocess
from unittest.mock import patch

from op_env.cli import parse_argv, process_args
from op_env.op import op_lookup, op_smart_lookup, op_fields_to_try


def test_process_args_runs_simple_command_with_simple_env():
    with patch('op_env.cli.subprocess') as mock_subprocess,\
         patch('op_env.cli.op_smart_lookup') as mock_op_lookup:
        command = ['env']
        args = {'subparser_name': 'run', 'command': command,
                'environment': ['a']}
        process_args(args)
        mock_op_lookup.assert_called_with('a')
        mock_subprocess.check_call.assert_called_with(command,
                                                      env={'a': mock_op_lookup.return_value})


def test_process_args_runs_simple_command():
    with patch('op_env.cli.subprocess') as mock_subprocess:
        command = ['env']
        args = {'subparser_name': 'run', 'command': command,
                'environment': []}
        process_args(args)
        mock_subprocess.check_call.assert_called_with(command, env={})


def test_process_args_rejects_non_run():
    with patch('op_env.op.subprocess'):  # for safety
        with pytest.raises(ValueError):
            args = {'subparser_name': 'definitely-not-run'}
            process_args(args)


def test_fields_to_try_simple():
    with patch('op_env.op.subprocess'):  # for safety
        out = op_fields_to_try('ABC')
        assert out == ['password']


def test_op_lookup_specific_field():
    with patch('op_env.op.subprocess') as mock_subprocess:
        mock_subprocess.check_output.return_value = b"value\n"
        out = op_lookup('ANY_TEST_VALUE', field_name='abc')
        mock_Popen = mock_subprocess.Popen
        mock_ps = mock_Popen.return_value
        mock_Popen.assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'],
                                      stdout=mock_subprocess.PIPE)
        mock_subprocess.check_output.\
            assert_called_with(['op', 'get', 'item', '-', '--fields', 'abc'],
                               stdin=mock_ps.stdout)
        assert out == "value"


def test_op_smart_lookup():
    with patch('op_env.op.op_lookup') as mock_op_lookup,\
         patch('op_env.op.op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle']
        ret = op_smart_lookup('ENVVARNAME')
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        mock_op_lookup.assert_called_with('ENVVARNAME', field_name='floogle')
        assert ret == mock_op_lookup.return_value


def test_op_lookup():
    with patch('op_env.op.subprocess') as mock_subprocess:
        mock_subprocess.check_output.return_value = b"value\n"
        out = op_lookup('ANY_TEST_VALUE')
        mock_Popen = mock_subprocess.Popen
        mock_ps = mock_Popen.return_value
        mock_Popen.assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'],
                                      stdout=mock_subprocess.PIPE)
        mock_subprocess.check_output.\
            assert_called_with(['op', 'get', 'item', '-', '--fields', 'password'],
                               stdin=mock_ps.stdout)
        assert out == "value"


def test_parse_args_run_command_with_long_env_variables():
    argv = ['op-env', 'run', '-e', 'DUMMY', '--environment', 'DUMMY2', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'],
                    'environment': ['DUMMY', 'DUMMY2'],
                    'subparser_name': 'run'}


def test_parse_args_run_command_with_multiple_variables():
    argv = ['op-env', 'run', '-e', 'DUMMY', '-e', 'DUMMY2', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'],
                    'environment': ['DUMMY', 'DUMMY2'],
                    'subparser_name': 'run'}


def test_parse_args_run_command_with_arguments():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['DUMMY'],
                    'subparser_name': 'run'}


def test_parse_args_run_simple():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'], 'environment': ['DUMMY'], 'subparser_name': 'run'}


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
