#!/usr/bin/env python3

import argparse
import base64
import socket
import sys
import traceback

from Crypto import Random
from Crypto.PublicKey import RSA

from commands import CommandRunner

debug = False


class Client(CommandRunner):
    connection = None
    conn_file = None
    key = None

    def run(self, port=8081):

        self.connection = socket.create_connection(('localhost', port))
        self.conn_file = self.connection.makefile()
        while True:
            line = ''
            try:
                line = input('% ')
            except EOFError or KeyboardInterrupt:
                self.cmd_quit()
            if not line.strip():
                continue
            try:
                self.run_command(line)
            except Exception:
                if debug:
                    traceback.print_exc()
                print('Error with command')

    def _get_key(self, user: str):
        self.connection.sendall(b'get_key %s\n' % user.encode())
        response = self.conn_file.readline()
        if not response.startswith('key'):
            return None
        length = int(response.split()[1])
        key = self.conn_file.read(length)
        return key

    def cmd_send(self, user: str, subject: str):
        key_text = self._get_key(user)
        if key_text is None:
            print('The user', user, 'does not exist.')
            return
        public_key = RSA.importKey(key_text)
        print('- Type your message. End with a blank line -')
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        message_pack = user.encode() + '\n'.join(lines).encode()
        encrypted = public_key.encrypt(message_pack, 0)[0]
        encrypted = base64.b64encode(encrypted)
        self.connection.send(b'put %s %s %d\n%s' % (
            user.encode(), subject.encode(), len(encrypted), encrypted
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

    def _read(self, user: str, index: int):
        self.connection.send(b'get %s %d\n' % (user.encode(), index))
        response = self.conn_file.readline()
        if not response.startswith('message'):
            print('server error:', response)
            return None, None
        _, subject, length = response.strip().split()
        length = int(length)
        message = self.conn_file.read(length)
        return subject, message

    def cmd_read(self, user: str, index: int):
        if self.key is None:
            print('You have not logged in')
            return
        subject, encrypted = self._read(user, index)
        if subject is None:
            return None
        encrypted = base64.b64decode(encrypted)
        user_bytes = user.encode()
        message_pack = self.key.decrypt(encrypted)
        if message_pack[:len(user_bytes)] != user_bytes:
            print('You cannot read this file.')
            return None
        message = message_pack[len(user_bytes):].decode()
        print(subject)
        print(message)

    def cmd_peek(self, user: str, index: int):
        subject, message = self._read(user, index)
        print(subject)
        print(message)

    def cmd_login(self, user: str):
        random_generator = Random.new().read
        self.key = RSA.generate(2048, random_generator)
        public_key = self.key.publickey()
        export = public_key.exportKey()
        self.connection.sendall(b'store_key %s %d\n%s' % (
            user.encode(), len(export), export
        ))
        response = self.conn_file.readline()
        if not response.startswith('OK'):
            print(response)

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
    global debug
    debug = args.debug
    Client().run(args.port)


if __name__ == '__main__':
    main()
