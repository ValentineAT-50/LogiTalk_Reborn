import colorsys
import random
import time
from queue import Empty, Queue
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread

from customtkinter import (CTk, CTkButton, CTkEntry, CTkFont, CTkFrame, CTkLabel,
                           CTkScrollableFrame, CTkToplevel, get_appearance_mode, set_appearance_mode)

HOST = 'localhost'
PORT = 8080

USERNAME = 'Test1'

ENC = 'utf-8'
BUFF = 4096
SEPAR = '@'
END = '\n'

MAX_MSG_LEN = 200
MAX_NAME_LEN = 20
COOLDOWN_SEC = 1.0


class ChatClient(CTk):
    def __init__(self):
        super().__init__()
        set_appearance_mode('dark')
        self.title('Chat Client')
        self.geometry('600x450')
        self.minsize(450, 300)

        self.username = USERNAME
        self.sock = None
        self.inbox = Queue()
        self.message_labels = []
        self.last_msg_time = 0
        self.casino_balance = 500

        # Для райдужної теми
        self.rainbow_active = False
        self.rainbow_hue = 0.0

        # Обробники команд згідно з вашим сервером
        self.handlers = {
            'TEXT': self.on_text,
            'INFO': self.on_info
        }

        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.process_inbox()
        self.after(100, self.connect)

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Бокове меню
        self.menu_frame = CTkFrame(self, width=160, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, sticky='ns')
        self.menu_frame.pack_propagate(False)

        menu_content = CTkScrollableFrame(self.menu_frame, fg_color='transparent')
        menu_content.pack(fill='both', expand=True, padx=5, pady=5)

        CTkLabel(menu_content, text='Профіль', font=CTkFont(weight='bold')).pack(anchor='w')
        self.name_entry = CTkEntry(menu_content, placeholder_text='Нік...')
        self.name_entry.pack(fill='x', pady=5)
        self.name_entry.insert(0, self.username)
        CTkButton(menu_content, text='Зберегти', command=self.save_name).pack(fill='x', pady=(0, 15))

        CTkLabel(menu_content, text='Оформлення', font=CTkFont(weight='bold')).pack(anchor='w')
        CTkButton(menu_content, text='Світла / Темна', command=self.toggle_theme).pack(fill='x', pady=5)

        # Кнопка райдужної теми
        self.rainbow_button = CTkButton(menu_content, text='🌈 LGBT тема', fg_color='#ff4b5c', hover_color='#ff2a40',
                                        command=self.toggle_rainbow_theme)
        self.rainbow_button.pack(fill='x', pady=(0, 15))

        CTkLabel(menu_content, text='Розваги', font=CTkFont(weight='bold')).pack(anchor='w')
        CTkButton(menu_content, text='🎰 Казино', fg_color='#f39c12', hover_color='#d68910',
                  command=self.open_casino).pack(fill='x', pady=5)

        # Основна область чату
        right_frame = CTkFrame(self, fg_color='transparent')
        right_frame.grid(row=0, column=1, sticky='nsew')
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        self.chat_field = CTkScrollableFrame(right_frame, fg_color='transparent')
        self.chat_field.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 0))

        # Нижня панель вводу
        bottom_frame = CTkFrame(right_frame, fg_color='transparent')
        bottom_frame.grid(row=1, column=0, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = CTkEntry(bottom_frame, height=35, placeholder_text=f'Повідомлення (до {MAX_MSG_LEN})...')
        self.message_entry.grid(row=0, column=0, sticky='ew', padx=(10, 5), pady=5)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.message_entry.bind('<KeyRelease>', self.check_msg_length)

        self.char_counter = CTkLabel(bottom_frame, text=f'0 / {MAX_MSG_LEN}', text_color='gray', font=CTkFont(size=10))
        self.char_counter.grid(row=1, column=0, sticky='w', padx=12, pady=(0, 5))

        self.send_button = CTkButton(bottom_frame, text='>', width=40, height=35, command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(0, 10), pady=5)

    def toggle_theme(self):
        if self.rainbow_active:
            self.toggle_rainbow_theme()
        set_appearance_mode('Light' if get_appearance_mode() == 'Dark' else 'Dark')

    def toggle_rainbow_theme(self):
        self.rainbow_active = not self.rainbow_active
        if self.rainbow_active:
            self.rainbow_button.configure(text='🛑 Вимкнути райдугу')
            set_appearance_mode('Light')
            self.animate_rainbow_theme()
        else:
            self.rainbow_button.configure(text='🌈 LGBT тема')
            set_appearance_mode('Dark')
            self.configure(fg_color=None)
            self.menu_frame.configure(fg_color=None)
            self.send_button.configure(fg_color=None, hover_color=None)

    def animate_rainbow_theme(self):
        if not self.rainbow_active: return
        r_bg, g_bg, b_bg = colorsys.hsv_to_rgb(self.rainbow_hue, 0.2, 0.97)
        r_btn, g_btn, b_btn = colorsys.hsv_to_rgb(self.rainbow_hue, 0.6, 0.9)
        bg_hex = f'#{int(r_bg * 255):02x}{int(g_bg * 255):02x}{int(b_bg * 255):02x}'
        btn_hex = f'#{int(r_btn * 255):02x}{int(g_btn * 255):02x}{int(b_btn * 255):02x}'
        try:
            self.configure(fg_color=bg_hex)
            self.menu_frame.configure(fg_color=bg_hex)
            self.send_button.configure(fg_color=btn_hex, hover_color=btn_hex)
        except:
            pass
        self.rainbow_hue = (self.rainbow_hue + 0.005) % 1.0
        self.after(100, self.animate_rainbow_theme)

    def check_msg_length(self, event=None):
        text = self.message_entry.get()
        if len(text) > MAX_MSG_LEN:
            self.message_entry.delete(MAX_MSG_LEN, 'end')
            text = self.message_entry.get()
        self.char_counter.configure(text=f'{len(text)} / {MAX_MSG_LEN}',
                                    text_color='#ff5555' if len(text) == MAX_MSG_LEN else 'gray')

    def save_name(self):
        new_name = self.name_entry.get().strip()[:MAX_NAME_LEN]
        if new_name:
            self.username = new_name
            if self.sock:
                try:
                    # Сервер очікує: NAME@нік + \n
                    packet = f"NAME{SEPAR}{new_name}{END}"
                    self.sock.sendall(packet.encode(ENC))
                except:
                    self.add_system_message("Помилка зміни ніку.")

    def add_system_message(self, text):
        lbl = CTkLabel(self.chat_field, text=text, text_color='gray', font=CTkFont(size=11))
        lbl.pack(pady=3)
        self.message_labels.append(lbl)

    def on_text(self, sender, text):
        align = 'w' if sender != self.username else 'e'
        color = '#2f6fdb' if sender == self.username else '#3a3f46'
        lbl = CTkLabel(self.chat_field, text=f"{sender}:\n{text}", fg_color=color, corner_radius=8, padx=8, pady=6,
                       anchor=align, justify='left', wraplength=350)
        lbl.pack(anchor=align, pady=3, padx=5)
        self.message_labels.append(lbl)

    def on_info(self, text):
        self.add_system_message(text)

    def send_message(self):
        if not self.sock or time.time() - self.last_msg_time < COOLDOWN_SEC: return
        text = self.message_entry.get().strip()[:MAX_MSG_LEN]
        if not text: return
        try:
            # Сервер очікує: TEXT@текст + \n
            packet = f"TEXT{SEPAR}{text}{END}"
            self.sock.sendall(packet.encode(ENC))
            self.message_entry.delete(0, 'end')
            self.char_counter.configure(text=f'0 / {MAX_MSG_LEN}')
            self.last_msg_time = time.time()
        except:
            self.add_system_message("Помилка відправки.")

    def open_casino(self):
        win = CTkToplevel(self)
        win.title('🎰 Міні-казино')
        win.geometry('380x350')
        win.resizable(False, False)
        win.grab_set()

        lbl_bal = CTkLabel(win, text=f'Баланс: {self.casino_balance} $', font=CTkFont(size=16, weight='bold'),
                           text_color='#f1c40f')
        lbl_bal.pack(pady=10)

        # 5 слотів казино
        CTkLabel(win, text='🎲 Звичайне казино (мін. 1$)', font=CTkFont(size=12, weight='bold')).pack(pady=5)
        f1 = CTkFrame(win, fg_color='transparent')
        f1.pack(pady=5)
        slot_lbls = [
            CTkLabel(f1, text=s, font=CTkFont(size=22), width=40, height=45, fg_color='#2b2b2b', corner_radius=6) for s
            in ['🍒', '7️⃣', '💎', '⭐', '🔔']]
        for i, l in enumerate(slot_lbls): l.grid(row=0, column=i, padx=3)

        entry_bet = CTkEntry(win, width=90, placeholder_text='Ставка')
        entry_bet.pack(pady=8)
        entry_bet.insert(0, '10')

        lbl_res = CTkLabel(win, text='Зробіть ставку!', font=CTkFont(size=11), text_color='gray')
        lbl_res.pack(pady=3)

        def animate_spin(final_res, steps_left, bet, btn_spin):
            syms = ['🍆', '🍋', '🍇', '🍑', '🥔']
            if steps_left > 0:
                for l in slot_lbls:
                    l.configure(text=random.choice(syms))
                win.after(80, lambda: animate_spin(final_res, steps_left - 1, bet, btn_spin))
            else:
                for i, r in enumerate(final_res):
                    slot_lbls[i].configure(text=r)

                max_same = max(final_res.count(s) for s in set(final_res))
                win_amt = bet * 25 if max_same == 5 else (
                    bet * 10 if max_same == 4 else (bet * 3 if max_same == 3 else 0))

                self.casino_balance += win_amt
                lbl_bal.configure(text=f'Баланс: {self.casino_balance} $')
                lbl_res.configure(text=f'Виграш: {win_amt} $!' if win_amt else 'Програш!',
                                  text_color='#2ecc71' if win_amt else '#e74c3c')

                btn_spin.configure(state='normal')

        def play():
            try:
                bet = int(entry_bet.get())
            except ValueError:
                return lbl_res.configure(text='Введіть число!', text_color='#ff5555')

            if bet < 1 or bet > self.casino_balance:
                return lbl_res.configure(text='Помилка ставки!', text_color='#ff5555')

            self.casino_balance -= bet
            lbl_bal.configure(text=f'Баланс: {self.casino_balance} $')
            lbl_res.configure(text='Крутимо...', text_color='#f39c12')

            btn_spin.configure(state='disabled')
            syms = ['🍆', '🍋', '🍇', '🍑', '🥔']
            final_res = [random.choice(syms) for _ in range(5)]

            animate_spin(final_res, 15, bet, btn_spin)

        btn_spin = CTkButton(win, text='🎲 Крутити', fg_color='#27ae60', hover_color='#219653', command=play)
        btn_spin.pack(pady=8)

    def connect(self):
        def worker():
            try:
                self.sock = socket(AF_INET, SOCK_STREAM)
                self.sock.connect((HOST, PORT))

                # Відправляємо нік серверу одразу після підключення
                init_packet = f"NAME{SEPAR}{self.username}{END}"
                self.sock.sendall(init_packet.encode(ENC))

                buffer = ""
                while True:
                    data = self.sock.recv(BUFF)
                    if not data: break
                    buffer += data.decode(ENC)
                    while END in buffer:
                        packet, buffer = buffer.split(END, 1)
                        self.inbox.put(packet.strip())
            except:
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
                # Сервер надсилає TEXT@нік@текст або INFO@текст
                # Використовуємо maxsplit=2, оскільки текст повідомлення може містити '@'
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
            except:
                pass
        self.destroy()


if __name__ == '__main__':
    ChatClient().mainloop()