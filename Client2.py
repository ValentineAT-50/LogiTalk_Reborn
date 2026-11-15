"""
Одне повідомлення - один рядок, частини розділені символом "@".

    Клієнт -> сервер:
        NAME@нік              задати або змінити нік
        TEXT@текст            надіслати повідомлення
        TYPING@1 / TYPING@0   почав / перестав друкувати

    Сервер -> клієнту:
        TEXT@нік@текст        чиєсь повідомлення
        INFO@текст            службове повідомлення
        TYPING@нік@1/0        хтось друкує / перестав
"""

from datetime import datetime
from queue import Queue, Empty
from random import choice
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from tkinter import StringVar
from tkinter.colorchooser import askcolor
from tkinter.filedialog import askopenfilename

from PIL import Image, ImageDraw, ImageOps
from customtkinter import (CTk, CTkButton, CTkEntry, CTkFrame, CTkImage, CTkLabel,
                           CTkScrollableFrame, CTkToplevel, CTkFont, set_appearance_mode)

HOST = 'localhost'
PORT = 8080

USERNAME = 'Test1'

ENC = 'utf-8'
BUFF = 4096
SEPAR = '@'
END = '\n'

# ---------- Меню ----------
OPENW = 220
CLOSEDW = 56
STEP = 18

# ---------- Кольори ----------
BG_MAIN = '#1a1d23'
BG_PANEL = '#15171c'
BG_HEADER = '#20242b'
BG_INPUT = '#262a32'

BUBBLE_OWN = '#4f7cff'
BUBBLE_OTHER = '#2b2f38'

TXT_MAIN = '#eef0f3'
TXT_MUTED = '#8b909b'
TXT_INFO = '#6f7480'

ACCENT = '#4f7cff'
ONLINE = '#3ddc84'
OFFLINE = '#e5534b'

DEFAULT_TEXT_COLOR = '#ffffff'

# ---------- Аватарки ----------
AVATAR_MENU = 56
AVATAR_MSG = 30
AVATAR_COLORS = ['#4f7cff', '#e5534b', '#3ddc84', '#f2b705',
                 '#9b5de5', '#00bbf9', '#f15bb5', '#ff7b54']

# ---------- "Друкує..." ----------
TYPING_TIMEOUT = 2000   # мс без натискань, після яких вважаємо, що людина перестала друкувати

# ---------- Ліміти ----------
MAX_MSG_LEN = 200
MAX_NAME_LEN = 20       # так само обрізає і сервер (NAME_LEN)

# ---------- Казино ----------
CASINO_START = 500
CASINO_SLOTS = 5
CASINO_SYMBOLS = ['🍒', '🍋', '🍇', '🍑', '🥔']
CASINO_PAYOUT = {5: 25, 4: 10, 3: 3}    # скільки однакових символів -> множник ставки
CASINO_SPIN_STEPS = 15

# ---------- T9 ----------
T9_COUNT = 3
T9_WORDS = [
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
    "які", "якого", "якому", "ясно", "...", "анкарамессі",
]


def avatar_color(name):
    # Один і той самий нік завжди отримує один і той самий колір
    return AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)]


def make_round_image(path, size):
    # Обрізає фото до квадрата по центру і робить його круглим.
    # Зображення беремо вдвічі більшим, щоб на екранах з масштабом 125-150% не було мила.
    real = size * 2
    image = ImageOps.fit(Image.open(path).convert('RGBA'), (real, real))
    mask = Image.new('L', (real, real), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, real, real), fill=255)
    image.putalpha(mask)
    return CTkImage(light_image=image, dark_image=image, size=(size, size))


