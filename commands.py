import shlex


class CommandRunner:
    def run_command(self, line):
        command, *args = shlex.split(line)
        func = getattr(self, 'cmd_' + command)
        if func is None:
            print('Command', command, 'not found')

        kwargs = {}
        for name, strval in zip(func.__code__.co_varnames[1:], args):
            valtype = func.__annotations__.get(name, str)
            if valtype is bytes:
                val = strval.encode()
            else:
                val = valtype(strval)
            kwargs[name] = val
        return func(**kwargs)
