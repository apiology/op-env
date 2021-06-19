#!/usr/bin/env python

"""Tests for `op_env` package."""

import argparse
import io
import os
import subprocess
import sys
import tempfile
from typing import Dict
from unittest.mock import call, patch

import pytest
import yaml


import op_env
from op_env._cli import Arguments, main, parse_argv, process_args
from op_env.op import (
    _op_fields_to_try,
    _op_pluck_correct_field,
    do_smart_lookups,
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


@pytest.fixture
def two_item_text_file():
    with tempfile.NamedTemporaryFile(mode="w+t") as text_file:
        contents = ['TVAR1', 'TVAR2']
        for item in contents:
            text_file.write(item)
            text_file.write("\n")
        text_file.flush()
        yield text_file.name


@patch('op_env.op._op_list_items', autospec=op_env.op._op_list_items)
@patch('op_env.op._op_consolidated_fields', autospec=op_env.op._op_consolidated_fields)
@patch('op_env.op._op_get_item', autospec=op_env.op._op_get_item)
@patch('op_env.op._op_pluck_correct_field', autospec=op_env.op._op_pluck_correct_field)
@patch('sys.stdout', new_callable=io.StringIO)
def test_process_args_shows_json_with_simple_env(stdout_stringio,
                                                 op_pluck_correct_field,
                                                 op_get_item,
                                                 op_consolidated_fields,
                                                 op_list_items) -> None:
    list_items_output = op_list_items.return_value
    all_fields_to_seek = op_consolidated_fields.return_value
    Dict[EnvVarName, Dict[FieldName, FieldValue]]
    retval: Dict[EnvVarName, Dict[FieldName, FieldValue]] = {
        EnvVarName('a'): {
            FieldName('password'): FieldValue('1'),
        }}
    op_get_item.return_value = retval
    env_var_names = [EnvVarName('a')]
    args: Arguments = {
        'operation': 'json',
        'environment': env_var_names,
        'command': []
    }
    op_pluck_correct_field.return_value = '1'
    process_args(args)
    assert stdout_stringio.getvalue() == '{"a": "1"}\n'
    op_list_items.assert_called_with(env_var_names)
    op_consolidated_fields.assert_called_with(env_var_names)
    op_pluck_correct_field.assert_called_with('a', {'password': '1'})
    op_get_item.assert_called_with(list_items_output,
                                   env_var_names,
                                   all_fields_to_seek)


@patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True)
@patch('op_env._cli.do_smart_lookups', autospec=op_env._cli.do_smart_lookups)
@patch('op_env._cli.subprocess', autospec=op_env._cli.subprocess)
def test_process_args_runs_simple_command_with_simple_env(subprocess,
                                                          do_smart_lookups):
    command = ['env']
    args = {'operation': 'run', 'command': command,
            'environment': ['a']}
    do_smart_lookups.return_value = {'a': '1'}
    process_args(args)
    do_smart_lookups.assert_called_with(['a'])
    subprocess.check_call.assert_called_with(command,
                                             env={'a': '1',
                                                  'ORIGINAL_ENV': 'TRUE'})


@patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True)
@patch('op_env._cli.do_smart_lookups', autospec=op_env._cli.do_smart_lookups)
@patch('sys.stdout', new_callable=io.StringIO)
def test_process_args_shows_env_with_variables_needing_escape(stdout_stringio,
                                                              do_smart_lookups):
    args = {'operation': 'sh', 'environment': ['a', 'c']}
    do_smart_lookups.return_value = {'a': "'", 'c': 'd'}
    process_args(args)
    assert stdout_stringio.getvalue() == 'a=\'\'"\'"\'\'; export a\nc=d; export c\n'


@patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True)
@patch('op_env._cli.do_smart_lookups', autospec=op_env._cli.do_smart_lookups)
@patch('sys.stdout', new_callable=io.StringIO)
def test_process_args_shows_env_with_multiple_variables(stdout_stringio,
                                                        do_smart_lookups):
    def fake_op_smart_lookup(k):
        return {
            'a': 'b',
            'c': 'd',
         }[k]

    do_smart_lookups.return_value = {'a': 'b', 'c': 'd'}
    args = {'operation': 'sh', 'environment': ['a', 'c']}
    process_args(args)
    assert stdout_stringio.getvalue() == 'a=b; export a\nc=d; export c\n'


@patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True)
@patch('op_env._cli.do_smart_lookups', autospec=op_env._cli.do_smart_lookups)
@patch('sys.stdout', new_callable=io.StringIO)
def test_process_args_shows_env_with_simple_env(stdout_stringio,
                                                do_smart_lookups):
    do_smart_lookups.return_value = {'a': 'b'}
    args = {'operation': 'sh', 'environment': ['a']}
    process_args(args)
    assert stdout_stringio.getvalue() == 'a=b; export a\n'


@pytest.mark.skip(reason="need to mock op binary in test PATH")
@patch.dict(os.environ, {'ORIGINAL_ENV': 'TRUE'}, clear=True)
@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_process_args_runs_simple_command(subprocess):
    command = ['env']
    args = {'operation': 'run', 'command': command,
            'environment': []}
    process_args(args)
    subprocess.check_call.assert_called_with(command, env={
        'ORIGINAL_ENV': 'TRUE',
    })


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_process_args_rejects_non_run(subprocess):
    with pytest.raises(ValueError):
        args = {'operation': 'definitely-not-run'}
        process_args(args)


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_fields_to_try_breaks_on_double_underscore_and_underscore(subprocess):
    out = _op_fields_to_try('ABC__FLOOGLE_BAR')
    assert out == ['abc__floogle_bar', 'floogle_bar', 'bar', 'password']


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_fields_to_try_breaks_on_double_underscore(subprocess):
    out = _op_fields_to_try('ABC__FLOOGLE')
    assert out == ['abc__floogle', 'floogle', 'password']


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_fields_to_try_conversion_username(subprocess):
    out = _op_fields_to_try('ABC_USER')
    assert out == ['abc_user', 'user', 'username', 'password']


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_fields_to_try_multiple_words(subprocess):
    out = _op_fields_to_try('ABC_FLOOGLE')
    assert out == ['abc_floogle', 'floogle', 'password']


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_fields_to_try_simple(subprocess):
    out = _op_fields_to_try('ABC')
    assert out == ['abc', 'password']


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_op_do_smart_lookups_multiple_entries(subprocess):
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
    subprocess.check_output.side_effect = [
        list_output,
        get_output,
    ]
    out = do_smart_lookups(['ANY_TEST_VALUE', 'ANOTHER_TEST_VALUE'])
    subprocess.check_output.\
        assert_has_calls([call(['op', 'list', 'items', '--tags',
                                'ANY_TEST_VALUE,ANOTHER_TEST_VALUE']),
                          call(['op', 'get', 'item', '-', '--fields',
                                'another_test_value,any_test_value,password,value'],
                               input=post_processed_list_output)])
    assert out == {
        'ANY_TEST_VALUE': 'any',
        'ANOTHER_TEST_VALUE': 'another'
    }


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_do_smart_lookups_no_field_value(subprocess):
    list_output = b'[{"overview":{"tags":["ANY_TEST_VALUE"]}}]'
    post_processed_list_output = b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}]'
    get_output = b'{"password":""}\n'
    subprocess.check_output.side_effect = [
        list_output,
        get_output,
    ]
    with pytest.raises(NoFieldValueOPLookupError,
                       match=('1Passsword entry with tag ANY_TEST_VALUE '
                              'has no value for the fields tried: '
                              'any_test_value, value, password.  '
                              'Please populate one of these fields in 1Password.')):
        do_smart_lookups(['ANY_TEST_VALUE'])
    subprocess.check_output.\
        assert_has_calls([call(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE']),
                          call(['op', 'get', 'item', '-', '--fields',
                                'any_test_value,password,value'],
                               input=post_processed_list_output)])


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_do_smart_lookups_too_few_entries(subprocess):
    list_output = b"[]"
    subprocess.check_output.return_value = list_output
    with pytest.raises(NoEntriesOPLookupError,
                       match='No 1Password entries with tag ANY_TEST_VALUE found'):
        do_smart_lookups(['ANY_TEST_VALUE'])
    subprocess.check_output.\
        assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'])


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_do_smart_lookups_too_many_entries(subprocess):
    list_output = \
        b'[{"overview":{"tags":["ANY_TEST_VALUE"]}},{"overview":{"tags":["ANY_TEST_VALUE"]}}]'
    subprocess.check_output.return_value = list_output
    with pytest.raises(TooManyEntriesOPLookupError,
                       match='Too many 1Password entries with tag ANY_TEST_VALUE'):
        do_smart_lookups(['ANY_TEST_VALUE'])
    subprocess.check_output.\
        assert_called_with(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE'])


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_op_do_smart_lookups_comma_in_env(subprocess):
    list_output = b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}]'
    get_output = b'{"any_test_value":"","password":"get_results","value":""}\n'
    subprocess.check_output.side_effect = [
        list_output,
        get_output,
    ]
    with pytest.raises(InvalidTagOPLookupError,
                       match='1Password does not support tags with commas'):
        do_smart_lookups(['ENV_WITH_,_IN_IT'])
    subprocess.check_output.assert_not_called()


