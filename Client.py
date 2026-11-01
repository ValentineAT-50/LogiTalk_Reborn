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
import random
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from customtkinter import (CTk, CTkButton, CTkEntry, CTkFrame, CTkLabel,
                           CTkScrollableFrame, CTkFont, set_appearance_mode)

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



COLOR_OWN = '#6699ff'
COLOR_OTHER = '#6699ff'
COLOR_INFO = '#6699ff'

t_nine = [
    "авжеж", "авто", "автобус", "ага", "ахах", "але",
    "більш", "близько", "блін", "брат", "брати", "будь",
    "буде", "будемо", "будеш", "буду", "будуть", "бувай",
    "був", "була", "було", "були", "бути", "бурмалда", "вас", "вау",
    "вам", "важкий", "важко", "важливий", "велика",
    "велике", "великий", "вечір", "вибач", "вибачте",
    "вільна", "вільний", "від", "віддати", "відразу",
    "відповідь", "відповісти", "вітаю", "він", "вона",
    "воно", "вони", "вода", "взяти", "вже", "вчора",
    "вулиця", "втомився", "втомилась", "вранці", "вдома",
    "вдень", "веселий", "воздухан", "гарна", "гарне", "гарний",
    "гаразд", "говориш", "говорю", "година", "гірша",
    "гірше", "гірший", "граю", "гроші", "дякую",
    "дякуючи", "далеко", "давати", "дати", "день", "де",
    "дивно", "дівчина", "дитина", "дім", "доброго",
    "добре", "добрий", "додому", "допомога", "допомогти",
    "дорога", "друг", "друзі", "дуже", "думаю", "думаєш",
    "документ", "жесть", "жінка", "жити", "завжди",
    "завтра", "зазвичай", "закрити", "зараз", "зайнята",
    "зайнятий", "зла", "злий", "знає", "знаєш", "знаю",
    "знати", "знову", "зробити", "зроблю", "зрозуміло",
    "звідси", "звідти", "згоден", "згодна", "зустріч",
    "іду", "їжа", "їхати", "їду", "їдеш", "їм", "їсти",
    "її", "іноді", "інтернет", "його", "йду", "кава",
    "каже", "кажу", "капец", "квартира", "коли", "кому",
    "кого", "ким", "ключі", "клас", "красивий", "краще",
    "краща", "кращий", "круто", "котрий", "купити",
    "кімната", "котость", "людина", "люди", "любити", "люблю",
    "ласка", "легко", "лише", "лол", "логіка", "магазин", "мама",
    "машина", "мабуть", "має", "маєш", "маємо", "маю",
    "майже", "малий", "мала", "мале", "мене", "мені",
    "менш", "мною", "місто", "місяць", "місце", "може",
    "можливий", "можливо", "можна", "можу", "можеш",
    "могти", "мрія", "мрії", "мармор", "мігну", "на", "навіть", "напевно", "наприклад",
    "написав", "написати", "нас", "нам", "не", "негайно",
    "нести", "новий", "нова", "нове", "ніч", "нічого",
    "ніколи", "ні", "нормально", "незвично", "неймовірно",
    "ну", "обожнюю", "окей", "окремо", "однак", "отримати",
    "отже", "ось", "ойой", "пам'ятати", "пака", "перед",
    "перепрошую", "після", "пішов", "пішла", "піти",
    "питання", "пити", "погано", "погоджуюсь", "поганий",
    "погана", "погане", "подруга", "подобається",
    "подзвонити", "поїзд", "поки", "потрібний", "працюю",
    "правда", "правильний", "принаймні", "приємно",
    "привіт", "приблизно", "прикольно", "прийду", "прийти",
    "прийшов", "проблема", "просто", "прошу", "проте",
    "пізніше", "пайтон", "пон", "потужно", "радий", "радісно", "раніше", "ранку",
    "разом", "рік", "робити", "роблю", "робиш", "робота",
    "рідко", "розуміти", "саме", "себе", "собі", "серйозно",
    "сестра", "сьогодні", "сім'я", "скільки", "скоро",
    "смішно", "сумно", "сумую", "супер", "старий", "стара",
    "старе", "спати", "справді", "справа", "справи", "сюди",
    "так", "таке", "також", "там", "тато", "телефон",
    "тепер", "тебе", "тобі", "тобою", "тоді", "той", "тому",
    "туди", "тут", "ти", "тиждень", "тільки", "увечері",
    "угу", "ух", "хаха", "хлопець", "хліб", "хочу",
    "хочеш", "хоча", "хоче", "хотів", "хотіла", "хто",
    "хвилина", "час", "чекай", "чекаю", "чоловік",
    "чудово", "чути", "чую", "чий", "чия", "чиє", "чиї",
    "чого", "чому", "черемша", "що", "швидкий", "швидко", "школа",
    "шкода", "ще", "щасливий", "як", "який", "яка", "яке",
    "які", "якого", "якому", "ясно", "&@#?...", "...", "siuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",
    "суууууууууууууууууууууууууууууууууууууууууууууууууууууууууууууууууууу", "анкарамессі"
]

