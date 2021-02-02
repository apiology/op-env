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


def op_lookup(env_var_name: str, field_name: str = 'password') -> str:
    # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    list_command = ['op', 'list', 'items', '--tags', env_var_name]
    pipe = subprocess.Popen(list_command,
                            stdout=subprocess.PIPE)
    get_command = ['op', 'get', 'item', '-', '--fields', field_name]
    output = subprocess.check_output(get_command, stdin=pipe.stdout)
    pipe.wait()
    return output.decode('utf-8').rstrip('\n')


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
