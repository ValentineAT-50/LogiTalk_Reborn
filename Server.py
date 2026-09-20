"""
Одне повідомлення - один рядок, частини розділені символом "@".

    Клієнт -> сервер:
        NAME@нік задати або змінити нік
        TEXT@текст надіслати повідомлення

    Сервер -> клієнту:
        TEXT@нік@текст чиєсь повідомлення
        INFO@текст службове повідомлення

"""

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread, Lock

HOST = 'localhost'
PORT = 8080

ENC = 'utf-8'
BUFF = 4096
SEPAR = '@'
END = '\n'

DEF_NAME = 'Тест'
NAME_LEN = 20


class ChatServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.clients = {}       # Сокет / нік 
        self.lock = Lock()      # Захист словника від запису, бо потоків багато

        # Типи повідомлень які сервер читає
        self.handlers = {
            'TEXT': self.on_text,
            'NAME': self.on_name,
        }

    def start(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Сервер запущено на {self.host}:{self.port}")

        while True:
            client_socket, address = server_socket.accept()
            print(f"Підключився клієнт: {address}")
            with self.lock:
                self.clients[client_socket] = None
            Thread(target=self.listen_client,
                   args=(client_socket, address), daemon=True).start()

    def listen_client(self, client_socket, address):
        # Окремий поток для кожного клієнта
        buffer = ''
        while True:
            try:
                chunk = client_socket.recv(BUFF)
            except OSError:
                break
            if not chunk:
                break

            # Зберігаємо все в buffer і ріжемо по \n
            buffer += chunk.decode(ENC, errors='ignore')
            while END in buffer:
                line, buffer = buffer.split(END, 1)
                self.handle_line(client_socket, line.strip())

        self.disconnect(client_socket, address)

    def disconnect(self, client_socket, address):
        with self.lock:
            name = self.clients.pop(client_socket, None)
        try:
            client_socket.close()
        except OSError:
            pass
        print(f"Відключився клієнт: {address}")
        if name:
            self.broadcast(f"INFO{SEPAR}{name} вийшов(ла) з чату")


    def handle_line(self, client_socket, line):
        if not line:
            return
        # maxsplit=1: сам текст може містити "@" і його не поріже
        parts = line.split(SEPAR, 1)
        message_type = parts[0]
        payload = parts[1] if len(parts) > 1 else ''

        handler = self.handlers.get(message_type)
        if handler is None:
            print(f"Невідомий тип повідомлення: {message_type}")
            return
        handler(client_socket, payload)

    def on_text(self, client_socket, payload):
        text = payload.strip()
        if not text:
            return
        # Нік береться зі словника, щоб не можна було імітувати іншого
        name = self.name_of(client_socket)
        print(f"{name}: {text}")
        self.broadcast(f"TEXT{SEPAR}{name}{SEPAR}{text}")

    def on_name(self, client_socket, payload):
        new_name = payload.replace(SEPAR, '').strip()[:NAME_LEN]
        if not new_name:
            new_name = DEF_NAME

        with self.lock:
            old_name = self.clients.get(client_socket)
            self.clients[client_socket] = new_name

        if old_name is None:
            self.broadcast(f"INFO{SEPAR}{new_name} приєднався(лась) до чату")
        elif old_name != new_name:
            self.broadcast(f"INFO{SEPAR}{old_name} тепер {new_name}")


    def name_of(self, client_socket):
        with self.lock:
            return self.clients.get(client_socket) or DEF_NAME

    def send_to(self, client_socket, line):
        try:
            client_socket.sendall((line + END).encode(ENC))
        except OSError:
            pass

    def broadcast(self, line, exclude=None):
        with self.lock:
            receivers = list(self.clients)
        for client_socket in receivers:
            if client_socket is not exclude:
                self.send_to(client_socket, line)


if __name__ == '__main__':
    ChatServer().start()