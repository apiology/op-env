import subprocess
import json
from typing import List, Any


class OPLookupError(LookupError):
    pass


class TooManyEntriesOPLookupError(OPLookupError):
    pass


class NoEntriesOPLookupError(OPLookupError):
    pass


class NoFieldValueOPLookupError(OPLookupError):
    pass


def op_smart_lookup(env_var_name: str) -> str:
    fields = op_fields_to_try(env_var_name)
    final_error = None
    for field in fields:
        try:
            return op_lookup(env_var_name, field_name=field)
        except NoFieldValueOPLookupError as e:
            final_error = e
    assert final_error is not None
    raise final_error


def op_list_items(env_var_name: str) -> List[Any]:
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


def op_get_item_fields(list_output: bytes, field_name: str = 'password') -> bytes:
    get_command = ['op', 'get', 'item', '-', '--fields', field_name]
    return subprocess.check_output(get_command, input=list_output)


def op_lookup(env_var_name: str, field_name: str = 'password') -> str:
    # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    list_output_data = op_list_items(env_var_name)
    list_output = json.dumps(list_output_data).encode('utf-8')
    get_output = op_get_item_fields(list_output, field_name)
    get_output_str = get_output.decode('utf-8').rstrip('\n')
    if get_output_str == '':
        raise NoFieldValueOPLookupError('1Passsword entry with tag '
                                        f'{env_var_name} has no value for field {field_name}')
    return get_output_str


def name_inferred_fields(env_var_name: str) -> List[str]:
    components = env_var_name.split('_')
    if len(components) <= 1:
        return []
    conversions = {
        'user': 'username'
    }
    raw_value = components[-1].lower()
    return [conversions.get(raw_value, raw_value)]


def op_fields_to_try(env_var_name: str) -> List[str]:
    return name_inferred_fields(env_var_name) + ['password']