class ChatClient(CTk):
    def __init__(self):
        super().__init__()
        set_appearance_mode('dark')
        self.title('LogiTalk Reborn')
        self.geometry('760x560')
        self.minsize(520, 520)
        self.configure(fg_color=BG_MAIN)

        self.username = USERNAME
        self.sock = None
        self.connected = False
        self.inbox = Queue()        # Черга, через яку потік передає рядки у вікно
        self.message_labels = []    # Список, щоб міняти перенос тексту при зміні розміру вікна
        self.wraplength = 420

        # Аватарка: поки фото не вибране - буквена
        self.avatar_path = None
        self.avatar_menu_img = None
        self.avatar_msg_img = None

        self.text_color = DEFAULT_TEXT_COLOR
        self.casino_balance = CASINO_START

        # "Друкує..."
        self.typing_users = set()
        self.is_typing = False
        self.typing_job = None

        # Повідомлення, які клієнт може прийняти
        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info,
            'TYPING': self.on_typing,
            'LOST': self.on_lost,   # внутрішнє: потік прийому повідомляє про розрив
        }

        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.process_inbox()        # перевірка черги
        self.after(100, self.connect)

    # ---------- UI ----------

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Бокове меню
        self.is_menu_open = False
        self.menu_width = CLOSEDW
        self.menu_job = None
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

        # Контейнер, у якому перестворюється аватарка (буква або фото)
        self.avatar_holder = CTkFrame(self.menu_content, fg_color='transparent')
        self.avatar_holder.pack(pady=(0, 8))
        self.refresh_avatar_preview()

        CTkButton(self.menu_content, text='Обрати аватарку', corner_radius=8,
                  fg_color=BG_INPUT, hover_color=BG_HEADER,
                  command=self.choose_avatar).pack(fill='x', pady=(0, 4))
        CTkButton(self.menu_content, text='Скинути аватарку', corner_radius=8,
                  fg_color='transparent', hover_color=BG_HEADER, text_color=TXT_MUTED,
                  command=self.reset_avatar).pack(fill='x', pady=(0, 12))

        self.name_entry = CTkEntry(self.menu_content, placeholder_text='Ваш нік',
                                   fg_color=BG_INPUT, border_width=0, corner_radius=8)
        self.name_entry.pack(fill='x', pady=(0, 8))
        self.name_entry.insert(0, self.username)

        CTkButton(self.menu_content, text='Зберегти', corner_radius=8,
                  fg_color=ACCENT, hover_color='#3d63d1',
                  command=self.save_name).pack(fill='x', pady=(0, 12))

        CTkLabel(self.menu_content, text='ПОВІДОМЛЕННЯ', anchor='w', text_color=TXT_MUTED,
                 font=CTkFont(size=11, weight='bold')).pack(fill='x', pady=(0, 8))

        self.color_button = CTkButton(self.menu_content, text='Колір тексту', corner_radius=8,
                                      fg_color=BG_INPUT, hover_color=BG_HEADER,
                                      text_color=self.text_color,
                                      command=self.choose_text_color)
        self.color_button.pack(fill='x')

        CTkLabel(self.menu_content, text='РОЗВАГИ', anchor='w', text_color=TXT_MUTED,
                 font=CTkFont(size=11, weight='bold')).pack(fill='x', pady=(12, 8))

        CTkButton(self.menu_content, text='🎰 Казино', corner_radius=8,
                  fg_color='#f39c12', hover_color='#d68910',
                  command=self.open_casino).pack(fill='x')

        # Права частина: шапка / чат / "друкує..." / поле введення
        right_frame = CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
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
        self.chat_field.grid(row=1, column=0, sticky='nsew', padx=6, pady=(6, 0))
        self.chat_field.bind('<Configure>', self.on_chat_resize, add='+')

        # Фіксована висота, щоб чат не стрибав, коли напис з'являється і зникає
        self.typing_label = CTkLabel(right_frame, text='', height=18, anchor='w',
                                     text_color=TXT_MUTED, font=CTkFont(size=11, slant='italic'))
        self.typing_label.grid(row=2, column=0, sticky='ew', padx=16)

        bottom_frame = CTkFrame(right_frame, fg_color=BG_PANEL, corner_radius=0)
        bottom_frame.grid(row=3, column=0, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)

        # T9: три підказки над полем введення (ховаються, коли підказок немає)
        self.t9_frame = CTkFrame(bottom_frame, fg_color='transparent')
        self.t9_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=(8, 0))
        self.t9_frame.grid_columnconfigure(tuple(range(T9_COUNT)), weight=1)
        self.t9_buttons = []
        for i in range(T9_COUNT):
            button = CTkButton(self.t9_frame, text='', height=28, corner_radius=8,
                               fg_color=BG_INPUT, hover_color=BG_HEADER,
                               command=lambda index=i: self.choose_t9_word(index))
            button.grid(row=0, column=i, sticky='ew', padx=3)
            self.t9_buttons.append(button)
        self.t9_frame.grid_remove()

        # Текст поля йде через StringVar: так ліміт спрацьовує і при вставці мишкою,
        # а не лише при натисканні клавіш
        self.entry_var = StringVar()
        self.message_entry = CTkEntry(
            bottom_frame, height=42, placeholder_text='Написати повідомлення...',
            textvariable=self.entry_var,
            fg_color=BG_INPUT, border_width=0, corner_radius=12,
            font=CTkFont(size=13))
        self.message_entry.grid(row=1, column=0, sticky='ew', padx=(12, 8), pady=(12, 2))
        self.message_entry.bind('<Return>', lambda event: self.send_message())
        self.message_entry.bind('<KeyRelease>', self.on_key)

        self.send_button = CTkButton(
            bottom_frame, text='➜', width=44, height=42, corner_radius=12,
            fg_color=ACCENT, hover_color='#3d63d1', font=CTkFont(size=15),
            command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=(0, 12), pady=(12, 2))

        self.char_counter = CTkLabel(bottom_frame, text=f'0 / {MAX_MSG_LEN}', anchor='w',
                                     text_color=TXT_MUTED, font=CTkFont(size=10))
        self.char_counter.grid(row=2, column=0, sticky='w', padx=16, pady=(0, 8))
        self.entry_var.trace_add('write', self.on_entry_change)

    def toggle_menu(self):
        self.is_menu_open = not self.is_menu_open
        if not self.is_menu_open:
            self.menu_content.pack_forget()
        # Якщо попередня анімація ще йде - зупиняємо її, щоб не було двох циклів одночасно
        if self.menu_job:
            self.after_cancel(self.menu_job)
        self.animate_menu()

    def animate_menu(self):
        # Ширину рахуємо власною змінною, а НЕ через winfo_width():
        # winfo_width() повертає реальні пікселі з урахуванням масштабу Windows (125%, 150%),
        # тому меню щоразу "перестрибувало" ціль і розширювалось безкінечно.
        target = OPENW if self.is_menu_open else CLOSEDW

        if abs(self.menu_width - target) <= STEP:
            self.menu_width = target
            self.menu_frame.configure(width=target)
            self.menu_job = None
            if self.is_menu_open:
                self.menu_content.pack(fill='x', padx=14, pady=(0, 14))
            return

        self.menu_width += STEP if target > self.menu_width else -STEP
        self.menu_frame.configure(width=self.menu_width)
        self.menu_job = self.after(10, self.animate_menu)

    # ---------- Аватарки ----------

    def make_avatar(self, parent, name, size, is_own):
        # Фото може бути лише у своєї аватарки, у всіх інших - буква на кольоровому колі
        if is_own and self.avatar_path:
            image = self.avatar_menu_img if size == AVATAR_MENU else self.avatar_msg_img
            return CTkLabel(parent, image=image, text='')

        return CTkLabel(parent, text=name[:1].upper(), width=size, height=size,
                        corner_radius=size // 2, fg_color=avatar_color(name),
                        text_color='white',
                        font=CTkFont(size=max(10, int(size * 0.38)), weight='bold'))

    def refresh_avatar_preview(self):
        # Перестворюємо віджет: CTkLabel не вміє нормально прибрати картинку через configure
        for child in self.avatar_holder.winfo_children():
            child.destroy()
        self.make_avatar(self.avatar_holder, self.username, AVATAR_MENU, is_own=True).pack()

    def choose_avatar(self):
        path = askopenfilename(
            parent=self, title='Оберіть аватарку',
            filetypes=[('Зображення', '*.png *.jpg *.jpeg *.webp *.bmp')])
        if not path:
            return

        try:
            self.avatar_menu_img = make_round_image(path, AVATAR_MENU)
            self.avatar_msg_img = make_round_image(path, AVATAR_MSG)
        except OSError as error:
            self.add_message(f"Не вдалося відкрити зображення: {error}", is_info=True)
            return

        self.avatar_path = path
        self.refresh_avatar_preview()

    def reset_avatar(self):
        self.avatar_path = None
        self.avatar_menu_img = None
        self.avatar_msg_img = None
        self.refresh_avatar_preview()

    # ---------- Колір тексту ----------

    def choose_text_color(self):
        # askcolor повертає ((r, g, b), '#rrggbb') або (None, None), якщо натиснули "Скасувати"
        color = askcolor(color=self.text_color, title='Колір тексту', parent=self)[1]
        if not color:
            return
        self.text_color = color
        self.color_button.configure(text_color=color)

    # ---------- Повідомлення в чаті ----------

    def add_message(self, text, author=None, is_own=False, is_info=False):
        if is_info:
            label = CTkLabel(self.chat_field, text=text, text_color=TXT_INFO,
                             font=CTkFont(size=11), wraplength=self.wraplength)
            label.pack(pady=6)
            self.message_labels.append(label)
            self.after(20, self.scroll_down)
            return

        side = 'e' if is_own else 'w'
        row = CTkFrame(self.chat_field, fg_color='transparent')
        row.pack(fill='x', pady=3)
        wrapper = CTkFrame(row, fg_color='transparent')
        wrapper.pack(anchor=side, padx=8)

        avatar = self.make_avatar(wrapper, author or '?', AVATAR_MSG, is_own)
        bubble = CTkFrame(wrapper, fg_color=BUBBLE_OWN if is_own else BUBBLE_OTHER,
                          corner_radius=14)

        # Своя аватарка праворуч від бульбашки, чужа - ліворуч
        if is_own:
            bubble.grid(row=0, column=0)
            avatar.grid(row=0, column=1, sticky='n', padx=(8, 0))
        else:
            avatar.grid(row=0, column=0, sticky='n', padx=(0, 8))
            bubble.grid(row=0, column=1)

        if not is_own:
            CTkLabel(bubble, text=author, anchor='w', text_color='#a9b4c4',
                     font=CTkFont(size=11, weight='bold')).pack(fill='x', padx=12, pady=(8, 0))

        label = CTkLabel(bubble, text=text, justify='left', anchor='w',
                         wraplength=self.wraplength,
                         text_color=self.text_color if is_own else 'white',
                         font=CTkFont(size=13))
        label.pack(fill='x', padx=12, pady=(8 if is_own else 2, 4))

        CTkLabel(bubble, text=datetime.now().strftime('%H:%M'), anchor='e',
                 text_color='#c7d2fe' if is_own else TXT_MUTED,
                 font=CTkFont(size=9)).pack(fill='x', padx=12, pady=(0, 6))

        self.message_labels.append(label)
        self.after(20, self.scroll_down)

    def on_chat_resize(self, event):
        # 0.55 а не 0.7, бо поруч з бульбашкою тепер ще аватарка
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

    # ---------- T9 ----------

    def update_t9_suggestions(self):
        current_text = self.message_entry.get()
        prefix = current_text.split()[-1] if current_text and not current_text.endswith(' ') else ''

        matches = []
        if prefix:
            # Перші збіги, а не випадкові - інакше підказки міняються на кожну літеру
            matches = [word for word in T9_WORDS
                       if word.startswith(prefix.lower())][:T9_COUNT]

        for index, button in enumerate(self.t9_buttons):
            if index < len(matches):
                button.configure(text=matches[index])
                button.grid()
            else:
                button.configure(text='')
                button.grid_remove()

        if matches:
            self.t9_frame.grid()
        else:
            self.t9_frame.grid_remove()

    def choose_t9_word(self, index):
        word = self.t9_buttons[index].cget('text')
        if not word:
            return

        parts = self.message_entry.get().rsplit(' ', 1)
        updated_text = (parts[0] + ' ' if len(parts) == 2 else '') + word

        self.message_entry.delete(0, 'end')
        self.message_entry.insert(0, updated_text + ' ')
        self.message_entry.focus_set()
        self.update_t9_suggestions()

    # ---------- Ліміт символів ----------

    def on_entry_change(self, *args):
        text = self.entry_var.get()
        if len(text) > MAX_MSG_LEN:
            text = text[:MAX_MSG_LEN]
            self.entry_var.set(text)    # це знову викличе цю функцію вже з коротким текстом
            return
        self.char_counter.configure(
            text=f'{len(text)} / {MAX_MSG_LEN}',
            text_color='#ff5555' if len(text) == MAX_MSG_LEN else TXT_MUTED)

    # ---------- Казино ----------

    def open_casino(self):
        win = CTkToplevel(self)
        win.title('🎰 Міні-казино')
        win.geometry('380x350')
        win.resizable(False, False)
        win.configure(fg_color=BG_MAIN)
        win.transient(self)
        win.after(100, win.grab_set)    # одразу після створення на Windows grab_set може впасти

        balance_label = CTkLabel(win, text=f'Баланс: {self.casino_balance} $',
                                 font=CTkFont(size=16, weight='bold'), text_color='#f1c40f')
        balance_label.pack(pady=(14, 6))

        CTkLabel(win, text='🎲 Звичайне казино (мін. 1$)',
                 font=CTkFont(size=12, weight='bold'), text_color=TXT_MAIN).pack(pady=5)

        slots_frame = CTkFrame(win, fg_color='transparent')
        slots_frame.pack(pady=5)
        slot_labels = []
        for i in range(CASINO_SLOTS):
            slot = CTkLabel(slots_frame, text=CASINO_SYMBOLS[i % len(CASINO_SYMBOLS)],
                            font=CTkFont(size=22), width=40, height=45,
                            fg_color=BG_INPUT, corner_radius=6)
            slot.grid(row=0, column=i, padx=3)
            slot_labels.append(slot)

        bet_entry = CTkEntry(win, width=90, placeholder_text='Ставка',
                             fg_color=BG_INPUT, border_width=0)
        bet_entry.pack(pady=8)
        bet_entry.insert(0, '10')

        result_label = CTkLabel(win, text='Зробіть ставку!', font=CTkFont(size=11),
                                text_color=TXT_MUTED)
        result_label.pack(pady=3)

        def finish_spin(result, bet):
            # Виграш нараховуємо навіть якщо вікно закрили під час прокрутки
            same = max(result.count(symbol) for symbol in set(result))
            win_amount = bet * CASINO_PAYOUT.get(same, 0)
            self.casino_balance += win_amount

            if not win.winfo_exists():
                return
            for slot, symbol in zip(slot_labels, result):
                slot.configure(text=symbol)
            balance_label.configure(text=f'Баланс: {self.casino_balance} $')
            result_label.configure(
                text=f'Виграш: {win_amount} $!' if win_amount else 'Програш!',
                text_color='#2ecc71' if win_amount else '#e74c3c')
            spin_button.configure(state='normal')

        def spin(steps_left, result, bet):
            if steps_left == 0 or not win.winfo_exists():
                finish_spin(result, bet)
                return
            for slot in slot_labels:
                slot.configure(text=choice(CASINO_SYMBOLS))
            win.after(80, spin, steps_left - 1, result, bet)

        def play():
            try:
                bet = int(bet_entry.get())
            except ValueError:
                result_label.configure(text='Введіть число!', text_color='#ff5555')
                return

            if self.casino_balance < 1:
                result_label.configure(text='Баланс порожній', text_color='#ff5555')
                return
            if bet < 1 or bet > self.casino_balance:
                result_label.configure(text='Помилка ставки!', text_color='#ff5555')
                return

            self.casino_balance -= bet
            balance_label.configure(text=f'Баланс: {self.casino_balance} $')
            result_label.configure(text='Крутимо...', text_color='#f39c12')
            spin_button.configure(state='disabled')

            result = [choice(CASINO_SYMBOLS) for _ in range(CASINO_SLOTS)]
            spin(CASINO_SPIN_STEPS, result, bet)

        spin_button = CTkButton(win, text='🎲 Крутити', fg_color='#27ae60',
                                hover_color='#219653', command=play)
        spin_button.pack(pady=8)

    # ---------- "Друкує..." ----------

    def on_key(self, event=None):
        self.update_t9_suggestions()
        self.typing_started()

    def typing_started(self):
        if not self.sock:
            return
        if not self.message_entry.get().strip():
            self.typing_stopped()
            return

        # Серверу пишемо лише один раз, на початку набору
        if not self.is_typing:
            self.is_typing = True
            self.send_line('TYPING', '1')

        # Кожне натискання відкладає "перестав друкувати" ще на TYPING_TIMEOUT
        if self.typing_job:
            self.after_cancel(self.typing_job)
        self.typing_job = self.after(TYPING_TIMEOUT, self.typing_stopped)

    def typing_stopped(self):
        if self.typing_job:
            self.after_cancel(self.typing_job)
            self.typing_job = None
        if self.is_typing:
            self.is_typing = False
            self.send_line('TYPING', '0')

    def update_typing_label(self):
        names = sorted(self.typing_users)
        if not names:
            text = ''
        elif len(names) == 1:
            text = f"{names[0]} друкує..."
        else:
            text = ', '.join(names) + ' друкують...'
        self.typing_label.configure(text=text)

    # ---------- Мережа ----------

    def connect(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except OSError as error:
            self.sock = None
            self.set_status(False, 'Немає зʼєднання')
            self.add_message(f"Не вдалося підключитися до сервера: {error}", is_info=True)
            return

        self.set_status(True, self.username)
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
            self.set_status(False, 'Зʼєднання втрачено')
            self.add_message('Зʼєднання із сервером втрачено', is_info=True)

    def receive_loop(self):
        # Окремий потік: лише кладе рядки в чергу, віджети тут не чіпаємо
        buffer = ''
        while True:
            try:
                chunk = self.sock.recv(BUFF)
            except (OSError, AttributeError):
                break
            if not chunk:
                break
            buffer += chunk.decode(ENC, errors='ignore')
            while END in buffer:
                line, buffer = buffer.split(END, 1)
                self.inbox.put(line.strip())
        self.inbox.put(f"LOST{SEPAR}Зʼєднання із сервером втрачено")

    def process_inbox(self):
        # Виводить все, що накопичилось у черзі
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
        # maxsplit=2: текст повідомлення сам може містити "@", його не ріжемо
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
        # Хто надіслав повідомлення - вже не друкує
        if author in self.typing_users:
            self.typing_users.discard(author)
            self.update_typing_label()
        self.add_message(text, author=author, is_own=(author == self.username))

    def on_info(self, parts):
        if len(parts) < 2:
            return
        self.add_message(parts[1], is_info=True)

    def on_typing(self, parts):
        if len(parts) < 3:
            return
        author, status = parts[1], parts[2]
        if author == self.username:
            return
        if status == '1':
            self.typing_users.add(author)
        else:
            self.typing_users.discard(author)
        self.update_typing_label()

    def on_lost(self, parts):
        self.sock = None
        self.is_typing = False
        self.typing_users.clear()
        self.update_typing_label()
        self.set_status(False, 'Зʼєднання втрачено')
        if len(parts) > 1:
            self.add_message(parts[1], is_info=True)

    # ---------- Дії ----------

    def send_message(self):
        text = self.message_entry.get().strip()[:MAX_MSG_LEN]
        if not text:
            return
        self.message_entry.delete(0, 'end')
        self.update_t9_suggestions()
        self.typing_stopped()
        # Своє повідомлення не виводимо одразу: сервер повертає його всім, і нам теж
        self.send_line('TEXT', text)

    def save_name(self):
        new_name = self.name_entry.get().replace(SEPAR, '').strip()[:MAX_NAME_LEN]
        if not new_name or new_name == self.username:
            return
        self.username = new_name
        self.refresh_avatar_preview()
        self.title(f"LogiTalk Reborn — {new_name}")
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