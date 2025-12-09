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


from .globals import VARIABLES
from .obs_related import get_replay_buffer_max_time, restart_replay_buffering
from .tech import get_time_since_last_input, get_active_window_pid, get_executable_path, _print

import obspython as obs
from threading import Thread
from contextlib import suppress


def restart_replay_buffering_callback():
    """
    Restarts replay buffering and adds itself to obs timer.

    This callback is only called by the obs timer.
    """
    _print("Restart replay buffering callback.")
    obs.timer_remove(restart_replay_buffering_callback)

    replay_length = get_replay_buffer_max_time()
    last_input_time = get_time_since_last_input()
    if last_input_time < replay_length:
        next_call = int((replay_length - last_input_time) * 1000)
        next_call = next_call if next_call >= 2000 else 2000

        _print(f"Replay length ({replay_length}s) is greater then time since last input ({last_input_time}s). Next call in {next_call / 1000}s.")
        obs.timer_add(restart_replay_buffering_callback, next_call)
        return

    # IMPORTANT
    # I don't know why, but it seems like stopping and starting replay buffering should be in the separate thread.
    # Otherwise it can "stuck" at stopping state.
    Thread(target=restart_replay_buffering, daemon=True).start()
    # I don't re-add this callback to timer again, cz it will be automatically added in on buffering start callback.


def append_clip_exe_history():
    """
    Adds current active executable path in clip exe history.
    """
    with suppress(Exception):
        pid = get_active_window_pid()
        exe = get_executable_path(pid)
        VARIABLES.clip_exe_history.appendleft(exe)


def append_video_exe_history():
    """
    Adds current active executable path in video exe history.
    """
    with suppress(Exception):
        pid = get_active_window_pid()
        exe = get_executable_path(pid)
        VARIABLES.video_exe_history[exe] += 1
