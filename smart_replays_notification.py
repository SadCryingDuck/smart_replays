import sys
import time
import tkinter as tk
from tkinter import font as f
from tkinter import messagebox


# -------------------- ui.py --------------------
# This part of the script is used only when it is run as a main program, not imported by OBS.
#
# You can run this script to show notification:
# python smart_replays.py <Notification Title> <Notification Text> <Notification Color>


class ScrollingText:
    def __init__(
        self,
        canvas: tk.Canvas,
        text: str,
        visible_area_width: int,
        start_pos: int,
        font: f.Font,
        pixels_per_second: float = 80.0,
        on_finish_callback=None,
    ):
        """
        Time-based scrolling text widget.

        :param canvas: Canvas to draw text on.
        :param text: Text to scroll.
        :param visible_area_width: Width of the visible area (clip border).
        :param start_pos: Initial X position of the text (usually left padding).
        :param font: Tkinter font instance.
        :param pixels_per_second: Horizontal scroll speed in pixels per second.
        :param on_finish_callback: Callback when text has fully scrolled.
        """
        self.canvas = canvas
        self.text = text
        self.area_width = visible_area_width
        self.start_pos = start_pos
        self.font = font
        self.px_per_sec = float(pixels_per_second)
        self.on_finish_callback = on_finish_callback

        self.text_width = font.measure(text)
        self.text_height = font.metrics('ascent') + font.metrics('descent')

        # Start at the requested position
        self.text_id = self.canvas.create_text(
            self.start_pos,
            round(self.text_height / 2),
            anchor=tk.NW,
            text=self.text,
            font=self.font,
            fill='#ffffff',
        )

        self._running = False
        self._last_time = 0.0
        self._pos_x = float(self.start_pos)

    def start(self) -> None:
        """Start scrolling."""
        if self._running:
            return
        self._running = True
        self._last_time = time.perf_counter()
        self._step()

    def stop(self) -> None:
        """Stop scrolling."""
        self._running = False

    def _step(self) -> None:
        """Single animation step (internal)."""
        if not self._running:
            return

        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now

        # How many pixels to move for elapsed time
        dx = -self.px_per_sec * dt
        self._pos_x += dx
        self.canvas.move(self.text_id, dx, 0)

        # End condition: right edge of text passed visible area
        if self._pos_x + self.text_width <= self.area_width:
            self._running = False
            if self.on_finish_callback:
                self.on_finish_callback()
            return

        # Schedule next frame (~60 FPS)
        self.canvas.after(16, self._step)


