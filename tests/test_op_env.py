#!/usr/bin/env python

"""Tests for `op_env` package."""

import argparse
import io
import os
import subprocess
import tempfile
from unittest.mock import call, patch

import pytest
import yaml


from op_env._cli import parse_argv, process_args
from op_env.op import (
    _op_fields_to_try,
    NoEntriesOPLookupError,
    NoFieldValueOPLookupError,
    op_lookup,
    op_smart_lookup,
    TooManyEntriesOPLookupError,
)


@pytest.fixture
def list_of_number_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        contents = [123, 456]
        yaml.dump(contents, yaml_file)
        yaml_file.flush()
        yield yaml_file.name


@pytest.fixture
def number_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        contents = 123
        yaml.dump(contents, yaml_file)
        yaml_file.flush()
        yield yaml_file.name


@pytest.fixture
def string_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        contents = 'foo'
        yaml.dump(contents, yaml_file)
        yaml_file.flush()
        yield yaml_file.name


@pytest.fixture
def object_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        contents = {'foo': 'bar'}
        yaml.dump(contents, yaml_file)
        yaml_file.flush()
        yield yaml_file.name


@pytest.fixture
def invalid_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        yaml_file.write('"')
        yaml_file.flush()
        yield yaml_file.name


@pytest.fixture
def empty_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        yield yaml_file.name


@pytest.fixture
def one_item_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        contents = ['VARA']
        yaml.dump(contents, yaml_file)
        yaml_file.flush()
        yield yaml_file.name


@pytest.fixture
def two_item_yaml_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as yaml_file:
        contents = ['VAR1', 'VAR2']
        yaml.dump(contents, yaml_file)
        yaml_file.flush()
        yield yaml_file.name


def test_process_args_shows_json_with_simple_env():
    with patch('op_env._cli.op_smart_lookup') as mock_op_lookup,\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        args = {'operation': 'json', 'environment': ['a']}
        mock_op_lookup.return_value = "1"
        process_args(args)
        assert stdout_stringio.getvalue() == '{"a": "1"}\n'
        mock_op_lookup.assert_called_with('a')


def test_process_args_runs_simple_command_with_simple_env():
    with patch('op_env._cli.subprocess') as mock_subprocess,\
         patch('op_env._cli.op_smart_lookup') as mock_op_lookup,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True):
        command = ['env']
        args = {'operation': 'run', 'command': command,
                'environment': ['a']}
        process_args(args)
        mock_op_lookup.assert_called_with('a')
        mock_subprocess.check_call.assert_called_with(command,
                                                      env={'a': mock_op_lookup.return_value,
                                                           'ORIGINAL_ENV': 'TRUE'})


def test_process_args_shows_env_with_variables_needing_escape():
    def fake_op_smart_lookup(k):
        return {
            'a': "'",
            'c': 'd',
         }[k]

    with patch('op_env._cli.op_smart_lookup', new=fake_op_smart_lookup),\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True),\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        args = {'operation': 'sh', 'environment': ['a', 'c']}
        process_args(args)
        assert stdout_stringio.getvalue() == 'a=\'\'"\'"\'\'; export a\nc=d; export c\n'


def test_process_args_shows_env_with_multiple_variables():
    def fake_op_smart_lookup(k):
        return {
            'a': 'b',
            'c': 'd',
         }[k]

    with patch('op_env._cli.op_smart_lookup', new=fake_op_smart_lookup),\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True),\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        args = {'operation': 'sh', 'environment': ['a', 'c']}
        process_args(args)
        assert stdout_stringio.getvalue() == 'a=b; export a\nc=d; export c\n'


def test_process_args_shows_env_with_simple_env():
    with patch('op_env._cli.op_smart_lookup') as mock_op_lookup,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True),\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        mock_op_lookup.return_value = 'b'
        args = {'operation': 'sh', 'environment': ['a']}
        process_args(args)
        assert stdout_stringio.getvalue() == 'a=b; export a\n'
        mock_op_lookup.assert_called_with('a')


