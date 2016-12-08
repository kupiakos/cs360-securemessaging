import shlex
from itertools import zip_longest


class CommandRunner:
    def run_command(self, line):
        command, *args = shlex.split(line)
        func = getattr(self, 'cmd_' + command)

        kwargs = {
            name: func.__annotations__.get(name, str)(strval)
            for name, strval in zip_longest(func.__code__.co_varnames[1:], args)
            }
        return func(**kwargs)