non_lol = []
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

        # Повідомлення, які клієнт може прийняти
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
        self.menu_width = CLOSEDW
        self.menu_frame = CTkFrame(self, width=CLOSEDW, corner_radius=0)
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

        # T9: три підказки над полем введення
        self.t9_frame = CTkFrame(bottom_frame, fg_color='transparent')
        self.t9_frame.grid(row=0, column=0, columnspan=2, sticky='ew',
                           padx=10, pady=(4, 0))
        self.t9_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.t9_buttons = []
        for i in range(3):
            button = CTkButton(
                self.t9_frame, text='', height=28,
                command=lambda index=i: self.choose_t9_word(index)
            )
            button.grid(row=0, column=i, sticky='ew', padx=3)
            button.grid_remove()
            self.t9_buttons.append(button)

        self.message_entry = CTkEntry(
            bottom_frame, height=42, placeholder_text='Написати повідомлення...',
            fg_color=BG_INPUT, border_width=0, corner_radius=12,
            font=CTkFont(size=13))
        self.message_entry.grid(row=1, column=0, sticky='ew', padx=(10, 6), pady=10)
        self.message_entry.bind('<Return>', lambda event: self.send_message())
        self.message_entry.bind('<KeyRelease>', self.update_t9_suggestions)

        self.send_button = CTkButton(bottom_frame, text='>', width=50, height=40,
            command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=(0, 10), pady=10)

    def toggle_menu(self):
        self.is_menu_open = not self.is_menu_open
        if not self.is_menu_open:
            self.menu_content.pack_forget()
        self.animate_menu()

    def animate_menu(self):
        target = OPENW if self.is_menu_open else CLOSEDW
        current = self.menu_frame.winfo_width()

        if abs(self.menu_width - target) <= STEP:
            self.menu_width = target
            self.menu_frame.configure(width=target)
            if self.is_menu_open:
                self.menu_content.pack(fill='x', padx=14, pady=14)
            return

        step = STEP if target > self.menu_width else -STEP
        self.menu_width += step
        self.menu_frame.configure(width=self.menu_width)
        self.after(10, self.animate_menu)


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
        self.wraplength = max(int(event.width * 0.7), 160)
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
        # Збирання рядка до купи ТИП@частина1@частина2
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
        self.inbox.put(f"INFO{SEPAR}З’єднання із сервером втрачено")

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
        text = parts[1]
        if 'втрачено' in text.lower() or 'не вдалося' in text.lower():
            self.set_status(False, 'Немає з’єднання')
        self.add_message(text, is_info=True)

    def text_count(self):
        text2 = self.message_entry.get()
        count = len(text2)
        lol_index = count - 1
        non_lol.append(lol_index)



    def update_t9_suggestions(self, event=None):
        current_text = self.message_entry.get()
        prefix = current_text.split()[-1] if current_text and not current_text.endswith(' ') else ''

        matches = []
        if prefix:
            matches = [word for word in t_nine
                       if word.lower().startswith(prefix.lower())]
            matches = random.sample(matches, min(3, len(matches)))

        for index, button in enumerate(self.t9_buttons):
            if index < len(matches):
                button.configure(text=matches[index], state='normal')
                button.grid()
            else:
                button.configure(text='')
                button.grid_remove()

    def choose_t9_word(self, index):
        button = self.t9_buttons[index]
        word = button.cget('text')
        if not word:
            return

        current_text = self.message_entry.get()
        if current_text.endswith(' '):
            updated_text = current_text + word
        else:
            parts = current_text.rsplit(' ', 1)
            updated_text = (parts[0] + ' ' if len(parts) == 2 else '') + word

        self.message_entry.delete(0, 'end')
        self.message_entry.insert(0, updated_text + " ")
        self.message_entry.focus_set()
        self.update_t9_suggestions()

    def send_message(self):
        text = self.message_entry.get().strip()
        if not text:
            return
        self.message_entry.delete(0, 'end')
        self.update_t9_suggestions()
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