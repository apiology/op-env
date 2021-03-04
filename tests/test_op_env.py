#!/usr/bin/env python

"""Tests for `op_env` package."""

import argparse
import io
import os
import subprocess
import tempfile
from typing import Dict
from unittest.mock import call, patch

import pytest
import yaml


from op_env._cli import Arguments, parse_argv, process_args
from op_env.op import (
    do_smart_lookups,
    _op_fields_to_try,
    _op_pluck_correct_field,
    EnvVarName,
    FieldName,
    FieldValue,
    InvalidTagOPLookupError,
    NoEntriesOPLookupError,
    NoFieldValueOPLookupError,
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


def test_process_args_shows_json_with_simple_env() -> None:
    with patch('op_env.op._op_list_items') as mock_op_list_items,\
         patch('op_env.op._op_consolidated_fields') as mock_op_consolidated_fields,\
         patch('op_env.op._op_get_item') as mock_op_get_item,\
         patch('op_env.op._op_pluck_correct_field') as mock_op_pluck_correct_field,\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        mock_list_items_output = mock_op_list_items.return_value
        mock_all_fields_to_seek = mock_op_consolidated_fields.return_value
        Dict[EnvVarName, Dict[FieldName, FieldValue]]
        retval: Dict[EnvVarName, Dict[FieldName, FieldValue]] = {
            EnvVarName('a'): {
                FieldName('password'): FieldValue('1'),
            }}
        mock_op_get_item.return_value = retval
        env_var_names = [EnvVarName('a')]
        args: Arguments = {
            'operation': 'json',
            'environment': env_var_names,
            'command': []
        }
        mock_op_pluck_correct_field.return_value = '1'
        process_args(args)
        assert stdout_stringio.getvalue() == '{"a": "1"}\n'
        mock_op_list_items.assert_called_with(env_var_names)
        mock_op_consolidated_fields.assert_called_with(env_var_names)
        mock_op_pluck_correct_field.assert_called_with('a', {'password': '1'})
        mock_op_get_item.assert_called_with(mock_list_items_output,
                                            env_var_names,
                                            mock_all_fields_to_seek)


def test_process_args_runs_simple_command_with_simple_env():
    with patch('op_env._cli.subprocess') as mock_subprocess,\
         patch('op_env._cli.do_smart_lookups') as mock_do_smart_lookups,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True):
        command = ['env']
        args = {'operation': 'run', 'command': command,
                'environment': ['a']}
        mock_do_smart_lookups.return_value = {'a': '1'}
        process_args(args)
        mock_do_smart_lookups.assert_called_with(['a'])
        mock_subprocess.check_call.assert_called_with(command,
                                                      env={'a': '1',
                                                           'ORIGINAL_ENV': 'TRUE'})


def test_process_args_shows_env_with_variables_needing_escape():
    with patch('op_env._cli.do_smart_lookups') as mock_do_smart_lookups,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True),\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        args = {'operation': 'sh', 'environment': ['a', 'c']}
        mock_do_smart_lookups.return_value = {'a': "'", 'c': 'd'}
        process_args(args)
        assert stdout_stringio.getvalue() == 'a=\'\'"\'"\'\'; export a\nc=d; export c\n'


def test_process_args_shows_env_with_multiple_variables():
    def fake_op_smart_lookup(k):
        return {
            'a': 'b',
            'c': 'd',
         }[k]

    with patch('op_env._cli.do_smart_lookups') as mock_do_smart_lookups,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True),\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        mock_do_smart_lookups.return_value = {'a': 'b', 'c': 'd'}
        args = {'operation': 'sh', 'environment': ['a', 'c']}
        process_args(args)
        assert stdout_stringio.getvalue() == 'a=b; export a\nc=d; export c\n'


def test_process_args_shows_env_with_simple_env():
    with patch('op_env._cli.do_smart_lookups') as mock_do_smart_lookups,\
         patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True),\
         patch('sys.stdout', new_callable=io.StringIO) as stdout_stringio:
        mock_do_smart_lookups.return_value = {'a': 'b'}
        args = {'operation': 'sh', 'environment': ['a']}
        process_args(args)
        assert stdout_stringio.getvalue() == 'a=b; export a\n'


@pytest.mark.skip(reason="need to mock op binary in test PATH")
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


def test_op_do_smart_lookups_multiple_entries():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = \
            b'[{"overview":{"tags":["ANY_TEST_VALUE"]}},' \
            b'{"overview": {"tags": ["ANOTHER_TEST_VALUE"]}}]'
        post_processed_list_output = \
            b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}, ' \
            b'{"overview": {"tags": ["ANOTHER_TEST_VALUE"]}}]'
        get_output = \
            b'{"any_test_value":"","another_test_value":"","password":"any","value":""}\n' \
            b'{"any_test_value":"","another_test_value":"another",'\
            b'"password":"get_results","value":""}'
        mock_subprocess.check_output.side_effect = [
            list_output,
            get_output,
        ]
        out = do_smart_lookups(['ANY_TEST_VALUE', 'ANOTHER_TEST_VALUE'])
        mock_subprocess.check_output.\
            assert_has_calls([call(['op', 'list', 'items', '--tags',
                                    'ANY_TEST_VALUE,ANOTHER_TEST_VALUE']),
                              call(['op', 'get', 'item', '-', '--fields',
                                    'another_test_value,any_test_value,password,value'],
                                   input=post_processed_list_output)])
        assert out == {
            'ANY_TEST_VALUE': 'any',
            'ANOTHER_TEST_VALUE': 'another'
        }


