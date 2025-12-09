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

from .globals import PN, CONSTANTS, ConfigTypes
from .tech import _print

from pathlib import Path
from typing import Any
import obspython as obs
import time


def get_obs_config(section_name: str | None = None,
                   param_name: str | None = None,
                   value_type: type[str, int, bool, float] = str,
                   config_type: ConfigTypes = ConfigTypes.PROFILE):
    """
    Gets a value from OBS config.
    If the value is not set, it will use the default value. If there is no default value, it will return NULL.
    If section_name or param_name are not specified, returns OBS config obj.

    :param section_name: Section name. If not specified, returns the OBS config.
    :param param_name: Parameter name. If not specified, returns the OBS config.
    :param value_type: Type of value (str, int, bool, float).
    :param config_type: Which config search in? (global / profile / user (obs v31 or higher)
    """
    if config_type is ConfigTypes.PROFILE:
        cfg = obs.obs_frontend_get_profile_config()
    elif config_type is ConfigTypes.APP:
        cfg = obs.obs_frontend_get_global_config()
    else:
        if CONSTANTS.OBS_VERSION[0] < 31:
            cfg = obs.obs_frontend_get_global_config()
        else:
            cfg = obs.obs_frontend_get_user_config()

    if not section_name or not param_name:
        return cfg

    functions = {
        str: obs.config_get_string,
        int: obs.config_get_int,
        bool: obs.config_get_bool,
        float: obs.config_get_double
    }

    if value_type not in functions.keys():
        raise ValueError("Unsupported type.")

    return functions[value_type](cfg, section_name, param_name)


def get_last_replay_file_name() -> str:
    """
    Returns the last saved buffer file name.
    """
    replay_buffer = obs.obs_frontend_get_replay_buffer_output()
    cd = obs.calldata_create()
    proc_handler = obs.obs_output_get_proc_handler(replay_buffer)
    obs.proc_handler_call(proc_handler, 'get_last_replay', cd)
    path = obs.calldata_string(cd, 'path')
    obs.calldata_destroy(cd)
    obs.obs_output_release(replay_buffer)
    return path


def get_current_scene_name() -> str:
    """
    Returns the current OBS scene name.
    """
    current_scene = obs.obs_frontend_get_current_scene()
    name = obs.obs_source_get_name(current_scene)
    obs.obs_source_release(current_scene)
    return name


def get_replay_buffer_max_time() -> int:
    """
    Returns replay buffer max time from OBS config (in seconds).
    """
    config_mode = get_obs_config("Output", "Mode")
    if config_mode == "Simple":
        return get_obs_config("SimpleOutput", "RecRBTime", int)
    else:
        return get_obs_config("AdvOut", "RecRBTime", int)


def get_base_path(script_settings: Any | None = None) -> Path:
    """
    Returns the base path for clips, either from the script settings or OBS config.

    :param script_settings: Script config. If not provided, base path returns from OBS config.
    :return: The base path as a `Path` object.
    """
    if script_settings is not None:
        script_path = obs.obs_data_get_string(script_settings, PN.PROP_CLIPS_BASE_PATH)
        # If PN.PROP_CLIPS_BASE_PATH is not saved in the script config, then it has a default value,
        # which is the value from the OBS config.
        if script_path:
            return Path(script_path)

    config_mode = get_obs_config("Output", "Mode")
    if config_mode == "Simple":
        return Path(get_obs_config("SimpleOutput", "FilePath"))
    else:
        return Path(get_obs_config("AdvOut", "RecFilePath"))


def restart_replay_buffering():
    """
    Restarts replay buffering, obviously -_-
    """
    _print("Stopping replay buffering...")
    replay_output = obs.obs_frontend_get_replay_buffer_output()
    obs.obs_frontend_replay_buffer_stop()

    while not obs.obs_output_can_begin_data_capture(replay_output, 0):
        time.sleep(0.1)
    _print("Replay buffering stopped.")
    _print("Starting replay buffering...")
    obs.obs_frontend_replay_buffer_start()
    _print("Replay buffering started.")
