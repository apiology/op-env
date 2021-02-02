import subprocess


def op_lookup(env_var_name: str, field_name: str = 'password') -> str:
    # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    list_command = ['op', 'list', 'items', '--tags', env_var_name]
    pipe = subprocess.Popen(list_command,
                            stdout=subprocess.PIPE)
    get_command = ['op', 'get', 'item', '-', '--fields', field_name]
    output = subprocess.check_output(get_command, stdin=pipe.stdout)
    pipe.wait()
    return output.decode('utf-8').rstrip('\n')
