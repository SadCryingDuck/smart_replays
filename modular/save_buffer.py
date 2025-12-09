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

from .globals import VARIABLES, CONSTANTS, PN, ClipNamingModes
from .obs_related import get_last_replay_file_name, get_base_path
from .clipname_gen import gen_clip_base_name, gen_filename, ensure_unique_filename
from .tech import _print, create_hard_link

from pathlib import Path
import obspython as obs
import os


def move_clip_file(mode: ClipNamingModes | None = None) -> tuple[str, Path]:
    old_file_path = get_last_replay_file_name()
    _print(f"Old clip file path: {old_file_path}")

    clip_name = gen_clip_base_name(mode)
    ext = old_file_path.split(".")[-1]
    filename_template = obs.obs_data_get_string(VARIABLES.script_settings,
                                                PN.PROP_CLIPS_FILENAME_TEMPLATE)
    filename = gen_filename(clip_name, filename_template) + f".{ext}"

    new_folder = Path(get_base_path(script_settings=VARIABLES.script_settings))
    if obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_CLIPS_SAVE_TO_FOLDER):
        new_folder = new_folder / clip_name

    os.makedirs(str(new_folder), exist_ok=True)
    new_path = new_folder / filename
    new_path = ensure_unique_filename(new_path)
    _print(f"New clip file path: {new_path}")

    os.rename(old_file_path, str(new_path))
    _print("Clip file successfully moved.")

    if obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_CLIPS_CREATE_LINKS):
        links_folder = obs.obs_data_get_string(VARIABLES.script_settings, PN.PROP_CLIPS_LINKS_FOLDER_PATH)
        create_hard_link(new_path, links_folder)
    return clip_name, new_path


def save_buffer_with_force_mode(mode: ClipNamingModes):
    """
    Sends a request to save the replay buffer and setting a specific clip naming mode.
    Can only be called using hotkeys.
    """
    if not obs.obs_frontend_replay_buffer_active():
        return

    if CONSTANTS.CLIPS_FORCE_MODE_LOCK.locked():
        return

    CONSTANTS.CLIPS_FORCE_MODE_LOCK.acquire()
    VARIABLES.force_mode = mode
    obs.obs_frontend_replay_buffer_save()
