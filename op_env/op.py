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


# def op_smart_lookup(env_var_name: str) -> str:  # TODO most renamed to _op_pluck_correct_field


def _op_list_items(env_var_names: List[EnvVarName]) -> OpListItemsOpaqueOutput:
    list_command = ['op', 'list', 'items', '--tags',
                    ','.join(env_var_names)]
    list_items_json_docs_bytes = subprocess.check_output(list_command)
    # list_items_json_docs_str = list_items_json_docs_bytes.decode('utf-8')
    list_items_data: List[OpListItemsEntry] = json.loads(list_items_json_docs_bytes)
    print(f"list_items_data: {list_items_data}")
    by_env_var_name: Dict[EnvVarName, OpListItemsEntry] = {}
    for entry in list_items_data:
        for env_var_name in entry['overview']['tags']:
            if 'env_var_name' in by_env_var_name:
                raise TooManyEntriesOPLookupError("Too many 1Password entries "
                                                  f"with tag {env_var_name} found")
            else:
                by_env_var_name[env_var_name] = entry

    return OpListItemsOpaqueOutput([
        by_env_var_name[env_var_name]
        for env_var_name in env_var_names
    ])

# TODO: prefix op cli commands with _op_cli?  unclear what is what


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


# TODO moved to op_get_item()
# def _op_get_item_fields(list_output: bytes, field_name: FieldName = 'password') -> bytes:


# TODO is this needed anymore?  Is all functionality still tested and there?
# def op_lookup(env_var_name: str, field_name: str = 'password') -> str:
#     # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
#     list_output_data = _op_list_items(env_var_name)
#     list_output = json.dumps(list_output_data).encode('utf-8')
#     get_output = _op_get_item_fields(list_output, field_name)
#     get_output_str = get_output.decode('utf-8').rstrip('\n')
#     if get_output_str == '':
#         raise NoFieldValueOPLookupError('1Passsword entry with tag '
#                                         f'{env_var_name} has no value for field {field_name}')
#     return get_output_str


def last_underscored_component_lowercased(env_var_name: EnvVarName) -> FieldName:
    components = env_var_name.split('_')
    return FieldName(components[-1].lower())


def last_double_underscored_component_lowercased(env_var_name: EnvVarName) -> FieldName:
    components = env_var_name.split('__')
    return FieldName(components[-1].lower())


def all_lowercased(env_var_name: EnvVarName) -> FieldName:
    return FieldName(env_var_name.lower())


T = TypeVar('T')


def uniqify(fields: Sequence[T]) -> List[T]:
    "Removes duplicates but preserves order"
    # https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
    return list(OrderedDict.fromkeys(fields))


def aliases(fields: List[FieldName]) -> List[FieldName]:
    if 'user' in fields:
        return [FieldName('username')]
    else:
        return []


def _op_consolidated_fields(env_var_names: Collection[EnvVarName]) -> Set[FieldName]:
    # TODO: write tests until this is fully written out
    return set(_op_fields_to_try(next(iter(env_var_names))))


def _op_fields_to_try(env_var_name: EnvVarName) -> List[FieldName]:
    candidates: List[FieldName] = uniqify([
        all_lowercased(env_var_name),
        last_double_underscored_component_lowercased(env_var_name),
        last_underscored_component_lowercased(env_var_name),
    ])
    return candidates + aliases(candidates) + [FieldName('password')]


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
