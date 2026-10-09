#  OBS Smart Replays is an OBS script that allows more flexible replay buffer management:
#  set the clip name depending on the current window, set the file name format, etc.
#  Copyright (C) 2024 qvvonk
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

import tkinter as tk
from tkinter import font as f

import ctypes
from ctypes import wintypes
import time
import sys

VREFRESH = 116
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
SLIDE_DURATION_SECONDS = 0.1
SLIDE_GAP_SECONDS = 0.04
SCROLL_START_DELAY_MS = 600
ctypes.windll.user32.GetDC.restype = wintypes.HDC
ctypes.windll.user32.GetDC.argtypes = (wintypes.HWND,)
ctypes.windll.user32.ReleaseDC.argtypes = (wintypes.HWND, wintypes.HDC)
ctypes.windll.gdi32.GetDeviceCaps.restype = ctypes.c_int
ctypes.windll.gdi32.GetDeviceCaps.argtypes = (wintypes.HDC, ctypes.c_int)


def make_overlay(window, previous_foreground) -> None:
    try:
        hwnd = int(window.wm_frame(), 16)
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        if previous_foreground and ctypes.windll.user32.GetForegroundWindow() == hwnd:
            ctypes.windll.user32.SetForegroundWindow(previous_foreground)
    except Exception:
        pass


def get_monitor_refresh_rate(default: int = 60) -> int:
    try:
        hdc = ctypes.windll.user32.GetDC(None)
        try:
            rate = ctypes.windll.gdi32.GetDeviceCaps(hdc, VREFRESH)
        finally:
            ctypes.windll.user32.ReleaseDC(None, hdc)
        if rate > 1:
            return rate
    except Exception:
        pass
    return default


# This part of the script uses only when it is run as a main program, not imported by OBS.
#
# You can run this script to show notification:
# python smart_replays.py <Notification Title> <Notification Text> <Notification Color>
class ScrollingText:
    def __init__(self,
                 canvas: tk.Canvas,
                 text,
                 visible_area_width,
                 start_pos,
                 font,
                 delay: int = 10,
                 speed=1,
                 on_finish_callback=None):
        """
        Scrolling text widget.

        :param canvas: canvas
        :param text: text
        :param visible_area_width: width of the visible area of the text
        :param start_pos: text's start position (most likely padding from left border)
        :param font: font
        :param delay: Delay between text moves (in ms)
        :param speed: scrolling speed
        :param on_finish_callback: callback function when text animation is finished
        """

        self.canvas = canvas
        self.text = text
        self.area_width = visible_area_width
        self.start_pos = start_pos
        self.font = font
        self.delay = delay
        self.speed = speed
        self.on_finish_callback = on_finish_callback

        self.text_width = font.measure(text)
        self.text_height = font.metrics("ascent") + font.metrics("descent")
        self.text_id = self.canvas.create_text(0, round(self.text_height / 2),
                                               anchor=tk.NW, text=self.text, font=self.font, fill="#ffffff")
        self.text_curr_pos = start_pos

    def update_scroll(self):
        if self.text_curr_pos + self.text_width > self.area_width:
            self.canvas.move(self.text_id, -self.speed, 0)
            self.text_curr_pos -= self.speed

            self.canvas.after(self.delay, self.update_scroll)
        else:
            if self.on_finish_callback:
                self.on_finish_callback()