class NotificationWindow:
    def __init__(self, title: str, message: str, primary_color: str = '#78B900'):
        self.title = title
        self.message_text = message
        self.primary_color = primary_color
        self.bg_color = '#000000'

        self.root = tk.Tk()
        self.root.withdraw()
        self.window = tk.Toplevel(bg='#000001')
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True, '-alpha', 0.99, '-transparentcolor', '#000001')

        self.scr_w, self.scr_h = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.wnd_w, self.wnd_h = round(self.scr_w / 6.4), round(self.scr_h / 12)
        self.wnd_x, self.wnd_y = self.scr_w - self.wnd_w, round(self.scr_h / 10)
        self.title_font_size = round(self.wnd_h / 5)
        self.message_font_size = round(self.wnd_h / 8)
        self.second_frame_padding_x = round(self.wnd_w / 40)
        self.message_right_padding = round(self.wnd_w / 40)
        self.content_frame_padding_x, self.content_frame_padding_y = (
            round(self.wnd_w / 40),
            round(self.wnd_h / 12),
        )

        self.window.geometry(f'{self.wnd_w}x{self.wnd_h}+{self.wnd_x}+{self.wnd_y}')

        self.first_frame = tk.Frame(
            self.window,
            bg=self.primary_color,
            bd=0,
            width=1,
            height=self.wnd_h,
        )
        self.first_frame.place(x=self.wnd_w - 1, y=0)

        self.second_frame = tk.Frame(
            self.window,
            bg=self.bg_color,
            bd=0,
            width=1,
            height=self.wnd_h,
        )
        self.second_frame.pack_propagate(False)
        self.second_frame.place(x=self.wnd_w - 1, y=0)

        self.content_frame = tk.Frame(self.second_frame, bg=self.bg_color, bd=0, height=self.wnd_h)
        self.content_frame.pack(
            fill=tk.X,
            padx=self.content_frame_padding_x,
            pady=self.content_frame_padding_y,
        )

        self.title_label = tk.Label(
            self.content_frame,
            text=self.title,
            font=('Bahnschrift', self.title_font_size, 'bold'),
            bg=self.bg_color,
            fg=self.primary_color,
        )
        self.title_label.pack(anchor=tk.W)

        self.canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack()
        self.canvas.update_idletasks()

        msg_font = f.Font(family='Cascadia Mono', size=self.message_font_size)
        self.message = ScrollingText(
            canvas=self.canvas,
            text=self.message_text,
            visible_area_width=self.wnd_w - self.second_frame_padding_x,
            start_pos=self.second_frame_padding_x + self.message_right_padding,
            font=msg_font,
            pixels_per_second=80.0,  # adjust to taste
            on_finish_callback=self.on_text_anim_finished_callback,
        )

    def _animate_frame(
        self,
        frame: tk.Frame,
        target_w: int,
        duration_ms: int = 200,
        on_finish=None,
    ) -> None:
        start_w = frame.winfo_width()
        start_time = time.perf_counter()
        total = duration_ms / 1000.0
        sign = 1 if target_w >= start_w else -1
        delta = abs(target_w - start_w)

        if delta == 0:
            if on_finish:
                on_finish()
            return

        def step():
            t = time.perf_counter() - start_time
            if t >= total:
                frame.config(width=target_w)
                frame.place(x=self.wnd_w - target_w, y=0)
                if on_finish:
                    on_finish()
                return

            k = t / total
            curr_w = start_w + sign * int(delta * k)

            frame.config(width=curr_w)
            frame.place(x=self.wnd_w - curr_w, y=0)

            self.window.after(1, step)

        step()

    def show(self) -> None:
        """Show window with animated slide-in and start text scrolling."""
        self._animate_frame(
            self.first_frame,
            self.wnd_w,
            duration_ms=300,
            on_finish=self._show_second_frame,
        )
        self.root.mainloop()

    def _show_second_frame(self) -> None:
        def start_second():
            self.second_frame.lift()
            self._animate_frame(
                self.second_frame,
                self.wnd_w - self.second_frame_padding_x,
                duration_ms=220,
                on_finish=self._start_message_scroll,
            )

        # small pause between first and second frames
        self.window.after(100, start_second)

    def _start_message_scroll(self) -> None:
        self.message.start()

    def close(self) -> None:
        """Close window with reverse animation."""
        def hide_first():
            self._animate_frame(
                self.first_frame,
                0,
                duration_ms=180,
                on_finish=self._destroy,
            )

        self._animate_frame(
            self.second_frame,
            0,
            duration_ms=200,
            on_finish=lambda: self.window.after(100, hide_first),
        )

    def _destroy(self) -> None:
        self.window.destroy()
        self.root.destroy()

    def on_text_anim_finished_callback(self) -> None:
        # wait 2.5 seconds, then close (non-blocking)
        self.window.after(2500, self.close)


def show_error_window(error_text: str):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    messagebox.showerror('[Smart Replays] - Error', error_text)
    root.destroy()


def main():
    if len(sys.argv) < 2:
        sys.exit()

    if sys.argv[1] == 'error':
        text = sys.argv[2] if len(sys.argv) > 2 else 'Error'
        show_error_window(text)
    elif sys.argv[1] == 'notification':
        t = sys.argv[2] if len(sys.argv) > 2 else 'Test Title'
        m = sys.argv[3] if len(sys.argv) > 3 else 'Test Message'
        color = sys.argv[4] if len(sys.argv) > 4 else '#76B900'
        NotificationWindow(t, m, color).show()
    sys.exit(0)


if __name__ == '__main__':
    main()