def test_process_args_runs_simple_command():
    with patch('op_env._cli.subprocess') as mock_subprocess,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True):
        command = ['env']
        args = {'operation': 'run', 'command': command,
                'environment': []}
        process_args(args)
        mock_subprocess.check_call.assert_called_with(command, env={
            'ORIGINAL_ENV': 'TRUE',
        })


def test_process_args_rejects_non_run():
    with patch('op_env.op.subprocess'):  # for safety
        with pytest.raises(ValueError):
            args = {'operation': 'definitely-not-run'}
            process_args(args)


def test_fields_to_try_breaks_on_double_underscore_and_underscore():
    with patch('op_env.op.subprocess'):  # for safety
        out = _op_fields_to_try('ABC__FLOOGLE_BAR')
        assert out == ['abc__floogle_bar', 'floogle_bar', 'bar', 'password']


def test_fields_to_try_breaks_on_double_underscore():
    with patch('op_env.op.subprocess'):  # for safety
        out = _op_fields_to_try('ABC__FLOOGLE')
        assert out == ['abc__floogle', 'floogle', 'password']


def test_fields_to_try_conversion_username():
    with patch('op_env.op.subprocess'):  # for safety
        out = _op_fields_to_try('ABC_USER')
        assert out == ['abc_user', 'user', 'username', 'password']


def test_fields_to_try_multiple_words():
    with patch('op_env.op.subprocess'):  # for safety
        out = _op_fields_to_try('ABC_FLOOGLE')
        assert out == ['abc_floogle', 'floogle', 'password']


def test_fields_to_try_simple():
    with patch('op_env.op.subprocess'):  # for safety
        out = _op_fields_to_try('ABC')
        assert out == ['abc', 'password']


