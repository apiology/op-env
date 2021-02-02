import subprocess
from typing import List


def op_smart_lookup(env_var_name: str) -> str:
    fields = op_fields_to_try(env_var_name)
    final_error = None
    for field in fields:
        try:
            return op_lookup(env_var_name, field_name=field)
        except subprocess.CalledProcessError as e:
            final_error = e
    assert final_error is not None
    raise final_error


def op_list_items(env_var_name: str) -> bytes:
    list_command = ['op', 'list', 'items', '--tags', env_var_name]
    list_output = subprocess.check_output(list_command)
    return list_output


def op_get_item_fields(list_output: bytes, field_name: str = 'password') -> bytes:
    get_command = ['op', 'get', 'item', '-', '--fields', field_name]
    return subprocess.check_output(get_command, input=list_output)


def op_lookup(env_var_name: str, field_name: str = 'password') -> str:
    # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    list_output = op_list_items(env_var_name)
    get_output = op_get_item_fields(list_output, field_name)
    return get_output.decode('utf-8').rstrip('\n')


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