@patch('op_env.op.subprocess', autospec=op_env.op.subprocess)
def test_op_do_smart_lookups_one_var(subprocess):
    list_output = b'[{"overview": {"tags": ["ANY_TEST_VALUE"]}}]'
    get_output = b'{"any_test_value":"","password":"get_results","value":""}\n'
    subprocess.check_output.side_effect = [
        list_output,
        get_output,
    ]
    out = do_smart_lookups(['ANY_TEST_VALUE'])
    subprocess.check_output.\
        assert_has_calls([call(['op', 'list', 'items', '--tags', 'ANY_TEST_VALUE']),
                          call(['op', 'get', 'item', '-', '--fields',
                                'any_test_value,password,value'],
                               input=list_output)])
    assert out == {'ANY_TEST_VALUE': 'get_results'}


@patch('op_env.op._op_fields_to_try', autospec=_op_fields_to_try)
def test_op_pluck_correct_field_multiple_fields(op_fields_to_try):
    op_fields_to_try.return_value = ['floogle', 'blah']
    ret = _op_pluck_correct_field('ENVVARNAME', {'blah': '', 'floogle': 'result value'})
    op_fields_to_try.assert_called_with('ENVVARNAME')
    assert ret == 'result value'


@patch('op_env.op._op_fields_to_try', autospec=_op_fields_to_try)
def test_op_pluck_correct_field_multiple_fields_all_errors(op_fields_to_try):
    op_fields_to_try.return_value = ['floogle', 'blah']
    with pytest.raises(NoFieldValueOPLookupError,
                       match=('1Passsword entry with tag '
                              'ENVVARNAME has no value for '
                              'the fields tried: '
                              "floogle, blah.  Please populate "
                              'one of these fields in 1Password.')):
        _op_pluck_correct_field('ENVVARNAME', {'floogle': '', 'blah': ''})
    op_fields_to_try.assert_called_with('ENVVARNAME')


@patch('op_env.op._op_fields_to_try', autospec=_op_fields_to_try)
def test_op_pluck_correct_field_single_field_with_error(op_fields_to_try):
    op_fields_to_try.return_value = ['floogle']
    with pytest.raises(NoFieldValueOPLookupError):
        _op_pluck_correct_field('ENVVARNAME', {'floogle': ''})
    op_fields_to_try.assert_called_with('ENVVARNAME')


@patch('op_env.op._op_fields_to_try', autospec=_op_fields_to_try)
def test_op_pluck_correct_field_multiple_fields_chooses_second(op_fields_to_try):

    op_fields_to_try.return_value = ['floogle', 'blah']
    ret = _op_pluck_correct_field('ENVVARNAME', {'floogle': '', 'blah': 'result value'})
    op_fields_to_try.assert_called_with('ENVVARNAME')
    assert ret == 'result value'


@patch('op_env.op._op_fields_to_try', autospec=_op_fields_to_try)
def test_op_pluck_correct_field_chooses_first(op_fields_to_try):
    op_fields_to_try.return_value = ['floogle']
    ret = _op_pluck_correct_field('ENVVARNAME', {'floogle': 'myvalue'})
    op_fields_to_try.assert_called_with('ENVVARNAME')
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


def test_parse_args_run_operation_with_yaml_arguments_and_text_environment_arguments(
        two_item_yaml_file,
        two_item_text_file
):
    argv = ['op-env', 'run',
            '-e', 'VAR0',
            '-y', two_item_yaml_file,
            '-f', two_item_text_file,
            'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['VAR0', 'VAR1', 'VAR2', 'TVAR1', 'TVAR2'],
                    'operation': 'run'}


