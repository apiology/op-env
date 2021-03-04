from collections import OrderedDict
import json
import subprocess
from typing import Any, Collection, Dict, List, NewType, Sequence, Set, TypeVar

from typing_extensions import TypedDict

EnvVarName = NewType('EnvVarName', str)


class OpListItemsEntryOverview(TypedDict, total=False):
    tags: List[EnvVarName]


class OpListItemsEntry(TypedDict, total=False):
    overview: OpListItemsEntryOverview


OpListItemsOpaqueOutput = NewType('OpListItemsOpaqueOutput', List[Any])

FieldName = NewType('FieldName', str)

FieldValue = NewType('FieldValue', str)


class OPLookupError(LookupError):
    pass


class TooManyEntriesOPLookupError(OPLookupError):
    pass


class NoEntriesOPLookupError(OPLookupError):
    pass


class NoFieldValueOPLookupError(OPLookupError):
    pass


class InvalidTagOPLookupError(OPLookupError):
    pass


def _op_list_items(env_var_names: List[EnvVarName]) -> OpListItemsOpaqueOutput:
    list_command = ['op', 'list', 'items', '--tags',
                    ','.join(env_var_names)]
    list_items_json_docs_bytes = subprocess.check_output(list_command)
    # list_items_json_docs_str = list_items_json_docs_bytes.decode('utf-8')
    list_items_data: List[OpListItemsEntry] = json.loads(list_items_json_docs_bytes)
    by_env_var_name: Dict[EnvVarName, OpListItemsEntry] = {}
    for entry in list_items_data:
        for env_var_name in entry['overview']['tags']:
            if env_var_name in by_env_var_name:
                raise TooManyEntriesOPLookupError("Too many 1Password entries "
                                                  f"with tag {env_var_name} found")
            else:
                by_env_var_name[env_var_name] = entry
    ordered_list_items_data = []
    for env_var_name in env_var_names:
        if env_var_name not in by_env_var_name:
            raise NoEntriesOPLookupError(f"No 1Password entries with tag {env_var_name} found")
        else:
            ordered_list_items_data.append(by_env_var_name[env_var_name])
    return OpListItemsOpaqueOutput(ordered_list_items_data)


def _op_get_item(list_items_output: OpListItemsOpaqueOutput,
                 env_var_names: Collection[EnvVarName],
                 all_fields_to_seek: Collection[FieldName]) ->\
                 Dict[EnvVarName, Dict[FieldName, FieldValue]]:
    sorted_fields_to_seek = sorted(all_fields_to_seek)
    get_command: List[str] = ['op', 'get', 'item', '-', '--fields',
                              ','.join(sorted_fields_to_seek)]
    list_items_output_raw = json.dumps(list_items_output).encode('utf-8')
    field_values_json_docs_bytes = subprocess.check_output(get_command,
                                                           input=list_items_output_raw)
    field_values_json_docs_str = field_values_json_docs_bytes.decode('utf-8')
    field_values_data = [
        json.loads(field_values_json)
        for field_values_json
        in field_values_json_docs_str.split('\n')
        if field_values_json != ''
    ]
    return {
        env_var_name: field_values
        for (env_var_name, field_values)
        in zip(env_var_names, field_values_data)
    }


def _last_underscored_component_lowercased(env_var_name: EnvVarName) -> FieldName:
    components = env_var_name.split('_')
    return FieldName(components[-1].lower())


def _last_double_underscored_component_lowercased(env_var_name: EnvVarName) -> FieldName:
    components = env_var_name.split('__')
    return FieldName(components[-1].lower())


def _all_lowercased(env_var_name: EnvVarName) -> FieldName:
    return FieldName(env_var_name.lower())


T = TypeVar('T')


def _uniqify(fields: Sequence[T]) -> List[T]:
    "Removes duplicates but preserves order"
    # https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
    return list(OrderedDict.fromkeys(fields))


def _aliases(fields: List[FieldName]) -> List[FieldName]:
    if 'user' in fields:
        return [FieldName('username')]
    else:
        return []


def _op_consolidated_fields(env_var_names: Collection[EnvVarName]) -> Set[FieldName]:
    return {
        field_name
        for env_var_name in env_var_names
        for field_name in _op_fields_to_try(env_var_name)
    }


def _op_fields_to_try(env_var_name: EnvVarName) -> List[FieldName]:
    candidates: List[FieldName] = _uniqify([
        _all_lowercased(env_var_name),
        _last_double_underscored_component_lowercased(env_var_name),
        _last_underscored_component_lowercased(env_var_name),
    ])
    return candidates + _aliases(candidates) + [FieldName('password')]


def _op_pluck_correct_field(env_var_name: EnvVarName,
                            field_values: Dict[FieldName,
                                               FieldValue]) -> FieldValue:
    fields = _op_fields_to_try(env_var_name)
    for field in fields:
        if field in field_values and field_values[field] != '':
            return field_values[field]
    raise NoFieldValueOPLookupError('1Passsword entry with tag '
                                    f'{env_var_name} has no value for '
                                    'the fields tried: '
                                    f'{", ".join(fields)}.  Please populate '
                                    'one of these fields in 1Password.')


def validate_env_var_names(env_var_names: List[EnvVarName]) -> None:
    for env_var_name in env_var_names:
        if ',' in env_var_name:
            raise InvalidTagOPLookupError('1Password does not support tags with commas')


def do_smart_lookups(env_var_names: List[EnvVarName]) -> Dict[str, str]:
    validate_env_var_names(env_var_names)
    list_items_output = _op_list_items(env_var_names)
    all_fields_to_seek = _op_consolidated_fields(env_var_names)
    field_values_for_envvars = _op_get_item(list_items_output,
                                            env_var_names,
                                            all_fields_to_seek)
    return {
        env_var_name: _op_pluck_correct_field(env_var_name, field_values_for_envvars[env_var_name])
        for env_var_name in field_values_for_envvars
    }
