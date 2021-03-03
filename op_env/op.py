# import json # TODO
from collections import OrderedDict
import subprocess
from typing import Any, Collection, Dict, List, NewType, Sequence, Set, TypeVar

OpListItemsOpaqueOutput = NewType('OpListItemsOpaqueOutput', List[Any])

EnvVarName = NewType('EnvVarName', str)

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
    raise NotImplementedError
    # list_command = ['op', 'list', 'items', '--tags', env_var_name]
    # list_output = subprocess.check_output(list_command)
    # list_output_data = json.loads(list_output)
    # assert isinstance(list_output_data, list)
    # if len(list_output_data) == 0:
    #     raise NoEntriesOPLookupError(f"No 1Password entries with tag {env_var_name} found")
    # if len(list_output_data) > 1:
    #     raise TooManyEntriesOPLookupError("Too many 1Password entries "
    #                                       f"with tag {env_var_name} found")
    # return OpListItemsOpaqueOutput(list_output_data)
# TODO: prefix op cli commands with _op_cli?  unclear what is what


def _op_get_item(list_items_output: OpListItemsOpaqueOutput,
                 env_var_names: Collection[EnvVarName],
                 all_fields_to_seek: Collection[FieldName]) ->\
                 Dict[EnvVarName, Dict[FieldName, FieldValue]]:
    raise NotImplementedError


# TODO is this needed anymore?  Is all functionality still tested and there?
# def _op_get_item_fields(list_output: bytes, field_name: FieldName = 'password') -> bytes:
#    get_command = ['op', 'get', 'item', '-', '--fields', field_name]
#    return subprocess.check_output(get_command, input=list_output)


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


def _op_consolidated_fields(env_var_name: Collection[EnvVarName]) -> Set[FieldName]:
    raise NotImplementedError


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
