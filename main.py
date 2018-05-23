import socket
import ssl
import re
import base64
from email.parser import Parser
from email.policy import default


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
            self.sock.settimeout(1)
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
        # print(self.sendrecv('USER mo8y.dick@yandex.ru'))
        # self.num_of_messages = int(self.sendrecv('PASS password123').split()[1])
        try:
            pass
            self.print_messages_info(1, 5)
        except:
            print("something went wrong")
            pass
        while True:
            command = input('> ').lower()
            try:
                if command == 'exit':
                    break
                elif command == "help" or command == "h":
                    print("""exit - выход из программы
info [NUM] - посмотреть информацию о сообщении
list [START] [FINISH] - посмотреть информацию о диапазоне сообщений
read [NUM] - прочитать сообщение
read_top [NUM] [LINES] - прочитать первые несколько строк сообщения
get_attach [NUM] - скачать прикрепленный файл
                    """)
                elif re.match("info \d+", command):
                    self.print_messages_info(int(re.search("\d+", command).group()))
                elif re.match("list \d+ \d+", command):
                    rng = re.findall("\d+", command)
                    self.print_messages_info(int(rng[0]), int(rng[1]))
                elif re.match("read \d+", command):
                    self.print_message(int(re.search("\d+", command).group()))
                elif re.match("read_top \d+ \d+", command):
                    rng = re.findall("\d+", command)
                    self.print_message(int(rng[0]), int(rng[1]))
                elif re.match("get_attach \d+", command):
                    self.download_attachment(int(re.search("\d+", command).group()))
                else:
                    raise ValueError
            except Exception as e:
                print('something went wrong, try again')
                print("for help type 'h' or 'help'")
                print(e)
        self.sendrecv('QUIT')

    def print_messages_info(self, first, count = 1):
        if first > self.num_of_messages:
            raise ValueError
        last = min(first + count, self.num_of_messages + 1)
        for i in range(first, last):
            print("\n№", i)
            self.get_and_parse(i)
            self.print_message_info()

    def print_message_info(self):
        print('From: ' + self.parsed_message.get('from', "empty"))
        print('To: ' + self.parsed_message.get('to', "empty"))
        print('Subject: ' + self.parsed_message.get('subject', "empty"))
        for part in self.parsed_message.walk():
            if str(part).startswith('Content-Disposition: attachment'):
                filename = re.findall('filename="(.*?)"', str(part))[0]
                print("Has attachment: " + filename)

    def get_and_parse(self, n):
        message = self.sendrecv('RETR ' + str(n))
        message = "\n".join(message.split("\n")[1:])
        self.parse_message(message)

    def print_message(self, num, top = None):
        self.get_and_parse(num)
        self.print_message_info()
        body = self.get_body()
        if top:
            spt = body.split('\n')
            print('\n'.join(spt[0:min(len(spt), top)]))
        else:
            print(body)

    def download_attachment(self, num):
        self.get_and_parse(num)
        for part in self.parsed_message.walk():
            if str(part).startswith('Content-Disposition: attachment'):
                filename = re.findall('filename="(.*?)"', str(part))[0]
                f = open(filename, 'wb+')
                for line in part.get_payload().split("\r\n"):
                    f.write(base64.b64decode(line))
                f.close()
                print("saved as " + filename)
                break
        else:
            print("no attachments")

    def get_body(self):
        body = 'empty'
        for part in self.parsed_message.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload()
                break
        else:
            for part in self.parsed_message.walk():
                if part.get_content_type() == 'text/html':
                    body = part.get_payload()
                    break
        return body

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

if __name__ == '__main__':
    client = POP3(('pop.yandex.ru', 995))