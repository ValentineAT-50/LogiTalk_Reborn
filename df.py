def add_message(self, text, author=None, is_own=False, is_info=False):
    if is_info:
        color = COLOR_INFO
    elif is_own:
        color = COLOR_OWN
    else:
        color = COLOR_OTHER

    message_frame = CTkFrame(
        self.chat_field,
        fg_color=color,
        corner_radius=10
    )

    message_frame.pack(
        anchor='e' if is_own else 'w',
        padx=5,
        pady=4
    )

    # Аватарка
    if author and self.avatar_image:
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

    if author:
        CTkLabel(
            content_frame,
            text=author,
            anchor='w',
            text_color='#e0e0e0',
            font=CTkFont(size=11, weight='bold')
        ).pack(
            fill='x',
            padx=10,
            pady=(6, 0)
        )

    label = CTkLabel(
        content_frame,
        text=text,
        justify='left',
        anchor='w',
        wraplength=self.wraplength,
        text_color='#9aa0a6' if is_info else 'white'
    )

    label.pack(
        fill='x',
        padx=10,
        pady=(2, 6)
    )

    self.message_labels.append(label)

    self.after(20, self.scroll_down)
