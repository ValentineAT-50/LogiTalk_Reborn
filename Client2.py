"""
Одне повідомлення - один рядок, частини розділені символом "@".

    Клієнт -> сервер:
        NAME@нік задати або змінити нік
        TEXT@текст надіслати повідомлення

    Сервер -> клієнту:
        TEXT@нік@текст чиєсь повідомлення
        INFO@текст службове повідомлення

"""


from queue import Queue, Empty
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from tkinter import filedialog

from datetime import datetime
from PIL import Image, ImageTk
from customtkinter import (CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkScrollableFrame, CTkFont, set_appearance_mode)


HOST = 'localhost'
PORT = 8080

USERNAME = 'Test1'

ENC = 'utf-8'
BUFF = 4096
SEPAR = '@'
END = '\n'

OPENW = 200
CLOSEDW = 48
STEP = 16


imager1 = None

avatarka = None

avatar_image = None
avatar_path = None

COLOR_OWN = '#2f6fdb'
COLOR_OTHER = '#3a3f46'
COLOR_INFO = '#2b2b2b'


class ChatClient(CTk):
    def __init__(self):
        super().__init__()

        self.avatar_image = None
        self.avatar_path = None

        set_appearance_mode('dark')
        self.title('Chat Client')
        self.geometry('700x500')
        self.minsize(500, 350)

        self.username = USERNAME
        self.sock = None
        self.inbox = Queue()        # Черга яка відправляє все повідомлення
        self.message_labels = []    # Список щоб міняти перенос тексту при зміні розміру вікна
        self.wraplength = 400

        # Повідомлення, які клієнт може прийняти
        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info,
            'TYPING': self.on_typing,
        }
        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.process_inbox()        # перевірка черги
        self.after(100, self.connect)

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Бічне меню
        self.is_menu_open = False

        self.menu_frame = CTkFrame(
            self, width=CLOSEDW, corner_radius=0
        )
        self.menu_frame.grid(row=0, column=0, sticky="ns")
        self.menu_frame.pack_propagate(False)

        self.menu_button = CTkButton(
            self.menu_frame,
            text="▶",
            width=32,
            command=self.toggle_menu
        )
        self.menu_button.pack(anchor="w", padx=8, pady=10)

        self.menu_content = CTkFrame(
            self.menu_frame, fg_color="transparent"
        )

        CTkLabel(
            self.menu_content,
            text="Ваш нік",
            anchor="w"
        ).pack(fill="x")

        self.name_entry = CTkEntry(
            self.menu_content,
            placeholder_text="Нік..."
        )
        self.name_entry.pack(fill="x", pady=5)
        self.name_entry.insert(0, self.username)

        CTkButton(
            self.menu_content,
            text="Зберегти",
            command=self.save_name
        ).pack(fill="x")

        self.avatar_button = CTkButton(
            self.menu_content,
            text="Обрати аватарку",
            command=self.choose_avatar
        )
        self.avatar_button.pack(fill="x", pady=5)

        self.avatar_preview = CTkLabel(
            self.menu_content,
            text="Аватарка не вибрана"
        )
        self.avatar_preview.pack(pady=10)

        self.avatar = CTkLabel(self.menu_content, text="")
        self.avatar.pack(pady=5)

        # Права частина вікна — створюємо ПЕРЕД використанням
        right_frame = CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew")

        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=0)
        right_frame.grid_rowconfigure(2, weight=0)

        # Повідомлення чату
        self.chat_field = CTkScrollableFrame(
            right_frame,
            fg_color="transparent"
        )
        self.chat_field.grid(
            row=0, column=0,
            sticky="nsew",
            padx=10, pady=(10, 0)
        )
        self.chat_field.bind(
            "<Configure>", self.on_chat_resize, add="+"
        )

        # Індикатор набору тексту
        self.typing_label = CTkLabel(
            right_frame,
            text="",
            text_color="#9aa0a6"
        )
        self.typing_label.grid(
            row=1, column=0,
            sticky="w",
            padx=15
        )

        # Поле введення
        bottom_frame = CTkFrame(
            right_frame, fg_color="transparent"
        )
        bottom_frame.grid(row=2, column=0, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = CTkEntry(
            bottom_frame,
            height=40,
            placeholder_text="Введіть повідомлення:"
        )
        self.message_entry.grid(
            row=0, column=0,
            sticky="ew",
            padx=(10, 6), pady=10
        )
        self.message_entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        self.send_button = CTkButton(
            bottom_frame,
            text=">",
            width=50,
            height=40,
            command=self.send_message
        )
        self.send_button.grid(
            row=0, column=1,
            padx=(0, 10), pady=10
        )

    def on_typing(self, parts):
        if len(parts) < 3:
            return

        author, status = parts[1], parts[2]

        if status == '1':
            self.typing_users.add(author)
        else:
            self.typing_users.discard(author)

        if not self.typing_users:
            self.typing_label.configure(text='')
            return

        names = []

        for name in sorted(self.typing_users):
            if name == self.username:
                names.append('Ти')
            else:
                names.append(name)

        if len(names) == 1:
            text = f'{names[0]} друкує...'
        else:
            text = ', '.join(names) + ' друкують...'

        self.typing_label.configure(text=text)


    def toggle_menu(self):
        self.is_menu_open = not self.is_menu_open
        self.menu_button.configure(text='◀' if self.is_menu_open else '▶')
        if not self.is_menu_open:
            self.menu_content.pack_forget()
        self.animate_menu()

    def choose_avatar(self):
        path = filedialog.askopenfilename(
            title='Виберіть аватарку',
            filetypes=[
                ('Зображення', '*.png *.jpg *.jpeg *.webp'),
                ('PNG', '*.png'),
                ('JPEG', '*.jpg *.jpeg'),
                ('Усі файли', '*.*')
            ]
        )

        if not path:
            return

        try:
            image = Image.open(path).convert('RGB')
            image.thumbnail((80, 80))

            self.avatar_image = ImageTk.PhotoImage(image)
            self.avatar_path = path

            self.avatar_preview.configure(
                image=self.avatar_image,
                text=''
            )

        except Exception as error:
            self.add_message(
                f'Не вдалося відкрити аватарку: {error}',
                is_info=True
            )

    def animate_menu(self):
        target = OPENW if self.is_menu_open else CLOSEDW
        current = self.menu_frame.winfo_width()

        if abs(current - target) <= STEP:
            self.menu_frame.configure(width=target)
            if self.is_menu_open:
                self.menu_content.pack(fill='x', padx=10, pady=10)
            return

        step = STEP if target > current else -STEP
        self.menu_frame.configure(width=current + step)
        self.after(10, self.animate_menu)

    def imager(self):

        global imager
        imag = Image.open()

        pass

    def avatar(self):
        pass

    def add_message(self, text, author=None, is_own=False, is_info=False):
        if is_info:
            color = COLOR_INFO
        elif is_own:
            color = COLOR_OWN
        else:
            color = COLOR_OTHER

        message_frame = CTkFrame(self.chat_field, fg_color=color, corner_radius=10)
        message_frame.pack(anchor='e' if is_own else 'w', padx=5, pady=4)

        # Аватарка
        if author and getattr(self, 'avatar_image', None):
            avatar_label = CTkLabel(
                message_frame,
                image=self.avatar_image,
                text=''
            )
            avatar_label.pack(
                side='left',
                padx=(8, 4),
                pady=8
            )

        content_frame = CTkFrame(
            message_frame,
            fg_color='transparent'
        )
        content_frame.pack(
            side='left',
            fill='both',
            expand=True
        )

        time_text = datetime.now().strftime('%H:%M')

        CTkLabel(
            message_frame,
            text=time_text,
            font=CTkFont(size=9),
            text_color='#b0b0b0'
        ).pack(anchor='e', padx=10, pady=(2, 0))

        if author:
            CTkLabel(message_frame, text=author, anchor='w', text_color='#e0e0e0',
                     font=CTkFont(size=11, weight='bold')).pack(fill='x', padx=10, pady=(6, 0))

        label = CTkLabel(message_frame, text=text, justify='left', anchor='w',
                         wraplength=self.wraplength,
                         text_color='#9aa0a6' if is_info else 'white')
        label.pack(fill='x', padx=10, pady=(2, 6))

        self.message_labels.append(label)
        self.after(20, self.scroll_down)

    def on_chat_resize(self, event):
        self.wraplength = max(int(event.width * 0.7), 160)
        for label in self.message_labels:
            label.configure(wraplength=self.wraplength)

    def scroll_down(self):
        self.update_idletasks()
        self.chat_field._parent_canvas.yview_moveto(1.0)


    def connect(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except OSError as error:
            self.sock = None
            self.add_message(f"Не вдалося підключитися до сервера: {error}", is_info=True)
            return

        Thread(target=self.receive_loop, daemon=True).start()
        self.send_line('NAME', self.username)

    def send_image(self):
        filedialog.askopenfilename(
            title="Вибір Картинки Для Відправлення.",
            initialdir="/",
            filetypes=[('Зображення', '*.png *.jpg *.jpeg *.webp'),
                ('PNG', '*.png'),
                ('JPEG', '*.jpg *.jpeg'),
                ('Усі файли', '*.*')
            ]
        )




    def send_line(self, message_type, *parts):
        # Збирання рядка до купи ТИП@частина1@частина2
        if not self.sock:
            self.add_message('Немає зʼєднання із сервером', is_info=True)
            return
        line = SEPAR.join((message_type,) + parts) + END
        try:
            self.sock.sendall(line.encode(ENC))
        except OSError:
            self.sock = None
            self.add_message('Зʼєднання із сервером втрачено', is_info=True)

    def receive_loop(self):
        # Потік який передає текст в чергу, бо іноді не все встигає обробитись перед виводом
        buffer = ''
        while True:
            try:
                chunk = self.sock.recv(BUFF)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk.decode(ENC, errors='ignore')
            while END in buffer:
                line, buffer = buffer.split(END, 1)
                self.inbox.put(line.strip())
        self.inbox.put(f"INFO{SEPAR}Зʼєднання із сервером втрачено")

    def process_inbox(self):
        # Виводить все що накопилось у черзі
        while True:
            try:
                line = self.inbox.get_nowait()
            except Empty:
                break
            self.handle_line(line)
        self.after(50, self.process_inbox)


    def handle_line(self, line):
        if not line:
            return
        # maxsplit=2: сам текст може містити "@" бо розділ буде лише через пробіл + @
        parts = line.split(SEPAR, 2)
        handler = self.handlers.get(parts[0])
        if handler is None:
            self.add_message(f"Невідоме повідомлення: {line}", is_info=True)
            return
        handler(parts)

    def on_text(self, parts):
        if len(parts) < 3:
            return
        author, text = parts[1], parts[2]
        self.add_message(text, author=author, is_own=(author == self.username))

    def on_info(self, parts):
        if len(parts) < 2:
            return
        self.add_message(parts[1], is_info=True)


    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        self.message_entry.delete(0, 'end')
        # Своє повідомлення не виводить, сервер повертає його всім,
        self.send_line('TEXT', text)

        def send_message(self):
            text = self.message_entry.get().strip()
            if not text:
                return  # Якщо рядок порожній — нічого не робимо

            # Формуємо повідомлення за вашим протоколом: TEXT@текст\n
            message = f"TEXT{SEPAR}{text}{END}"

            try:
                if self.sock:
                    self.sock.sendall(message.encode(ENC))

                    # ВАРІАНТ А: Відображаємо повідомлення у себе ВІДРАЗУ після відправки
                    self.add_message(f"{self.username}: {text}", is_own=True)

                    self.message_entry.delete(0, 'end')  # Очищаємо поле введення
            except Exception as e:
                self.add_message(f"Помилка відправки: {e}", is_info=True)

    def save_name(self):
        new_name = self.name_entry.get().replace(SEPAR, '').strip()
        if not new_name or new_name == self.username:
            return
        self.username = new_name
        self.title(f"Chat Client — {new_name}")
        self.send_line('NAME', new_name)

    def on_close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.destroy()


if __name__ == '__main__':
    win = ChatClient()
    win.mainloop()