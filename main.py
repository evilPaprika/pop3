import socket
import ssl
import re
import base64
import email
from email.parser import BytesParser, Parser
from email.policy import default
from email.parser import HeaderParser


class POP3:
    def __init__(self, addr):
        self.server_addr = addr
        self.connect_to_server()
        self.try_to_login()
        self.main_loop()

    def connect_to_server(self):
        try:
            self.sock = socket.socket()
            self.sock = ssl.wrap_socket(self.sock)
            self.sock.settimeout(0.5)
            self.sock.connect(self.server_addr)
            self.sock.recv(1024).decode()
        except:
            print("can't connect to the server")
            exit(1)
        print("connected to the server")

    def try_to_login(self):
        login = input('login: ')
        password = input('password: ')
        try:
            self.sendrecv('USER ' + login)
            self.num_of_messages = int(self.sendrecv('PASS ' + password).split()[1])
            print('you have', self.num_of_messages, 'messages')
        except:
            print('bad login/password. try again')
            self.connect_to_server()
            self.try_to_login()

    def main_loop(self):
        # print(sendrecv('USER mo8y.dick@yandex.ru', sock))
        # print(sendrecv('PASS password123', sock))
        try:
            self.print_messages_info(1, 5)
        except:
            print("something went wrong")
            pass
        while True:
            command = input('> ').lower()
            try:
                if command == 'exit':
                    break
                elif re.match("info \d+", command):
                    self.print_messages_info(int(re.search("\d+", command).group()))
                elif re.match("range \d+ \d+", command):
                    rng = re.findall("\d+", command)
                    self.print_messages_info(int(rng[0]), int(rng[1]))
                elif re.match("read \d+", command):
                    self.print_message(int(re.search("\d+", command).group()))
                elif re.match("read_top \d+ \d+", command):
                    break
                else:
                    raise ValueError
            except:
                print('something went wrong, try again')
                print("for help type 'h' or 'help'")
        self.sendrecv('QUIT')

    def print_messages_info(self, first, count = 1):
        if first > self.num_of_messages:
            raise ValueError
        last = min(first + count, self.num_of_messages + 1)
        for i in range(first, last):
            print("№", i)
            message = self.sendrecv('RETR ' + str(i))
            message = "\n".join(message.split("\n")[1:])
            self.parse_message(message)
            self.print_message_info()

    def print_message_info(self):
        # print(re.search('^To:[.\n]*[< ](.*?@.*?)[> ]?$, message, re.MULTILINE).group())
        # print(re.search('^From:[.\n]*[< ](.*?@.*?)[> ]?$', message, re.MULTILINE).group())
        # print('Subject: ' + get_subject(message))
        print('From: ' + self.parsed_message.get('from', "empty"))
        print('To: ' + self.parsed_message.get('to', "empty"))
        print('Subject: ' + self.parsed_message.get('subject', "empty"))

    def print_message(self, num):
        message = self.sendrecv('RETR ' + str(num))
        message = "\n".join(message.split("\n")[1:])
        self.parse_message(message)
        self.print_message_info()
        print('Message: ' + str(self.parsed_message.get_payload()))

    def parse_message(self, message):
        self.parsed_message = Parser(policy=default).parsestr(message)

    def sendrecv(self, command):
        self.sock.send((command + '\n').encode())
        result = b''
        while True:
            try:
                data = self.sock.recv(1024)
                result += data
                if data == b"":
                    break
            except Exception:
                break
        result = result.decode()
        if result != '' and result.split()[0] != "+OK":
            raise ValueError
        return result


def get_subject(message):
    result = re.findall('(Subject: |\s)=\?utf-8\?B\?(.*?)\?=', message, re.IGNORECASE)
    if not result:
        return re.findall('Subject: (.*?)\n', message)[0]
    for line in range(len(result)):
        result[line] = base64.b64decode(result[line][1]).decode()
    return ''.join(result)


if __name__ == '__main__':
    client = POP3(('pop.yandex.ru', 995))