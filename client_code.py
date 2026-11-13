
from queue import Queue, Empty
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from tkinter import filedialog, colorchooser
from datetime import datetime

from PIL import Image, ImageTk
from customtkinter import (
    CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
    CTkScrollableFrame, CTkFont, set_appearance_mode
)

HOST = 'localhost'
PORT = 8080

USERNAME = 'Test1'
ENC = 'utf-8'
BUFF = 4096
SEPAR = '@'
END = '\n'

COLOR_OWN = '#2f6fdb'
COLOR_OTHER = '#3a3f46'
COLOR_INFO = '#2b2b2b'


class ChatClient(CTk):
    def __init__(self):
        super().__init__()

        set_appearance_mode('dark')
        self.title('LogiTalk Reborn')
        self.geometry('700x550')
        self.minsize(500, 350)

        self.username = USERNAME
        self.username_color = '#55b8ff'
        self.user_colors = {self.username: self.username_color}
        self.user_avatars = {}

        self.avatar_image = None
        self.avatar_path = None

        self.sock = None
        self.inbox = Queue()
        self.message_labels = []
        self.message_frames = []
        self.wraplength = 400

        self.is_typing = False
        self.typing_after_id = None
        self.typing_users = set()

        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info,
            'TYPING': self.on_typing,
            'COLOR': self.on_color,
        }

        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.process_inbox()
        self.after(100, self.connect)

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.menu_frame = CTkFrame(self, width=48, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, sticky='ns')
        self.menu_frame.grid_propagate(False)

        self.menu_open = False

        self.menu_button = CTkButton(
            self.menu_frame,
            text='▶',
            width=32,
            command=self.toggle_menu
        )
        self.menu_button.pack(anchor='w', padx=8, pady=10)

        self.menu_content = CTkFrame(
            self.menu_frame,
            fg_color='transparent'
        )

        CTkLabel(
            self.menu_content,
            text='Ваш нік',
            anchor='w'
        ).pack(fill='x')

        self.name_entry = CTkEntry(
            self.menu_content,
            placeholder_text='Нік...'
        )
        self.name_entry.pack(fill='x', pady=5)
        self.name_entry.insert(0, self.username)

        CTkButton(
            self.menu_content,
            text='Зберегти нік',
            command=self.save_name
        ).pack(fill='x', pady=5)

        CTkButton(
            self.menu_content,
            text='🎨 Колір нікнейму',
            command=self.choose_name_color
        ).pack(fill='x', pady=5)

        CTkButton(
            self.menu_content,
            text='🖼️ Обрати аватарку',
            command=self.choose_avatar
        ).pack(fill='x', pady=5)

        self.avatar_preview = CTkLabel(
            self.menu_content,
            text='Аватарка не вибрана'
        )
        self.avatar_preview.pack(pady=10)

        right_frame = CTkFrame(self, fg_color='transparent')
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        self.chat_field = CTkScrollableFrame(
            right_frame,
            fg_color='transparent'
        )
        self.chat_field.grid(
            row=0, column=0,
            sticky='nsew',
            padx=10, pady=(10, 0)
        )
        self.chat_field.bind(
            '<Configure>', self.on_chat_resize, add='+'
        )

        self.typing_label = CTkLabel(
            right_frame,
            text='',
            text_color='#9aa0a6',
            anchor='w'
        )
        self.typing_label.grid(
            row=1, column=0,
            sticky='ew',
            padx=15, pady=(3, 0)
        )

        bottom_frame = CTkFrame(
            right_frame,
            fg_color='transparent'
        )
        bottom_frame.grid(row=2, column=0, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = CTkEntry(
            bottom_frame,
            height=40,
            placeholder_text='Введіть повідомлення...'
        )
        self.message_entry.grid(
            row=0, column=0,
            sticky='ew',
            padx=(10, 6), pady=10
        )
        self.message_entry.bind(
            '<Return>', self.send_message
        )
        self.message_entry.bind(
            '<KeyRelease>', self.on_message_key
        )

        self.send_button = CTkButton(
            bottom_frame,
            text='➤',
            width=50,
            height=40,
            command=self.send_message
        )
        self.send_button.grid(
            row=0, column=1,
            padx=(0, 10), pady=10
        )

        right_frame.grid_rowconfigure(1, weight=0)
        right_frame.grid_rowconfigure(2, weight=0)

    def toggle_menu(self):
        self.menu_open = not self.menu_open

        if self.menu_open:
            self.menu_frame.configure(width=200)
            self.menu_button.configure(text='◀')
            self.menu_content.pack(
                fill='x', padx=10, pady=10
            )
        else:
            self.menu_content.pack_forget()
            self.menu_frame.configure(width=48)
            self.menu_button.configure(text='▶')

    def choose_name_color(self):
        result = colorchooser.askcolor(
            color=self.username_color,
            title='Колір нікнейму'
        )

        color = result[1]
        if not color:
            return

        self.username_color = color
        self.user_colors[self.username] = color
        self.send_line('COLOR', color)

        self.add_message(
            'Колір нікнейму змінено',
            is_info=True
        )

    def choose_avatar(self):
        path = filedialog.askopenfilename(
            title='Виберіть аватарку',
            filetypes=[
                ('Зображення', '*.png *.jpg *.jpeg *.webp')
            ]
        )

        if not path:
            return

        try:
            image = Image.open(path).convert('RGB')
            image.thumbnail((64, 64))

            avatar = ImageTk.PhotoImage(image)

            self.avatar_image = avatar
            self.avatar_path = path
            self.user_avatars[self.username] = avatar

            self.avatar_preview.configure(
                image=avatar,
                text=''
            )

            self.add_message(
                'Аватарку змінено',
                is_info=True
            )

        except Exception as error:
            self.add_message(
                f'Не вдалося відкрити аватарку: {error}',
                is_info=True
            )

    def on_message_key(self, event=None):
        text = self.message_entry.get().strip()

        if text and not self.is_typing:
            self.is_typing = True
            self.send_line('TYPING', '1')

        if self.typing_after_id is not None:
            self.after_cancel(self.typing_after_id)
            self.typing_after_id = None

        if text:
            self.typing_after_id = self.after(
                1500, self.stop_typing
            )
        else:
            self.stop_typing()

    def stop_typing(self):
        if self.typing_after_id is not None:
            self.after_cancel(self.typing_after_id)
            self.typing_after_id = None

        if self.is_typing:
            self.is_typing = False
            self.send_line('TYPING', '0')

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

    def on_color(self, parts):
        if len(parts) < 3:
            return

        author, color = parts[1], parts[2]
        self.user_colors[author] = color

        for frame in self.message_frames:
            for widget in frame.winfo_children():
                if (
                    isinstance(widget, CTkLabel)
                    and widget.cget('text') == author
                ):
                    widget.configure(text_color=color)

    def add_message(
        self, text, author=None,
        is_own=False, is_info=False
    ):
        color = (
            COLOR_INFO if is_info
            else COLOR_OWN if is_own
            else COLOR_OTHER
        )

        frame = CTkFrame(
            self.chat_field,
            fg_color=color,
            corner_radius=10
        )
        frame.pack(
            anchor='e' if is_own else 'w',
            padx=5, pady=4
        )
        self.message_frames.append(frame)

        if author:
            avatar = self.user_avatars.get(author)

            if avatar:
                CTkLabel(
                    frame,
                    image=avatar,
                    text=''
                ).pack(
                    side='left',
                    padx=(8, 4), pady=8
                )

            CTkLabel(
                frame,
                text=author,
                anchor='w',
                text_color=self.user_colors.get(
                    author, '#e0e0e0'
                ),
                font=CTkFont(size=11, weight='bold')
            ).pack(
                fill='x', padx=10, pady=(6, 0)
            )

        time_text = datetime.now().strftime('%H:%M')

        CTkLabel(
            frame,
            text=time_text,
            font=CTkFont(size=9),
            text_color='#b0b0b0'
        ).pack(anchor='e', padx=10, pady=(2, 0))

        label = CTkLabel(
            frame,
            text=text,
            justify='left',
            anchor='w',
            wraplength=self.wraplength,
            text_color='#9aa0a6' if is_info else 'white'
        )
        label.pack(
            fill='x', padx=10, pady=(2, 6)
        )

        self.message_labels.append(label)
        self.after(20, self.scroll_down)

    def on_chat_resize(self, event):
        self.wraplength = max(
            int(event.width * 0.7), 160
        )

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
            self.add_message(
                f'Не вдалося підключитися: {error}',
                is_info=True
            )
            return

        Thread(
            target=self.receive_loop,
            daemon=True
        ).start()

        self.send_line('NAME', self.username)
        self.send_line('COLOR', self.username_color)

    def send_line(self, message_type, *parts):
        if not self.sock:
            return

        line = SEPAR.join(
            (message_type,) + parts
        ) + END

        try:
            self.sock.sendall(line.encode(ENC))
        except OSError:
            self.add_message(
                'З’єднання із сервером втрачено',
                is_info=True
            )
            self.sock = None

    def receive_loop(self):
        buffer = ''

        while True:
            try:
                chunk = self.sock.recv(BUFF)
                if not chunk:
                    break

                buffer += chunk.decode(
                    ENC, errors='ignore'
                )

                while END in buffer:
                    line, buffer = buffer.split(END, 1)
                    self.inbox.put(line.strip())

            except OSError:
                break

        self.inbox.put(
            f'INFO{SEPAR}З’єднання із сервером втрачено'
        )

    def process_inbox(self):
        while True:
            try:
                line = self.inbox.get_nowait()
            except Empty:
                break

            self.handle_line(line)

        try:
            self.after(50, self.process_inbox)
        except Exception:
            pass

    def handle_line(self, line):
        if not line:
            return

        parts = line.split(SEPAR, 2)
        handler = self.handlers.get(parts[0])

        if handler:
            handler(parts)
        else:
            self.add_message(
                f'Невідоме повідомлення: {line}',
                is_info=True
            )

    def on_text(self, parts):
        if len(parts) < 3:
            return

        author, text = parts[1], parts[2]

        self.add_message(
            text,
            author=author,
            is_own=(author == self.username)
        )

    def on_info(self, parts):
        if len(parts) >= 2:
            self.add_message(
                parts[1], is_info=True
            )

    def send_message(self, event=None):
        text = self.message_entry.get().strip()

        if not text:
            return 'break'

        self.stop_typing()
        self.send_line('TEXT', text)
        self.message_entry.delete(0, 'end')

        return 'break'

    def save_name(self):
        new_name = self.name_entry.get().replace(
            SEPAR, ''
        ).strip()[:20]

        if not new_name or new_name == self.username:
            return

        old_name = self.username
        self.username = new_name

        self.user_colors[new_name] = self.user_colors.pop(
            old_name, self.username_color
        )

        if old_name in self.user_avatars:
            self.user_avatars[new_name] = (
                self.user_avatars.pop(old_name)
            )

        self.title(f'LogiTalk Reborn — {new_name}')
        self.send_line('NAME', new_name)
        self.send_line('COLOR', self.username_color)

    def on_close(self):
        self.stop_typing()

        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass

        self.destroy()


if __name__ == '__main__':
    app = ChatClient()
    app.mainloop()
