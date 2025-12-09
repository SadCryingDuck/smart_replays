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

from .globals import user32

import ctypes
from ctypes import wintypes
import winsound
from pathlib import Path
from datetime import datetime
from contextlib import suppress
import os

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT),
                ("dwTime", wintypes.DWORD)]


def _print(*values, sep: str | None = None, end: str | None = None, file=None, flush: bool = False):
    str_time = datetime.now().strftime(f"%d.%m.%Y %H:%M:%S")
    print(f"[{str_time}]", *values, sep=sep, end=end, file=file, flush=flush)


def get_active_window_pid() -> int | None:
    """
    Gets process ID of the current active window.
    """
    hwnd = user32.GetForegroundWindow()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def get_executable_path(pid: int) -> Path:
    """
    Gets path of process's executable.

    :param pid: process ID.
    :return: Executable path.
    """
    process_handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
    # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ

    if not process_handle:
        raise OSError(f"Process {pid} does not exist.")

    filename_buffer = ctypes.create_unicode_buffer(260)  # Windows path is 260 characters max.
    result = ctypes.windll.psapi.GetModuleFileNameExW(process_handle, None, filename_buffer, 260)
    ctypes.windll.kernel32.CloseHandle(process_handle)
    if result:
        return Path(filename_buffer.value)
    else:
        raise RuntimeError(f"Cannot get executable path for process {pid}.")


def play_sound(path: str | Path):
    """
    Plays sound using windows engine.

    :param path: path to sound (.wav)
    """
    with suppress(Exception):
        winsound.PlaySound(str(path), winsound.SND_ASYNC)


def get_time_since_last_input() -> int:
    """
    Gets the time (in seconds) since the last mouse or keyboard input.
    """
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        current_time = ctypes.windll.kernel32.GetTickCount()
        idle_time_ms = current_time - last_input_info.dwTime
        return idle_time_ms // 1000
    return 0


def create_hard_link(file_path: Path | str, links_folder: Path | str) -> None:
    """
    Creates a hard link for `file_path`.

    :param file_path: Original file path.
    :param links_folder: Folder where the link will be created.
    """
    link_path = Path(links_folder) / Path(file_path).name

    os.makedirs(str(links_folder), exist_ok=True)
    os.link(str(file_path), link_path)
