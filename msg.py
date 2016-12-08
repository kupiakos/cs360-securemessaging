import argparse
import socket
import sys

from commands import CommandRunner


class Client(CommandRunner):
    connection = None
    conn_file = None

    def run(self, port=8081):
        self.connection = socket.create_connection(('localhost', port))
        self.conn_file = self.connection.makefile()
        while True:
            line = ''
            try:
                line = input('% ')
            except KeyboardInterrupt:
                pass
            except EOFError:
                self.cmd_quit()
            if not line.strip():
                continue
            try:
                self.run_command(line)
            except Exception:
                # traceback.print_exc()
                print('Error with command')

    def cmd_send(self, user: str, subject: str):
        print('- Type your message. End with a blank line -')
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        message = '\n'.join(lines).encode()
        self.connection.send(b'put %s %s %d\n%s' % (
            user.encode(), subject.encode(), len(message), message
        ))
        response = self.conn_file.readline()
        if not response.startswith('OK'):
            print(response)

    def cmd_list(self, user: str):
        self.connection.send(b'list %s\n' % user.encode())
        response = self.conn_file.readline()
        if not response.startswith('list'):
            print(response)
            return
        num = int(response.split()[1])
        for _ in range(num):
            print(self.conn_file.readline(), end='')

    def cmd_read(self, user: str, index: int):
        self.connection.send(b'get %s %d\n' % (user.encode(), index))
        response = self.conn_file.readline()
        if not response.startswith('message'):
            print(response)
            return
        _, subject, length = response.strip().split()
        length = int(length)
        message = self.conn_file.read(length)
        print(subject)
        print(message)

    def cmd_quit(self):
        print()
        self.connection.close()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', metavar='port', default=8081, dest='port', type=int,
                        help='port number of the messaging server')
    parser.add_argument('-d', action='store_true', dest='debug', help='print debugging information')
    args = parser.parse_args()
    Client().run(args.port)


if __name__ == '__main__':
    main()