def test_do_smart_lookups_no_field_value():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b'[{"overview":{"tags":["ANY_TEST_VALUE"]}}]'
        post_processed_list_output = b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}]'
        get_output = b'{"password":""}\n'
        mock_subprocess.check_output.side_effect = [
            list_output,
            get_output,
        ]
        with pytest.raises(NoFieldValueOPLookupError,
                           match=('1Passsword entry with tag ANY_TEST_VALUE '
                                  'has no value for the fields tried: '
                                  'any_test_value, value, password.  '
                                  'Please populate one of these fields in 1Password.')):
            do_smart_lookups(['ANY_TEST_VALUE'])
        mock_subprocess.check_output.\
            assert_has_calls([call(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE']),
                              call(['op', 'get', 'item', '-', '--fields',
                                    'any_test_value,password,value'],
                                   input=post_processed_list_output)])


def test_do_smart_lookups_too_few_entries():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b"[]"
        mock_subprocess.check_output.return_value = list_output
        with pytest.raises(NoEntriesOPLookupError,
                           match='No 1Password entries with tag ANY_TEST_VALUE found'):
            do_smart_lookups(['ANY_TEST_VALUE'])
        mock_subprocess.check_output.\
            assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'])


def test_do_smart_lookups_too_many_entries():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = \
            b'[{"overview":{"tags":["ANY_TEST_VALUE"]}},{"overview":{"tags":["ANY_TEST_VALUE"]}}]'
        mock_subprocess.check_output.return_value = list_output
        with pytest.raises(TooManyEntriesOPLookupError,
                           match='Too many 1Password entries with tag ANY_TEST_VALUE'):
            do_smart_lookups(['ANY_TEST_VALUE'])
        mock_subprocess.check_output.\
            assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'])


def test_op_do_smart_lookups_comma_in_env():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}]'
        get_output = b'{"any_test_value":"","password":"get_results","value":""}\n'
        mock_subprocess.check_output.side_effect = [
            list_output,
            get_output,
        ]
        with pytest.raises(InvalidTagOPLookupError,
                           match='1Password does not support tags with commas'):
            do_smart_lookups(['ENV_WITH_,_IN_IT'])
        mock_subprocess.check_output.assert_not_called()


def test_op_do_smart_lookups_one_var():
    with patch('op_env.op.subprocess') as mock_subprocess:
        list_output = b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}]'
        get_output = b'{"any_test_value":"","password":"get_results","value":""}\n'
        mock_subprocess.check_output.side_effect = [
            list_output,
            get_output,
        ]
        out = do_smart_lookups(['ANY_TEST_VALUE'])
        mock_subprocess.check_output.\
            assert_has_calls([call(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE']),
                              call(['op', 'get', 'item', '-', '--fields',
                                    'any_test_value,password,value'],
                                   input=list_output)])
        assert out == {'ANY_TEST_VALUE': 'get_results'}


def test_op_pluck_correct_field_multiple_fields():
    with patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle', 'blah']
        ret = _op_pluck_correct_field('ENVVARNAME', {'blah': '', 'floogle': 'result value'})
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        assert ret == 'result value'


def test_op_pluck_correct_field_multiple_fields_all_errors():
    with patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle', 'blah']
        with pytest.raises(NoFieldValueOPLookupError,
                           match=('1Passsword entry with tag '
                                  'ENVVARNAME has no value for '
                                  'the fields tried: '
                                  "floogle, blah.  Please populate "
                                  'one of these fields in 1Password.')):
            _op_pluck_correct_field('ENVVARNAME', {'floogle': '', 'blah': ''})
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')


def test_op_pluck_correct_field_single_field_with_error():
    with patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle']
        with pytest.raises(NoFieldValueOPLookupError):
            _op_pluck_correct_field('ENVVARNAME', {'floogle': ''})
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')


def test_op_pluck_correct_field_multiple_fields_chooses_second():
    with patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle', 'blah']
        ret = _op_pluck_correct_field('ENVVARNAME', {'floogle': '', 'blah': 'result value'})
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        assert ret == 'result value'


def test_op_pluck_correct_field_chooses_first():
    with patch('op_env.op._op_fields_to_try') as mock_op_fields_to_try:
        mock_op_fields_to_try.return_value = ['floogle']
        ret = _op_pluck_correct_field('ENVVARNAME', {'floogle': 'myvalue'})
        mock_op_fields_to_try.assert_called_with('ENVVARNAME')
        assert ret == 'myvalue'


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
