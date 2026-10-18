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

import os
from tkinter import Canvas
from PIL import Image, ImageTk, ImageEnhance
from customtkinter import (CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkScrollableFrame, CTkFont, set_appearance_mode,CTkScrollbar)

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
PAD = 10
SIDE = 14
INNER = 10
RADIUS = 12

BG_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images.jpg')
BG_DIM = 0.55
COLOR_BG = '#1e1e1e'


COLOR_OWN = '#2f6fdb'
COLOR_OTHER = '#3a3f46'
COLOR_INFO = '#2b2b2b'


class ChatClient(CTk):
    def __init__(self):
        super().__init__()
        set_appearance_mode('dark')
        self.title('Chat Client')
        self.geometry('700x500')
        self.minsize(500, 350)

        self.username = USERNAME
        self.sock = None
        self.inbox = Queue()        # Черга яка відправляє все повідомлення
        self.messages = []  # усі повідомлення, щоб перемалювати при зміні розміру
        self.next_y = PAD  # де малювати наступне повідомлення
        self.bg_photo = None
        self.bg_source = self.load_background()

        # Повідомлення які клієнт може прийняти
        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info,
        }

        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.process_inbox()        # перевірка черги
        self.after(100, self.connect)


    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.is_menu_open = False
        self.menu_frame = CTkFrame(self, width=CLOSEDW, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, sticky='ns')
        self.menu_frame.pack_propagate(False)

        self.menu_button = CTkButton(self.menu_frame, text='▶', width=32,
                                     command=self.toggle_menu)
        self.menu_button.pack(anchor='w', padx=8, pady=10)

        self.menu_content = CTkFrame(self.menu_frame, fg_color='transparent')
        CTkLabel(self.menu_content, text='Ваш нік', anchor='w').pack(fill='x')
        self.name_entry = CTkEntry(self.menu_content, placeholder_text='Нік...')
        self.name_entry.pack(fill='x', pady=5)
        self.name_entry.insert(0, self.username)
        CTkButton(self.menu_content, text='Зберегти',
                  command=self.save_name).pack(fill='x')

        right_frame = CTkFrame(self, fg_color='transparent')
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        self.chat_canvas = Canvas(right_frame, highlightthickness=0, bd=0,
                                  bg=COLOR_BG, yscrollincrement=20)
        self.chat_canvas.grid(row=0, column=0, sticky='nsew')
        self.bg_item = self.chat_canvas.create_image(0, 0, anchor='nw', tags='bg')

        self.scrollbar = CTkScrollbar(right_frame, command=self.chat_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.chat_canvas.configure(yscrollcommand=self.on_scroll)

        self.chat_canvas.bind('<Configure>', self.on_chat_resize)
        self.bind_all('<MouseWheel>', self.on_mousewheel)

        bottom_frame = CTkFrame(right_frame, fg_color='transparent')
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = CTkEntry(bottom_frame, height=40,
                                      placeholder_text='Введіть повідомлення:')
        self.message_entry.grid(row=0, column=0, sticky='ew', padx=(10, 6), pady=10)
        self.message_entry.bind('<Return>', lambda event: self.send_message())

        self.send_button = CTkButton(bottom_frame, text='>', width=50, height=40,
                                     command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=10)

    def toggle_menu(self):
        self.is_menu_open = not self.is_menu_open
        self.menu_button.configure(text='◀' if self.is_menu_open else '▶')
        if not self.is_menu_open:
            self.menu_content.pack_forget()
        self.animate_menu()

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


    def load_background(self):
        try:
            img = Image.open(BG_IMAGE).convert('RGB')
        except OSError:
            return None                       # немає файлу, буде суцільний колір
        img.thumbnail((1920, 1080))           # щоб ресайз не гальмував
        return ImageEnhance.Brightness(img).enhance(BG_DIM)

    def update_background(self, width, height):
        if not self.bg_source or width < 2 or height < 2:
            return
        # "cover": заповнюємо всю область і обрізаємо зайве по центру
        sw, sh = self.bg_source.size
        scale = max(width / sw, height / sh)
        resized = self.bg_source.resize((int(sw * scale) + 1, int(sh * scale) + 1),
                                        Image.BILINEAR)
        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        cropped = resized.crop((left, top, left + width, top + height))
        self.bg_photo = ImageTk.PhotoImage(cropped)   # треба тримати посилання!
        self.chat_canvas.itemconfigure(self.bg_item, image=self.bg_photo)

    def place_background(self):
        # фон не прокручується: тримаємо його у верхньому лівому куті видимої області
        self.chat_canvas.coords(self.bg_item, 0, self.chat_canvas.canvasy(0))
        self.chat_canvas.tag_lower('bg')

    # ---------- прокрутка ----------
    def on_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self.place_background()

    def on_mousewheel(self, event):
        self.chat_canvas.yview_scroll(-3 if event.delta > 0 else 3, 'units')

    def scroll_down(self):
        self.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ---------- повідомлення ----------
    def add_message(self, text, author=None, is_own=False, is_info=False):
        message = {'text': text, 'author': author, 'own': is_own, 'info': is_info}
        self.messages.append(message)
        self.render(message)
        self.after(20, self.scroll_down)

    def render(self, message):
        canvas = self.chat_canvas
        width = canvas.winfo_width()
        self.next_y = self.draw_message(message, width, self.next_y)
        canvas.configure(scrollregion=(0, 0, width, max(self.next_y, canvas.winfo_height())))

    def redraw(self):
        self.chat_canvas.delete('msg')
        self.next_y = PAD
        for message in self.messages:
            self.render(message)

    def on_chat_resize(self, event):
        self.update_background(event.width, event.height)
        self.redraw()
        self.place_background()

    def draw_message(self, message, width, y):
        canvas = self.chat_canvas
        max_text_w = max(int(width * 0.7), 160)

        if message['info']:
            color, text_color = COLOR_INFO, '#9aa0a6'
        elif message['own']:
            color, text_color = COLOR_OWN, 'white'
        else:
            color, text_color = COLOR_OTHER, 'white'

        author_id = None
        if message['author']:
            author_id = canvas.create_text(0, 0, text=message['author'], anchor='nw',
                                           fill='#e0e0e0', font=('Segoe UI', 9, 'bold'),
                                           tags='msg')
        text_id = canvas.create_text(0, 0, text=message['text'], anchor='nw',
                                     width=max_text_w, fill=text_color,
                                     justify='center' if message['info'] else 'left',
                                     font=('Segoe UI', 11), tags='msg')

        # міряємо розміри тексту, поки він у (0, 0)
        tx1, ty1, tx2, ty2 = canvas.bbox(text_id)
        text_w, text_h = tx2 - tx1, ty2 - ty1
        author_w = author_h = 0
        if author_id:
            ax1, ay1, ax2, ay2 = canvas.bbox(author_id)
            author_w, author_h = ax2 - ax1, ay2 - ay1

        box_w = max(text_w, author_w) + 2 * INNER
        box_h = author_h + text_h + 2 * 6

        if message['info']:
            left = (width - box_w) // 2
        elif message['own']:
            left = width - SIDE - box_w
        else:
            left = SIDE

        rect = self.rounded_rect(left, y, left + box_w, y + box_h, RADIUS,
                                 fill=color, outline='', tags='msg')
        inner_y = y + 6
        if author_id:
            canvas.coords(author_id, left + INNER, inner_y)
            inner_y += author_h
        canvas.coords(text_id, left + INNER, inner_y)
        canvas.tag_lower(rect, author_id or text_id)   # бульбашка під текстом, але над фоном

        return y + box_h + PAD

    def rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
                  x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
                  x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.chat_canvas.create_polygon(points, smooth=True, **kwargs)


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