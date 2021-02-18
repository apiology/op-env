import json
import subprocess
from collections import OrderedDict
from typing import Any, List


class OPLookupError(LookupError):
    pass


class TooManyEntriesOPLookupError(OPLookupError):
    pass


class NoEntriesOPLookupError(OPLookupError):
    pass


class NoFieldValueOPLookupError(OPLookupError):
    pass


def op_smart_lookup(env_var_name: str) -> str:
    fields = _op_fields_to_try(env_var_name)
    for field in fields:
        try:
            return op_lookup(env_var_name, field_name=field)
        except NoFieldValueOPLookupError:
            pass
    raise NoFieldValueOPLookupError('1Passsword entry with tag '
                                    f'{env_var_name} has no value for '
                                    'the fields tried: '
                                    f'{", ".join(fields)}.  Please populate '
                                    'one of these fields in 1Password.')


def _op_list_items(env_var_name: str) -> List[Any]:
    list_command = ['op', 'list', 'items', '--tags', env_var_name]
    list_output = subprocess.check_output(list_command)
    list_output_data = json.loads(list_output)
    assert isinstance(list_output_data, list)
    if len(list_output_data) == 0:
        raise NoEntriesOPLookupError(f"No 1Password entries with tag {env_var_name} found")
    if len(list_output_data) > 1:
        raise TooManyEntriesOPLookupError("Too many 1Password entries "
                                          f"with tag {env_var_name} found")
    return list_output_data


def _op_get_item_fields(list_output: bytes, field_name: str = 'password') -> bytes:
    get_command = ['op', 'get', 'item', '-', '--fields', field_name]
    return subprocess.check_output(get_command, input=list_output)


def op_lookup(env_var_name: str, field_name: str = 'password') -> str:
    # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    list_output_data = _op_list_items(env_var_name)
    list_output = json.dumps(list_output_data).encode('utf-8')
    get_output = _op_get_item_fields(list_output, field_name)
    get_output_str = get_output.decode('utf-8').rstrip('\n')
    if get_output_str == '':
        raise NoFieldValueOPLookupError('1Passsword entry with tag '
                                        f'{env_var_name} has no value for field {field_name}')
    return get_output_str


def last_underscored_component_lowercased(env_var_name: str) -> str:
    components = env_var_name.split('_')
    return components[-1].lower()


def last_double_underscored_component_lowercased(env_var_name: str) -> str:
    components = env_var_name.split('__')
    return components[-1].lower()


def all_lowercased(env_var_name: str) -> str:
    return env_var_name.lower()


def uniqify(fields: List[str]) -> List[str]:
    "Removes duplicates but preserves order"
    # https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
    return list(OrderedDict.fromkeys(fields))


def aliases(fields: List[str]) -> List[str]:
    if 'user' in fields:
        return ['username']
    else:
        return []


def _op_fields_to_try(env_var_name: str) -> List[str]:
    candidates = uniqify([
        all_lowercased(env_var_name),
        last_double_underscored_component_lowercased(env_var_name),
        last_underscored_component_lowercased(env_var_name),
    ])
    return candidates + aliases(candidates) + ['password']
