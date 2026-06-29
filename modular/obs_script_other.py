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

from .globals import VARIABLES, CONSTANTS, ClipNamingModes, PopupPathDisplayModes, PN

from .tech import log, setup_logging
from .obs_related import get_base_path
from .other_callbacks import restart_replay_buffering_callback, append_clip_exe_history
from .obs_events_callbacks import (on_buffer_save_callback,
                                   on_buffer_recording_started_callback,
                                   on_buffer_recording_stopped_callback)
from .script_helpers import load_aliases
from .updates_check import check_updates_in_background
from .hotkeys import load_hotkeys

import obspython as obs
import json


def script_defaults(s):
    log.debug("Loading default values...")
    obs.obs_data_set_default_string(s, PN.PROP_CLIPS_BASE_PATH, str(get_base_path()))
    obs.obs_data_set_default_int(s, PN.PROP_CLIPS_NAMING_MODE, ClipNamingModes.CURRENT_PROCESS.value)
    obs.obs_data_set_default_string(s, PN.PROP_CLIPS_FILENAME_TEMPLATE, CONSTANTS.DEFAULT_FILENAME_FORMAT)
    obs.obs_data_set_default_bool(s, PN.PROP_CLIPS_SAVE_TO_FOLDER, True)
    obs.obs_data_set_default_string(s, PN.PROP_CLIPS_LINKS_FOLDER_PATH, str(get_base_path() / '_links'))

    # obs.obs_data_set_default_int(s, PN.PROP_VIDEOS_NAMING_MODE, VideoNamingModes.MOST_RECORDED_PROCESS.value)
    # obs.obs_data_set_default_string(s, PN.PROP_VIDEOS_FILENAME_FORMAT, CONSTANTS.DEFAULT_FILENAME_FORMAT)
    # obs.obs_data_set_default_bool(s, PN.PROP_VIDEOS_SAVE_TO_FOLDER, True)

    obs.obs_data_set_default_bool(s, PN.PROP_NOTIFY_CLIPS_ON_SUCCESS, False)
    obs.obs_data_set_default_bool(s, PN.PROP_NOTIFY_CLIPS_ON_FAILURE, False)
    obs.obs_data_set_default_bool(s, PN.PROP_POPUP_CLIPS_ON_SUCCESS, False)
    obs.obs_data_set_default_bool(s, PN.PROP_POPUP_CLIPS_ON_FAILURE, False)
    obs.obs_data_set_default_int(s, PN.PROP_POPUP_PATH_DISPLAY_MODE, PopupPathDisplayModes.FULL_PATH.value)

    obs.obs_data_set_default_int(s, PN.PROP_RESTART_BUFFER_LOOP, 3600)
    obs.obs_data_set_default_bool(s, PN.PROP_RESTART_BUFFER, True)
    obs.obs_data_set_default_bool(s, PN.PROP_DEBUG_MODE, False)

    arr = obs.obs_data_array_create()
    for index, i in enumerate(CONSTANTS.DEFAULT_ALIASES):
        data = obs.obs_data_create_from_json(json.dumps(i))
        obs.obs_data_array_insert(arr, index, data)

    obs.obs_data_set_default_array(s, PN.PROP_ALIASES_LIST, arr)
    log.debug("The default values are set.")


def script_update(settings):
    VARIABLES.script_settings = settings
    setup_logging(obs.obs_data_get_bool(settings, PN.PROP_DEBUG_MODE))

    log.debug("Updating script...")
    log.debug(obs.obs_data_get_json(VARIABLES.script_settings))
    log.debug("Script updated")


def script_save(settings):
    log.debug("Saving script...")

    for key_name in VARIABLES.hotkey_ids:
        k = obs.obs_hotkey_save(VARIABLES.hotkey_ids[key_name])
        obs.obs_data_set_array(settings, key_name, k)
    log.debug("Script saved")


def script_load(script_settings):
    VARIABLES.script_settings = script_settings
    setup_logging(obs.obs_data_get_bool(script_settings, PN.PROP_DEBUG_MODE))
    log.debug("Loading script...")
    check_updates_in_background(CONSTANTS.VERSION)

    json_settings = json.loads(obs.obs_data_get_json(script_settings))
    load_aliases(json_settings)

    obs.obs_frontend_add_event_callback(on_buffer_save_callback)
    obs.obs_frontend_add_event_callback(on_buffer_recording_started_callback)
    obs.obs_frontend_add_event_callback(on_buffer_recording_stopped_callback)

    # obs.obs_frontend_add_event_callback(on_video_recording_started_callback)  # todo: for future updates
    # obs.obs_frontend_add_event_callback(on_video_recording_stopping_callback)  # todo: for future updates
    # obs.obs_frontend_add_event_callback(on_video_recording_stopped_callback)  # todo: for future updates
    load_hotkeys()

    if obs.obs_frontend_replay_buffer_active():
        on_buffer_recording_started_callback(obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED)

    log.debug("Script loaded.")


def script_unload():
    obs.timer_remove(append_clip_exe_history)
    obs.timer_remove(restart_replay_buffering_callback)

    log.debug("Script unloaded.")


def script_description():
    return f"""
<div style="font-size: 60pt; text-align: center;">
Smart Replays
</div>

<div style="font-size: 12pt; text-align: left;">
Smart Replays is an OBS script whose main purpose is to save clips with different names and to separate folders depending on the application being recorded (imitating NVIDIA Shadow Play functionality). This script also has additional functionality, such as sound and pop-up notifications, auto-restart of the replay buffer, etc.
</div>

<div style="font-size: 10pt; text-align: left; margin-top: 20px;">
Version: {CONSTANTS.VERSION}<br/>
Developed by: Qvvonk<br/>
</div>
"""