def test_parse_args_run_operation_with_text_arguments_and_environment_arguments(two_item_text_file):
    argv = ['op-env', 'run', '-e', 'VAR0', '-f', two_item_text_file, 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['VAR0', 'TVAR1', 'TVAR2'],
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


def test_parse_args_run_operation_with_empty_file_text_argument(empty_file):
    argv = ['op-env', 'run', '-f', empty_file, 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': [],
                    'operation': 'run'}


def test_parse_args_run_operation_with_text_argument(two_item_text_file):
    argv = ['op-env', 'run', '-f', two_item_text_file, 'mycmd', '1', '2', '3']
    args = parse_argv(argv)
    assert args == {'command': ['mycmd', '1', '2', '3'],
                    'environment': ['TVAR1', 'TVAR2'],
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
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)

    expected_help = """usage: op-env run [-h] [--environment ENVVAR] [--yaml-environment YAMLENV] \
[--file-environment FILEENV] command [command ...]

Run the specified command with the given environment variables

positional arguments:
  command               Command to run with the environment set from 1Password

options:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
  --yaml-environment YAMLENV, -y YAMLENV
                        YAML config specifying a list of environment variable names to set
  --file-environment FILEENV, -f FILEENV
                        Text config specifying environment variable names to set, one on each line
"""
    if sys.version_info <= (3, 10):
        # 3.10 changed the wording a bit
        expected_help = expected_help.replace('options:', 'optional arguments:')

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', 'run', '--help'], env=env).decode('utf-8')
    assert actual_help == expected_help


def test_cli_help_json():
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)
    expected_help = """usage: op-env json [-h] [--environment ENVVAR] [--yaml-environment YAMLENV] \
[--file-environment FILEENV]

Produce simple JSON on stdout mapping requested env variables to values

options:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
  --yaml-environment YAMLENV, -y YAMLENV
                        YAML config specifying a list of environment variable names to set
  --file-environment FILEENV, -f FILEENV
                        Text config specifying environment variable names to set, one on each line
"""
    if sys.version_info <= (3, 10):
        # 3.10 changed the wording a bit
        expected_help = expected_help.replace('options:', 'optional arguments:')

    actual_help = subprocess.check_output(['op-env', 'json', '--help'], env=env).decode('utf-8')

    assert actual_help == expected_help


def test_cli_help_sh():
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)
    expected_help = """usage: op-env sh [-h] [--environment ENVVAR] [--yaml-environment YAMLENV] \
[--file-environment FILEENV]

Produce commands on stdout that can be 'eval'ed to set variables in current shell

options:
  -h, --help            show this help message and exit
  --environment ENVVAR, -e ENVVAR
                        environment variable name to set, based on item with same tag in 1Password
  --yaml-environment YAMLENV, -y YAMLENV
                        YAML config specifying a list of environment variable names to set
  --file-environment FILEENV, -f FILEENV
                        Text config specifying environment variable names to set, one on each line
"""
    if sys.version_info <= (3, 10):
        # 3.10 changed the wording a bit
        expected_help = expected_help.replace('options:', 'optional arguments:')

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
    request_long_lines = {'COLUMNS': '999', 'LINES': '25'}
    env = {}
    env.update(os.environ)
    env.update(request_long_lines)
    expected_help = """usage: op-env [-h] {run,json,sh} ...

positional arguments:
  {run,json,sh}
    run          Run the specified command with the given environment variables
    json         Produce simple JSON on stdout mapping requested env variables to values
    sh           Produce commands on stdout that can be 'eval'ed to set variables in current shell

options:
  -h, --help     show this help message and exit
"""
    if sys.version_info <= (3, 10):
        # 3.10 changed the wording a bit
        expected_help = expected_help.replace('options:', 'optional arguments:')

    # older python versions show arguments like this:
    actual_help = subprocess.check_output(['op-env', '--help'],
                                          env=env).decode('utf-8')
    assert actual_help == expected_help


@patch('op_env._cli.parse_argv', autospec=parse_argv)
@patch('op_env._cli.process_args', autospec=process_args)
def test_main(process_args, parse_argv):
    argv = object()
    args = parse_argv.return_value
    assert process_args.return_value == main(argv)
    process_args.assert_called_with(args)