class NotificationWindow:
    def __init__(self,
                 title: str,
                 message: str,
                 primary_color: str = "#78B900"):
        self.title = title
        self.message = message
        self.primary_color = primary_color
        self.bg_color = "#000000"
        self.fps = get_monitor_refresh_rate()
        self.previous_foreground = ctypes.windll.user32.GetForegroundWindow()

        self.root = tk.Tk()
        self.root.withdraw()
        self.window = tk.Toplevel(bg="#000001")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True, "-alpha", 0.99, "-transparentcolor", "#000001")

        self.scr_w, self.scr_h = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.wnd_w, self.wnd_h = round(self.scr_w / 6.4), round(self.scr_h / 12)
        self.wnd_x, self.wnd_y = self.scr_w - self.wnd_w, round(self.scr_h / 10)
        self.title_font_size = round(self.wnd_h / 5)
        self.message_font_size = round(self.wnd_h / 8)
        self.second_frame_padding_x = round(self.wnd_w / 40)
        self.message_right_padding = round(self.wnd_w / 40)
        self.content_frame_padding_x, self.content_frame_padding_y = (round(self.wnd_w / 40),
                                                                      round(self.wnd_h / 12))

        self.window.geometry(f"{self.wnd_w}x{self.wnd_h}+{self.wnd_x}+{self.wnd_y}")

        self.first_frame = tk.Frame(self.window, bg=self.primary_color, bd=0, width=1, height=self.wnd_h)
        self.first_frame.place(x=self.wnd_w-1, y=0)

        self.second_frame = tk.Frame(self.window, bg=self.bg_color, bd=0, width=1, height=self.wnd_h)
        self.second_frame.pack_propagate(False)
        self.second_frame.place(x=self.wnd_w-1, y=0)

        self.content_frame = tk.Frame(self.second_frame, bg=self.bg_color, bd=0, height=self.wnd_h)
        self.content_frame.pack(fill=tk.X,
                                padx=self.content_frame_padding_x,
                                pady=self.content_frame_padding_y)


        self.title_label = tk.Label(self.content_frame,
                                    text=self.title,
                                    font=("Bahnschrift", self.title_font_size, "bold"),
                                    bg=self.bg_color,
                                    fg=self.primary_color)
        self.title_label.pack(anchor=tk.W)


        self.canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack()
        self.canvas.update()
        make_overlay(self.window, self.previous_foreground)

        font = f.Font(family="Cascadia Mono", size=self.message_font_size)
        self.message = ScrollingText(canvas=self.canvas,
                                     text=message,
                                     visible_area_width=self.wnd_w - self.second_frame_padding_x,
                                     start_pos=self.second_frame_padding_x + self.message_right_padding,
                                     font=font,
                                     delay=10,
                                     speed=2,
                                     on_finish_callback=self.on_text_anim_finished_callback)


    def animate_frame(self, frame: tk.Frame, target_w, duration: float = SLIDE_DURATION_SECONDS):
        init_w = frame.winfo_width()
        steps = max(1, int(duration * self.fps))
        frame_delay = duration / steps

        for step in range(1, steps + 1):
            curr_w = round(init_w + (target_w - init_w) * step / steps)
            frame.config(width=curr_w)
            frame.place(x=self.wnd_w - curr_w, y=0)
            frame.update()
            time.sleep(frame_delay)

        frame.config(width=target_w)
        frame.place(x=self.wnd_w - target_w, y=0)
        frame.update()

    def show(self):
        self.animate_frame(self.first_frame, self.wnd_w)
        time.sleep(SLIDE_GAP_SECONDS)
        self.second_frame.lift()
        self.animate_frame(self.second_frame, self.wnd_w - self.second_frame_padding_x)
        self.root.after(SCROLL_START_DELAY_MS, self.message.update_scroll)
        self.root.mainloop()

    def close(self):
        self.animate_frame(self.second_frame, 0)
        time.sleep(SLIDE_GAP_SECONDS)
        self.animate_frame(self.first_frame, 0)
        self.window.destroy()
        self.root.destroy()

    def on_text_anim_finished_callback(self):
        time.sleep(2.5)
        self.close()


if __name__ == '__main__':
    t = sys.argv[1] if len(sys.argv) > 1 else "Test Title"
    m = sys.argv[2] if len(sys.argv) > 2 else "Test Message"
    color = sys.argv[3] if len(sys.argv) > 3 else "#76B900"
    NotificationWindow(t, m, color).show()
    sys.exit(0)