def test_op_lookup_no_field_value():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b"[{}]"
        get_output = b"\n"
        mock_subprocess.check_output.side_effect = [
            list_output,
            get_output,
        ]
        with pytest.raises(NoFieldValueOPLookupError,
                           match=('1Passsword entry with tag '
                                  'ANY_TEST_VALUE has no value for field abc')):
            op_lookup('ANY_TEST_VALUE', field_name='abc')
        mock_subprocess.check_output.\
            assert_has_calls([call(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE']),
                              call(['op', 'get', 'item', '-', '--fields', 'abc'],
                                   input=list_output)])


def test_op_lookup_too_few_entries():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b"[]"
        mock_subprocess.check_output.return_value = list_output
        with pytest.raises(NoEntriesOPLookupError,
                           match='No 1Password entries with tag ANY_TEST_VALUE found'):
            op_lookup('ANY_TEST_VALUE', field_name='abc')
        mock_subprocess.check_output.\
            assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'])


def test_op_lookup_too_many_entries():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b"[{}, {}]"
        mock_subprocess.check_output.return_value = list_output
        with pytest.raises(TooManyEntriesOPLookupError,
                           match='Too many 1Password entries with tag ANY_TEST_VALUE'):
            op_lookup('ANY_TEST_VALUE', field_name='abc')
        mock_subprocess.check_output.\
            assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'])


def test_op_lookup_specific_field():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b"[{}]"
        get_output = b"get_results\n"
        mock_subprocess.check_output.side_effect = [
            list_output,
            get_output,
        ]
        out = op_lookup('ANY_TEST_VALUE', field_name='abc')
        mock_subprocess.check_output.\
            assert_has_calls([call(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE']),
                              call(['op', 'get', 'item', '-', '--fields', 'abc'],
                                   input=list_output)])
        assert out == "get_results"


def test_op_smart_lookup_multiple_fields():
    with patch('op_env.op.op_lookup') as mock_op_lookup,\
         patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle', 'blah']
        mock_op_lookup.return_value = 'result value'
        ret = op_smart_lookup('ENVVARNAME')
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        mock_op_lookup.assert_called_with('ENVVARNAME', field_name='floogle')
        assert ret == 'result value'


def test_op_smart_lookup_multiple_fields_all_errors():
    with patch('op_env.op.op_lookup') as mock_op_lookup,\
         patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle', 'blah']
        mock_op_lookup.side_effect = [NoFieldValueOPLookupError,
                                      NoFieldValueOPLookupError]
        with pytest.raises(NoFieldValueOPLookupError,
                           match=('1Passsword entry with tag '
                                  'ENVVARNAME has no value for '
                                  'the fields tried: '
                                  "floogle, blah.  Please populate "
                                  'one of these fields in 1Password.')):
            op_smart_lookup('ENVVARNAME')
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        mock_op_lookup.assert_has_calls([call('ENVVARNAME', field_name='floogle'),
                                         call('ENVVARNAME', field_name='blah')])


def test_op_smart_lookup_single_field_with_error():
    with patch('op_env.op.op_lookup') as mock_op_lookup,\
         patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle']
        mock_op_lookup.side_effect = NoFieldValueOPLookupError
        with pytest.raises(NoFieldValueOPLookupError):
            op_smart_lookup('ENVVARNAME')
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        mock_op_lookup.assert_called_with('ENVVARNAME', field_name='floogle')


def test_op_smart_lookup_multiple_fields_chooses_second():
    with patch('op_env.op.op_lookup') as mock_op_lookup,\
         patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle', 'blah']
        mock_op_lookup.side_effect = [NoFieldValueOPLookupError,
                                      'result value']
        ret = op_smart_lookup('ENVVARNAME')
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        mock_op_lookup.assert_has_calls([call('ENVVARNAME', field_name='floogle'),
                                         call('ENVVARNAME', field_name='blah')])
        assert ret == 'result value'


def test_op_smart_lookup_chooses_first():
    with patch('op_env.op.op_lookup') as mock_op_lookup,\
         patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle']
        ret = op_smart_lookup('ENVVARNAME')
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        mock_op_lookup.assert_called_with('ENVVARNAME', field_name='floogle')
        assert ret == mock_op_lookup.return_value


def test_parse_args_json_operation_no_env_variables():
    argv = ['op-env', 'json']
    args = parse_argv(argv)
    assert args == {'environment': [],
                    'operation': 'json'}


def test_parse_args_run_operation_with_long_env_variables():
    argv = ['op-env', 'run', '-e', 'DUMMY', '--environment', 'DUMMY2', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'],
                    'environment': ['DUMMY', 'DUMMY2'],
                    'operation': 'run'}


def test_parse_args_run_operation_no_env_variables():
    argv = ['op-env', 'run', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'],
                    'environment': [],
                    'operation': 'run'}


def test_parse_args_run_operation_with_multiple_environment_arguments():
    argv = ['op-env', 'run', '-e', 'DUMMY', '-e', 'DUMMY2', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'],
                    'environment': ['DUMMY', 'DUMMY2'],
                    'operation': 'run'}


def test_parse_args_run_operation_with_environment_arguments():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['DUMMY'],
                    'operation': 'run'}


def test_parse_args_run_operation_with_multiple_yaml_and_environment_arguments(one_item_yaml_file,
                                                                               two_item_yaml_file):
    argv = ['op-env', 'run', '-e', 'VAR_1', '-e', 'VAR0',
            '-y', two_item_yaml_file, '-y', one_item_yaml_file,
            'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['VAR_1', 'VAR0', 'VAR1', 'VAR2', 'VARA'],
                    'operation': 'run'}


def test_parse_args_run_operation_with_yaml_arguments_and_environment_arguments(two_item_yaml_file):
    argv = ['op-env', 'run', '-e', 'VAR0', '-y', two_item_yaml_file, 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['VAR0', 'VAR1', 'VAR2'],
                    'operation': 'run'}


def test_list_of_numbers_yaml_argument(list_of_number_yaml_file):
    argv = ['op-env', 'run', '-y', list_of_number_yaml_file, 'mycmd', '1', '2', '3']
    with pytest.raises(argparse.ArgumentTypeError,
                       match='YAML file must contain a list of strings'):
        parse_argv(argv)


def test_parse_args_run_operation_with_number_file_yaml_argument(number_yaml_file):
    argv = ['op-env', 'run', '-y', number_yaml_file, 'mycmd', '1', '2', '3']
    with pytest.raises(argparse.ArgumentTypeError, match='YAML file must be a list; found'):
        parse_argv(argv)


def test_parse_args_run_operation_with_string_file_yaml_argument(string_yaml_file):
    argv = ['op-env', 'run', '-y', string_yaml_file, 'mycmd', '1', '2', '3']
    with pytest.raises(argparse.ArgumentTypeError, match='YAML file must be a list; found'):
        parse_argv(argv)


def test_parse_args_run_operation_with_object_file_yaml_argument(object_yaml_file):
    argv = ['op-env', 'run', '-y', object_yaml_file, 'mycmd', '1', '2', '3']
    with pytest.raises(argparse.ArgumentTypeError, match='YAML file must be a list; found'):
        parse_argv(argv)


def test_parse_args_run_operation_with_invalid_file_yaml_argument(invalid_yaml_file):
    argv = ['op-env', 'run', '-y', invalid_yaml_file, 'mycmd', '1', '2', '3']
    with pytest.raises(yaml.scanner.ScannerError):
        parse_argv(argv)


def test_parse_args_run_operation_with_empty_file_yaml_argument(empty_file):
    argv = ['op-env', 'run', '-y', empty_file, 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': [],
                    'operation': 'run'}


def test_parse_args_run_operation_with_yaml_argument(two_item_yaml_file):
    argv = ['op-env', 'run', '-y', two_item_yaml_file, 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['VAR1', 'VAR2'],
                    'operation': 'run'}


def test_parse_args_run_simple():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'mycmd']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd'], 'environment': ['DUMMY'], 'operation': 'run'}


