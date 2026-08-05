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
from .script_helpers import notify_saving
from .tech import create_hard_link, log

from pathlib import Path
import obspython as obs
import os
import shutil
import time
import traceback


def move_clip_file(mode: ClipNamingModes | None = None) -> tuple[str, Path]:
    old_file_path = get_last_replay_file_name()
    log.debug(f"Old clip file path: {old_file_path}")
    if not old_file_path:
        raise FileNotFoundError("OBS did not return a replay file path.")

    clip_name = VARIABLES.pending_clip_name or gen_clip_base_name(mode)
    ext = Path(old_file_path).suffix
    filename_template = obs.obs_data_get_string(VARIABLES.script_settings,
                                                PN.PROP_CLIPS_FILENAME_TEMPLATE)
    filename = gen_filename(clip_name, filename_template) + ext

    new_folder = Path(get_base_path(script_settings=VARIABLES.script_settings))
    if obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_CLIPS_SAVE_TO_FOLDER):
        new_folder = new_folder / clip_name

    os.makedirs(str(new_folder), exist_ok=True)
    new_path = new_folder / filename
    new_path = ensure_unique_filename(new_path)
    log.debug(f"New clip file path: {new_path}")

    shutil.move(str(old_file_path), str(new_path))
    log.debug("Clip file successfully moved.")
    os.utime(new_folder)

    if obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_CLIPS_CREATE_LINKS):
        links_folder = obs.obs_data_get_string(VARIABLES.script_settings, PN.PROP_CLIPS_LINKS_FOLDER_PATH)
        try:
            create_hard_link(new_path, links_folder)
        except Exception:
            log.warning("Failed to create hard link.")
            log.debug(traceback.format_exc())
    return clip_name, new_path


def save_buffer_with_force_mode(mode: ClipNamingModes):
    """
    Sends a request to save the replay buffer and setting a specific clip naming mode.
    Can only be called using hotkeys.
    """
    if not obs.obs_frontend_replay_buffer_active():
        log.warning("Replay buffer is not running, there is nothing to save.")
        return

    if CONSTANTS.CLIPS_FORCE_MODE_LOCK.locked():
        waited = time.monotonic() - VARIABLES.save_requested_at
        if waited < CONSTANTS.SAVE_REQUEST_TIMEOUT_SECONDS:
            log.warning(f"A save has been in progress for {waited:.1f}s. This one was ignored.")
            return

        log.warning("The previous save never completed. Releasing the save lock.")
        VARIABLES.force_mode = None
        VARIABLES.instant_popup_shown = False
        VARIABLES.pending_clip_name = None
        CONSTANTS.CLIPS_FORCE_MODE_LOCK.release()

    CONSTANTS.CLIPS_FORCE_MODE_LOCK.acquire()
    VARIABLES.save_requested_at = time.monotonic()
    VARIABLES.force_mode = mode

    try:
        VARIABLES.pending_clip_name = gen_clip_base_name(mode)
        VARIABLES.instant_popup_shown = notify_saving(VARIABLES.pending_clip_name)
    except Exception:
        VARIABLES.pending_clip_name = None
        VARIABLES.instant_popup_shown = False
        log.warning("Failed to show the saving notification.")
        log.debug(traceback.format_exc())

    obs.obs_frontend_replay_buffer_save()
