import colorsys
import random
import time
from queue import Empty, Queue
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread

from customtkinter import (
    CTk,
    CTkButton,
    CTkEntry,
    CTkFont,
    CTkFrame,
    CTkLabel,
    CTkScrollableFrame,
    CTkToplevel,
    get_appearance_mode,
    set_appearance_mode,
)

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

COLOR_OWN = '#2f6fdb'
COLOR_OTHER = '#3a3f46'
COLOR_INFO = '#2b2b2b'

# --- НАЛАШТУВАННЯ ОБМЕЖЕНЬ ---
MAX_MSG_LEN = 200  # Максимальна довжина повідомлення (в символах)
MAX_NAME_LEN = 20  # Максимальна довжина ніка
COOLDOWN_SEC = 1.0  # Затримка між повідомленнями у секундах (захист від спаму)


class ChatClient(CTk):
    def __init__(self):
        super().__init__()
        set_appearance_mode('dark')
        self.title('Chat Client')
        self.geometry('700x500')
        self.minsize(500, 350)

        self.username = USERNAME
        self.sock = None
        self.inbox = Queue()
        self.message_labels = []
        self.wraplength = 400

        # Змінна для відстеження часу останнього повідомлення (для кулдауну)
        self.last_msg_time = 0

        # Змінні для керування райдужною темою
        self.rainbow_active = False
        self.rainbow_hue = 0.0

        # Баланс для казіка
        self.casino_balance = 500

        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info,
        }

        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.process_inbox()
        self.after(100, self.connect)

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Бокове меню (всі налаштування та розваги тепер тут)
        self.is_menu_open = False
        self.menu_frame = CTkFrame(self, width=CLOSEDW, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, sticky='ns')
        self.menu_frame.pack_propagate(False)

        self.menu_button = CTkButton(self.menu_frame, text='▶', width=32,
                                     command=self.toggle_menu)
        self.menu_button.pack(anchor='w', padx=8, pady=10)

        # Використовуємо ScrollableFrame для меню, щоб все гарантовано помістилося
        self.menu_content = CTkScrollableFrame(self.menu_frame, fg_color='transparent')

        # --- Секція: Профіль ---
        CTkLabel(self.menu_content, text='Ваш нік', anchor='w', font=CTkFont(weight='bold')).pack(fill='x')
        self.name_entry = CTkEntry(self.menu_content, placeholder_text='Нік...')
        self.name_entry.pack(fill='x', pady=5)
        self.name_entry.insert(0, self.username)

        CTkButton(self.menu_content, text='Зберегти нік',
                  command=self.save_name).pack(fill='x', pady=(0, 15))

        # --- Секція: Теми оформлення ---
        CTkLabel(self.menu_content, text='Теми оформлення', anchor='w', font=CTkFont(weight='bold')).pack(fill='x')

        self.theme_button = CTkButton(self.menu_content, text='Світла / Темна',
                                      command=self.toggle_theme)
        self.theme_button.pack(fill='x', pady=5)

        self.rainbow_button = CTkButton(self.menu_content, text='🌈 Райдужна тема',
                                        fg_color='#ff4b5c', hover_color='#ff2a40',
                                        command=self.toggle_rainbow_theme)
        self.rainbow_button.pack(fill='x', pady=(5, 15))

        # --- Секція: Розваги (Казино) ---
        CTkLabel(self.menu_content, text='Розваги', anchor='w', font=CTkFont(weight='bold')).pack(fill='x')
        self.casino_btn = CTkButton(self.menu_content, text='🎰 Міні-казино',
                                    fg_color='#f39c12', hover_color='#d68910',
                                    command=self.open_casino)
        self.casino_btn.pack(fill='x', pady=5)

        # Основна область чату
        right_frame = CTkFrame(self, fg_color='transparent')
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        # Секція чату та вводу
        self.chat_field = CTkScrollableFrame(right_frame, fg_color='transparent')
        self.chat_field.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 0))
        self.chat_field.bind('<Configure>', self.on_chat_resize, add='+')

        # Нижня панель вводу
        bottom_frame = CTkFrame(right_frame, fg_color='transparent')
        bottom_frame.grid(row=1, column=0, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = CTkEntry(
            bottom_frame,
            height=40,
            placeholder_text=f'Введіть повідомлення (до {MAX_MSG_LEN} симв.):'
        )
        self.message_entry.grid(row=0, column=0, sticky='ew', padx=(10, 6), pady=(10, 2))
        self.message_entry.bind('<Return>', lambda event: self.send_message())
        self.message_entry.bind('<KeyRelease>', self.check_msg_length)

        # Лічильник символів під полем вводу
        self.char_counter = CTkLabel(
            bottom_frame,
            text=f'0 / {MAX_MSG_LEN}',
            text_color='gray',
            font=CTkFont(size=10)
        )
        self.char_counter.grid(row=1, column=0, sticky='w', padx=12, pady=(0, 5))

        self.send_button = CTkButton(
            bottom_frame,
            text='>',
            width=50,
            height=40,
            command=self.send_message
        )
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=(10, 2))

    def toggle_menu(self):
        if self.is_menu_open:
            self.menu_content.pack_forget()
            self.menu_button.configure(text='▶')
            self.animate_menu(OPENW, CLOSEDW, -STEP)
        else:
            self.animate_menu(CLOSEDW, OPENW, STEP)

    def animate_menu(self, current, target, step):
        current += step
        self.menu_frame.configure(width=current)
        if (step > 0 and current < target) or (step < 0 and current > target):
            self.after(10, lambda: self.animate_menu(current, target, step))
        else:
            self.menu_frame.configure(width=target)
            if step > 0:
                self.menu_content.pack(fill='both', expand=True, padx=5, pady=5)
                self.menu_button.configure(text='◀')
                self.is_menu_open = True
            else:
                self.is_menu_open = False

    def toggle_theme(self):
        if self.rainbow_active:
            self.toggle_rainbow_theme()

        current_mode = get_appearance_mode()
        if current_mode == 'Dark':
            set_appearance_mode('Light')
        else:
            set_appearance_mode('Dark')

    def toggle_rainbow_theme(self):
        self.rainbow_active = not self.rainbow_active
        if self.rainbow_active:
            self.rainbow_button.configure(text='🛑 Вимкнути райдугу')
            set_appearance_mode('Light')
            self.animate_rainbow_theme()
        else:
            self.rainbow_button.configure(text='🌈 Райдужна тема')
            set_appearance_mode('Dark')
            self.configure(fg_color=None)
            self.menu_frame.configure(fg_color=None)

    def animate_rainbow_theme(self):
        if not self.rainbow_active:
            return

        r_bg, g_bg, b_bg = colorsys.hsv_to_rgb(self.rainbow_hue, 0.2, 0.97)
        r_btn, g_btn, b_btn = colorsys.hsv_to_rgb(self.rainbow_hue, 0.6, 0.9)

        bg_hex = f'#{int(r_bg * 255):02x}{int(g_bg * 255):02x}{int(b_bg * 255):02x}'
        btn_hex = f'#{int(r_btn * 255):02x}{int(g_btn * 255):02x}{int(b_btn * 255):02x}'

        try:
            self.configure(fg_color=bg_hex)
            self.menu_frame.configure(fg_color=bg_hex)
            self.send_button.configure(fg_color=btn_hex, hover_color=btn_hex)
        except Exception:
            pass

        self.rainbow_hue = (self.rainbow_hue + 0.005) % 1.0
        self.after(100, self.animate_rainbow_theme)

    def check_msg_length(self, event=None):
        text = self.message_entry.get()
        if len(text) > MAX_MSG_LEN:
            self.message_entry.delete(MAX_MSG_LEN, 'end')
            text = self.message_entry.get()

        length = len(text)
        self.char_counter.configure(text=f'{length} / {MAX_MSG_LEN}')

        if length > MAX_MSG_LEN:
            self.char_counter.configure(text_color='#ff5555')
        else:
            self.char_counter.configure(text_color='gray')

    def save_name(self):
        new_name = self.name_entry.get().strip()
        if not new_name:
            return
        if len(new_name) > MAX_NAME_LEN:
            new_name = new_name[:MAX_NAME_LEN]
        self.username = new_name
        self.add_system_message(f"Нік змінено на: {self.username}")

    def on_chat_resize(self, event):
        self.wraplength = max(200, event.width - 100)
        for lbl in self.message_labels:
            lbl.configure(wraplength=self.wraplength)

    def add_system_message(self, text):
        lbl = CTkLabel(self.chat_field, text=text, text_color='gray', font=CTkFont(size=11))
        lbl.pack(pady=5)
        self.message_labels.append(lbl)

    def on_text(self, sender, text):
        align = 'w' if sender != self.username else 'e'
        color = COLOR_OWN if sender == self.username else COLOR_OTHER
        msg_text = f"{sender}:\n{text}"

        lbl = CTkLabel(
            self.chat_field,
            text=msg_text,
            fg_color=color,
            corner_radius=10,
            padx=10,
            pady=8,
            anchor=align,
            justify='left',
            wraplength=self.wraplength
        )
        lbl.pack(anchor=align, pady=4, padx=5)
        self.message_labels.append(lbl)

    def on_info(self, text):
        self.add_system_message(text)

    def send_message(self):
        if not self.sock:
            return

        current_time = time.time()
        if current_time - self.last_msg_time < COOLDOWN_SEC:
            return

        text = self.message_entry.get().strip()
        if not text:
            return

        if len(text) > MAX_MSG_LEN:
            text = text[:MAX_MSG_LEN]

        packet = f"TEXT{SEPAR}{self.username}{SEPAR}{text}{END}"
        try:
            self.sock.sendall(packet.encode(ENC))
            self.message_entry.delete(0, 'end')
            self.char_counter.configure(text=f'0 / {MAX_MSG_LEN}')
            self.last_msg_time = current_time
        except Exception:
            self.add_system_message("Помилка відправки повідомлення.")

    def open_casino(self):
        casino_win = CTkToplevel(self)
        casino_win.title('🎰 Міні-Казино')
        casino_win.geometry('320x380')
        casino_win.resizable(False, False)
        casino_win.grab_set()


        symbols = ['🍒', '🍋', '🔔', '⭐', '        ', '🥭']

        lbl_balance = CTkLabel(casino_win, text=f'Баланс: {self.casino_balance} 🪙',
                               font=CTkFont(size=16, weight='bold'))
        lbl_balance.pack(pady=15)

        slots_frame = CTkFrame(casino_win, fg_color='transparent')
        slots_frame.pack(pady=10)

        slot1 = CTkLabel(slots_frame, text='🍒', font=CTkFont(size=36), width=60, height=60, fg_color='#2b2b2b',
                         corner_radius=8)
        slot1.grid(row=0, column=0, padx=5)
        slot2 = CTkLabel(slots_frame, text='7️⃣', font=CTkFont(size=36), width=60, height=60, fg_color='#2b2b2b',
                         corner_radius=8)
        slot2.grid(row=0, column=1, padx=5)
        slot3 = CTkLabel(slots_frame, text='💎', font=CTkFont(size=36), width=60, height=60, fg_color='#2b2b2b',
                         corner_radius=8)
        slot3.grid(row=0, column=2, padx=5)

        bet_frame = CTkFrame(casino_win, fg_color='transparent')
        bet_frame.pack(pady=10)

        CTkLabel(bet_frame, text='Ставка:').pack(side='left', padx=5)
        entry_bet = CTkEntry(bet_frame, width=80)
        entry_bet.pack(side='left', padx=5)
        entry_bet.insert(0, '10')

        lbl_result = CTkLabel(casino_win, text='Зробіть ставку та крутіть!', font=CTkFont(size=12), text_color='gray')
        lbl_result.pack(pady=5)

        def spin():
            try:
                bet = int(entry_bet.get())
            except ValueError:
                lbl_result.configure(text='Введіть числове значення ставки!', text_color='#ff5555')
                return

            if bet <= 0:
                lbl_result.configure(text='Ставка має бути більше 0!', text_color='#ff5555')
                return

            if bet > self.casino_balance:
                lbl_result.configure(text='Недостатньо коштів на балансі!', text_color='#ff5555')
                return

            self.casino_balance -= bet

            res1 = random.choice(symbols)
            res2 = random.choice(symbols)
            res3 = random.choice(symbols)

            slot1.configure(text=res1)
            slot2.configure(text=res2)
            slot3.configure(text=res3)

            if res1 == res2 == res3:
                win_amount = bet * 10
                self.casino_balance += win_amount
                lbl_result.configure(text=f'Джекпот! Ви виграли {win_amount} 🪙!', text_color='#2ecc71')
            elif res1 == res2 or res2 == res3 or res1 == res3:
                win_amount = bet * 2
                self.casino_balance += win_amount
                lbl_result.configure(text=f'Виграш! Ви отримали {win_amount} 🪙!', text_color='#3498db')
            else:
                lbl_result.configure(text='На жаль, програш. Спробуйте ще!', text_color='#e74c3c')

            lbl_balance.configure(text=f'Баланс: {self.casino_balance} 🪙')

        btn_spin = CTkButton(casino_win, text='🎲 КРУТИТИ', fg_color='#27ae60', hover_color='#219653', command=spin)
        btn_spin.pack(pady=10)

        def share_to_chat():
            if not self.sock:
                lbl_result.configure(text='Немає підключення до чату!', text_color='#ff5555')
                return

            chat_text = f"🎰 [Казино] Баланс гравця: {self.casino_balance} 🪙 (Слоти крутнулися успішно!)"
            packet = f"TEXT{SEPAR}{self.username}{SEPAR}{chat_text}{END}"
            try:
                self.sock.sendall(packet.encode(ENC))
                lbl_result.configure(text='Результат надіслано в чат!', text_color='#2ecc71')
            except Exception:
                lbl_result.configure(text='Помилка відправки в чат.', text_color='#ff5555')

        btn_share = CTkButton(casino_win, text='💬 Надіслати в чат', fg_color='#2980b9', hover_color='#2471a3',
                              command=share_to_chat)
        btn_share.pack(pady=2)

    def connect(self):
        def worker():
            try:
                self.sock = socket(AF_INET, SOCK_STREAM)
                self.sock.connect((HOST, PORT))
                self.add_system_message("Підключено до сервера!")

                buffer = ""
                while True:
                    data = self.sock.recv(BUFF)
                    if not data:
                        break
                    buffer += data.decode(ENC)
                    while END in buffer:
                        packet, buffer = buffer.split(END, 1)
                        self.inbox.put(packet)
            except Exception:
                self.add_system_message("Не вдалося підключитися до сервера.")
            finally:
                if self.sock:
                    self.sock.close()
                    self.sock = None

        Thread(target=worker, daemon=True).start()

    def process_inbox(self):
        try:
            while True:
                packet = self.inbox.get_nowait()
                parts = packet.split(SEPAR, 2)
                cmd = parts[0]

                if cmd in self.handlers:
                    if cmd == 'TEXT' and len(parts) >= 3:
                        self.handlers[cmd](parts[1], parts[2])
                    elif cmd == 'INFO' and len(parts) >= 2:
                        self.handlers[cmd](parts[1])
        except Empty:
            pass
        finally:
            self.after(100, self.process_inbox)

    def on_close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.destroy()


if __name__ == '__main__':
    app = ChatClient()
    app.mainloop()