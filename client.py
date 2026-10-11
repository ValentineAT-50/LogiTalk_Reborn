"""
Одне повідомлення - один рядок, частини розділені символом "@".

    Клієнт -> сервер:
        NAME@нік задати або змінити нік
        TEXT@текст надіслати повідомлення

    Сервер -> клієнту:
        TEXT@нік@текст чиєсь повідомлення
        INFO@текст службове повідомлення

"""

from datetime import datetime
from queue import Queue, Empty
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from customtkinter import (CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkScrollableFrame, CTkFont, set_appearance_mode,
                           set_default_color_theme)

HOST = 'localhost'
PORT = 8080

USERNAME = 'Test1'

ENC = 'utf-8'
BUFF = 4096
SEPAR = '@'
END = '\n'

OPENW = 220
CLOSEDW = 56
STEP = 18

BG_MAIN = '#1a1d23'
BG_PANEL = '#15171c'
BG_HEADER = '#20242b'
BG_INPUT = '#262a32'

BUBBLE_OWN = '#4f7cff'
BUBBLE_OTHER = '#2b2f38'
BUBBLE_INFO = '#20242b'

TXT_MAIN = '#eef0f3'
TXT_MUTED = '#8b909b'
TXT_INFO = '#6f7480'

ACCENT = '#4f7cff'
ONLINE = '#3ddc84'
OFFLINE = '#e5534b'

AVATAR_COLORS = ['#4f7cff', '#e5534b', '#3ddc84', '#f2b705',
                 '#9b5de5', '#00bbf9', '#f15bb5', '#ff7b54']


def avatar_color(name):
    return AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)]