def test_parse_args_sh_simple():
    argv = ['op-env', 'sh', '-e', 'DUMMY']
    args = parse_argv(argv)
    assert args == {'environment': ['DUMMY'], 'operation': 'sh'}


@pytest.mark.skip(reason="need to mock op binary in test PATH")
def test_cli_run():
    argv = ['op-env', 'run', '-e', 'DUMMY', 'env']
    expected_envvar = 'DUMMY=dummyvalue'
    actual_output = subprocess.check_output(argv).decode('utf-8')
    assert expected_envvar in actual_output


def test_cli_help_run():
    expected_help = """usage: op-env run [-h] [--environment ENVVAR] [--yaml-environment YAMLENV] command [command ...]

Run the specified command with the given environment variables

positional arguments:
  command               Command to run with the environment set from 1Password

optional arguments:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
  --yaml-environment YAMLENV, -y YAMLENV
                        YAML config specifying a list of environment variable names to set
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', 'run', '--help'], env=env).decode('utf-8')
    assert actual_help == expected_help


def test_cli_help_json():
    expected_help = """usage: op-env json [-h] [--environment ENVVAR] [--yaml-environment YAMLENV]

Produce simple JSON on stdout mapping requested env variables to values

optional arguments:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
  --yaml-environment YAMLENV, -y YAMLENV
                        YAML config specifying a list of environment variable names to set
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', 'json', '--help'], env=env).decode('utf-8')
    assert actual_help == expected_help


def test_cli_help_sh():
    expected_help = """usage: op-env sh [-h] [--environment ENVVAR] [--yaml-environment YAMLENV]

Produce commands on stdout that can be 'eval'ed to set variables in current shell

optional arguments:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
  --yaml-environment YAMLENV, -y YAMLENV
                        YAML config specifying a list of environment variable names to set
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', 'sh', '--help'], env=env).decode('utf-8')
    assert actual_help == expected_help


def test_cli_no_args():
    expected_help = """usage: op-env [-h] {run,json,sh} ...
op-env: error: the following arguments are required: operation
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    completed_process = subprocess.run(['op-env'], env=env,
                                       stderr=subprocess.PIPE)
    actual_help = completed_process.stderr.decode('utf-8')
    assert actual_help == expected_help
    assert completed_process.returncode == 2


def test_cli_help():
    expected_help = """usage: op-env [-h] {run,json,sh} ...

positional arguments:
  {run,json,sh}
    run          Run the specified command with the given environment variables
    json         Produce simple JSON on stdout mapping requested env variables to values
    sh           Produce commands on stdout that can be 'eval'ed to set variables in current shell

optional arguments:
  -h, --help     show this help message and exit
"""
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', '--help'],
                                          env=env).decode('utf-8')
    assert actual_help == expected_help