class ChatClient(CTk):
    def __init__(self):
        super().__init__()
        set_appearance_mode('dark')
        try:
            set_default_color_theme('blue')
        except Exception:
            pass

        self.title('клон діскорда')
        self.geometry('760x560')
        self.minsize(520, 380)
        self.configure(fg_color=BG_MAIN)

        self.username = USERNAME
        self.sock = None
        self.connected = False
        self.inbox = Queue()
        self.message_labels = []
        self.wraplength = 420

        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info,
        }

        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.process_inbox()
        self.after(150, self.connect)

    # ---------- UI ----------

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.is_menu_open = False
        self.menu_frame = CTkFrame(self, width=CLOSEDW, corner_radius=0, fg_color=BG_PANEL)
        self.menu_frame.grid(row=0, column=0, sticky='ns')
        self.menu_frame.pack_propagate(False)

        self.menu_button = CTkButton(
            self.menu_frame, text='☰', width=36, height=36, corner_radius=8,
            fg_color='transparent', hover_color=BG_HEADER, text_color=TXT_MAIN,
            command=self.toggle_menu)
        self.menu_button.pack(anchor='w', padx=10, pady=14)

        self.menu_content = CTkFrame(self.menu_frame, fg_color='transparent')
        CTkLabel(self.menu_content, text='ПРОФІЛЬ', anchor='w', text_color=TXT_MUTED,
                 font=CTkFont(size=11, weight='bold')).pack(fill='x', pady=(0, 8))

        self.avatar_preview = CTkLabel(
            self.menu_content, text=self.username[:1].upper(), width=56, height=56,
            corner_radius=28, fg_color=avatar_color(self.username), text_color='white',
            font=CTkFont(size=20, weight='bold'))
        self.avatar_preview.pack(pady=(0, 12))

        self.name_entry = CTkEntry(self.menu_content, placeholder_text='Ваш нік',
                                    fg_color=BG_INPUT, border_width=0, corner_radius=8)
        self.name_entry.pack(fill='x', pady=(0, 8))
        self.name_entry.insert(0, self.username)

        CTkButton(self.menu_content, text='Зберегти', corner_radius=8,
                  fg_color=ACCENT, hover_color='#3d63d1',
                  command=self.save_name).pack(fill='x')

        right_frame = CTkFrame(self, fg_color=BG_MAIN)
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)

        header = CTkFrame(right_frame, fg_color=BG_HEADER, corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky='ew')
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        self.status_dot = CTkLabel(header, text='●', text_color=OFFLINE,
                                    font=CTkFont(size=14), width=20)
        self.status_dot.grid(row=0, column=0, padx=(16, 0), pady=10)

        self.status_label = CTkLabel(header, text='Підключення...', anchor='w',
                                      text_color=TXT_MAIN,
                                      font=CTkFont(size=13, weight='bold'))
        self.status_label.grid(row=0, column=1, sticky='w', padx=8, pady=10)

        self.chat_field = CTkScrollableFrame(right_frame, fg_color=BG_MAIN,
                                              scrollbar_button_color=BG_HEADER,
                                              scrollbar_button_hover_color=ACCENT)
        self.chat_field.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)
        self.chat_field.grid_columnconfigure(0, weight=1)
        self.chat_field.bind('<Configure>', self.on_chat_resize, add='+')

        bottom_frame = CTkFrame(right_frame, fg_color=BG_PANEL, corner_radius=0)
        bottom_frame.grid(row=2, column=0, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = CTkEntry(
            bottom_frame, height=42, placeholder_text='Написати повідомлення...',
            fg_color=BG_INPUT, border_width=0, corner_radius=12,
            font=CTkFont(size=13))
        self.message_entry.grid(row=0, column=0, sticky='ew', padx=(12, 8), pady=12)
        self.message_entry.bind('<Return>', lambda event: self.send_message())

        self.send_button = CTkButton(
            bottom_frame, text='➜', width=44, height=42, corner_radius=12,
            fg_color=ACCENT, hover_color='#3d63d1', font=CTkFont(size=15),
            command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(0, 12), pady=12)

    def toggle_menu(self):
        self.is_menu_open = not self.is_menu_open
        if not self.is_menu_open:
            self.menu_content.pack_forget()
        self.animate_menu()

    def animate_menu(self):
        target = OPENW if self.is_menu_open else CLOSEDW
        current = self.menu_frame.winfo_width()

        if abs(current - target) <= STEP:
            self.menu_frame.configure(width=target)
            if self.is_menu_open:
                self.menu_content.pack(fill='x', padx=14, pady=14)
            return

        step = STEP if target > current else -STEP
        self.menu_frame.configure(width=current + step)
        self.after(8, self.animate_menu)

    # ---------- Chat rendering ----------

    def add_message(self, text, author=None, is_own=False, is_info=False):
        if is_info:
            row = CTkFrame(self.chat_field, fg_color='transparent')
            row.pack(fill='x', pady=6)
            CTkLabel(row, text=text, text_color=TXT_INFO, font=CTkFont(size=11)
                      ).pack(anchor='center')
            self.after(20, self.scroll_down)
            return

        outer = CTkFrame(self.chat_field, fg_color='transparent')
        outer.pack(fill='x', pady=3, anchor='e' if is_own else 'w')

        wrapper = CTkFrame(outer, fg_color='transparent')
        wrapper.pack(anchor='e' if is_own else 'w', padx=8)

        if not is_own and author:
            avatar = CTkLabel(wrapper, text=author[:1].upper(), width=30, height=30,
                              corner_radius=15, fg_color=avatar_color(author),
                              text_color='white', font=CTkFont(size=12, weight='bold'))
            avatar.grid(row=0, column=0, rowspan=2, sticky='n', padx=(0, 8))

        bubble = CTkFrame(wrapper, fg_color=BUBBLE_OWN if is_own else BUBBLE_OTHER,
                          corner_radius=14)
        col = 1 if (not is_own and author) else 0
        bubble.grid(row=0, column=col, sticky='e' if is_own else 'w')

        if author and not is_own:
            CTkLabel(bubble, text=author, anchor='w',
                     text_color='#c7d2fe' if is_own else '#a9b4c4',
                     font=CTkFont(size=11, weight='bold')
                     ).pack(fill='x', padx=12, pady=(8, 0))

        label = CTkLabel(bubble, text=text, justify='left', anchor='w',
                         wraplength=self.wraplength, text_color='white',
                         font=CTkFont(size=13))
        label.pack(fill='x', padx=12, pady=(2 if (author and not is_own) else 8, 4))

        time_label = CTkLabel(bubble, text=datetime.now().strftime('%H:%M'),
                              text_color='#c7d2fe' if is_own else TXT_MUTED,
                              font=CTkFont(size=9), anchor='e')
        time_label.pack(fill='x', padx=12, pady=(0, 6))

        self.message_labels.append(label)
        self.after(20, self.scroll_down)

    def on_chat_resize(self, event):
        self.wraplength = max(int(event.width * 0.55), 140)
        for label in self.message_labels:
            label.configure(wraplength=self.wraplength)

    def scroll_down(self):
        self.update_idletasks()
        self.chat_field._parent_canvas.yview_moveto(1.0)

    def set_status(self, connected, text):
        self.connected = connected
        self.status_dot.configure(text_color=ONLINE if connected else OFFLINE)
        self.status_label.configure(text=text)

    # ---------- Network ----------

    def connect(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except OSError as error:
            self.sock = None
            self.set_status(False, 'Немає з’єднання')
            self.add_message(f"Не вдалося підключитися до сервера: {error}", is_info=True)
            return

        self.set_status(True, self.username)
        Thread(target=self.receive_loop, daemon=True).start()
        self.send_line('NAME', self.username)

    def send_line(self, message_type, *parts):
        if not self.sock:
            self.add_message('Немає з’єднання із сервером', is_info=True)
            return
        line = SEPAR.join((message_type,) + parts) + END
        try:
            self.sock.sendall(line.encode(ENC))
        except OSError:
            self.sock = None
            self.set_status(False, 'З’єднання втрачено')
            self.add_message('З’єднання із сервером втрачено', is_info=True)

    def receive_loop(self):
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
        self.inbox.put(f"INFO{SEPAR}З’єднання із сервером втрачено")

    def process_inbox(self):
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
        text = parts[1]
        if 'втрачено' in text.lower() or 'не вдалося' in text.lower():
            self.set_status(False, 'Немає з’єднання')
        self.add_message(text, is_info=True)

    # ---------- Actions ----------

    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        self.message_entry.delete(0, 'end')
        self.send_line('TEXT', text)

    def save_name(self):
        new_name = self.name_entry.get().replace(SEPAR, '').strip()
        if not new_name or new_name == self.username:
            return
        self.username = new_name
        self.avatar_preview.configure(text=new_name[:1].upper(),
                                       fg_color=avatar_color(new_name))
        self.title(f"Chat — {new_name}")
        if self.connected:
            self.status_label.configure(text=new_name)
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